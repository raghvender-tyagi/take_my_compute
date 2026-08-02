from rest_framework import viewsets, permissions, status, decorators
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from .models import RentalSession
from .serializers import RentalSessionSerializer

class RentalSessionViewSet(viewsets.ModelViewSet):
    serializer_class = RentalSessionSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        # Users can view sessions they rented, or providers can view sessions on their machines
        if user.role == 'provider':
            return RentalSession.objects.filter(provider_machine__owner=user).order_by('-created_at')
        elif user.role == 'renter':
            return RentalSession.objects.filter(renter=user).order_by('-created_at')
        else:
            # If user has 'both' role, return union of both
            return RentalSession.objects.filter(renter=user).order_by('-created_at') | \
                   RentalSession.objects.filter(provider_machine__owner=user).order_by('-created_at')

    def perform_create(self, serializer):
        session = serializer.save(renter=self.request.user)
        
        # Broadcast assignment to the agent via WebSocket Channel Layer!
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if channel_layer:
                provider_id = session.provider_machine.provider_id
                async_to_sync(channel_layer.group_send)(
                    f"agent_{provider_id}",
                    {
                        "type": "rental_assign",
                        "session_id": session.id,
                        "docker_image": session.docker_image,
                        "command": session.command,
                        "cpu_limit": session.cpu_limit,
                        "memory_limit_mb": session.memory_limit_mb
                    }
                )
        except Exception as e:
            # Fallback if channel layer is not running or redis is down in test env
            pass

    @decorators.action(detail=True, methods=['post'], url_path='stop')
    def stop(self, request, pk=None):
        """
        Renter requests session termination. Sets the status to 'stopping'.
        The provider agent will pick up this transition and stop the container.
        """
        session = self.get_object()
        
        # Check permissions: Only the renter or the machine owner can stop the session
        if session.renter != request.user and session.provider_machine.owner != request.user:
            return Response(
                {"detail": "You do not have permission to stop this session."},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Check if the session is in an active state that can be stopped
        if session.status not in [RentalSession.Status.PENDING, RentalSession.Status.PROVISIONING, RentalSession.Status.RUNNING]:
            return Response(
                {"detail": f"Cannot stop session in state: {session.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        session.status = RentalSession.Status.STOPPING
        session.save()
        
        # Broadcast stop command to the agent via WebSocket Channel Layer!
        try:
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            channel_layer = get_channel_layer()
            if channel_layer:
                provider_id = session.provider_machine.provider_id
                async_to_sync(channel_layer.group_send)(
                    f"agent_{provider_id}",
                    {
                        "type": "rental_stop",
                        "session_id": session.id
                    }
                )
        except Exception as e:
            pass

        return Response(
            {
                "status": "success",
                "message": "Stop request submitted.",
                "session": RentalSessionSerializer(session).data
            },
            status=status.HTTP_200_OK
        )

    @decorators.action(detail=True, methods=['patch'], url_path='agent-update')
    def agent_update(self, request, pk=None):
        """
        Endpoint for the provider agent to update the status, container ID, error reason, and timestamps.
        """
        session = self.get_object()
        
        allowed_fields = ['status', 'container_id', 'error_reason', 'started_at', 'ended_at']
        updated = False
        
        for field in allowed_fields:
            if field in request.data:
                setattr(session, field, request.data[field])
                updated = True
                
        if updated:
            # Bypass clean() to allow status changes even if machine is offline/changed
            session.save()
            return Response(RentalSessionSerializer(session).data, status=status.HTTP_200_OK)
            
        return Response({"detail": "No valid fields provided for update."}, status=status.HTTP_400_BAD_REQUEST)

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from apps.providers.models import ProviderMachine

def home_view(request):
    """Landing page for the web application."""
    return render(request, 'rentals/home.html')

@login_required
def browse_machines(request):
    min_cpu = request.GET.get('min_cpu')
    min_ram = request.GET.get('min_ram')
    min_disk = request.GET.get('min_disk')
    status_filter = request.GET.get('status', 'online')

    # Self-clean offline status based on heartbeat threshold
    import datetime
    from django.utils import timezone
    cutoff = timezone.now() - datetime.timedelta(seconds=30)
    ProviderMachine.objects.filter(last_heartbeat__lt=cutoff).update(is_online=False)

    machines = ProviderMachine.objects.all()

    if status_filter == 'online':
        machines = machines.filter(is_online=True)

    if min_cpu:
        machines = machines.filter(cpu_count__gte=int(min_cpu))
    if min_ram:
        machines = machines.filter(memory_total_gb__gte=float(min_ram))
    if min_disk:
        machines = machines.filter(disk_total_gb__gte=float(min_disk))

    return render(request, 'rentals/browse.html', {
        'machines': machines,
        'min_cpu': min_cpu,
        'min_ram': min_ram,
        'min_disk': min_disk,
        'status_filter': status_filter
    })

@login_required
def launch_session(request, machine_id):
    machine = get_object_or_404(ProviderMachine, id=machine_id)
    
    max_cpus = machine.cpu_count or 1
    max_ram_mb = int(machine.memory_total_gb * 1024) if machine.memory_total_gb else 1024

    error = None
    if request.method == 'POST':
        docker_image = request.POST.get('docker_image')
        command = request.POST.get('command')
        cpu_limit = float(request.POST.get('cpu_limit', 1.0))
        memory_limit_mb = int(request.POST.get('memory_limit_mb', 512))

        if cpu_limit > max_cpus:
            error = f"Requested CPU limit ({cpu_limit}) exceeds machine capability ({max_cpus})."
        elif memory_limit_mb > max_ram_mb:
            error = f"Requested memory limit ({memory_limit_mb}MB) exceeds machine capability ({max_ram_mb}MB)."
        elif not docker_image:
            error = "Docker image is required."
        else:
            try:
                session = RentalSession(
                    renter=request.user,
                    provider_machine=machine,
                    docker_image=docker_image,
                    command=command,
                    cpu_limit=cpu_limit,
                    memory_limit_mb=memory_limit_mb,
                    status=RentalSession.Status.PENDING
                )
                session.clean()
                session.save()

                # Trigger websocket push assignment to agent
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    channel_layer = get_channel_layer()
                    if channel_layer:
                        async_to_sync(channel_layer.group_send)(
                            f"agent_{machine.provider_id}",
                            {
                                "type": "rental_assign",
                                "session_id": session.id,
                                "docker_image": session.docker_image,
                                "command": session.command,
                                "cpu_limit": session.cpu_limit,
                                "memory_limit_mb": session.memory_limit_mb
                            }
                        )
                except Exception:
                    pass

                return redirect('renter_monitor', session_id=session.id)
            except Exception as e:
                error = str(e)

    return render(request, 'rentals/launch.html', {
        'machine': machine,
        'max_cpus': max_cpus,
        'max_ram_mb': max_ram_mb,
        'error': error,
        'form_data': request.POST if request.method == 'POST' else {}
    })

@login_required
def monitor_session(request, session_id):
    session = get_object_or_404(RentalSession, id=session_id)
    if session.renter != request.user and session.provider_machine.owner != request.user:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("You do not have permission to view this session.")
        
    return render(request, 'rentals/monitor.html', {
        'session': session
    })

@login_required
def rentals_list(request):
    sessions = RentalSession.objects.filter(renter=request.user).order_by('-created_at')
    return render(request, 'rentals/rentals_list.html', {
        'sessions': sessions
    })
