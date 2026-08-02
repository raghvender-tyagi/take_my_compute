from rest_framework import views, generics, permissions, status
from rest_framework.response import Response
from django.utils import timezone
from .models import ProviderMachine, ProviderHeartbeatLog
from .serializers import ProviderHeartbeatSerializer, ProviderMachineSerializer

class ProviderHeartbeatView(views.APIView):
    """
    Endpoint for provider monitoring agents to report status/resources.
    Requires a valid JWT token to associate the machine with a registered user.
    """
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        serializer = ProviderHeartbeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        data = serializer.validated_data
        provider_id = data['provider_id']
        
        # Check if machine already exists
        machine, created = ProviderMachine.objects.get_or_create(
            provider_id=provider_id,
            defaults={'name': f"Machine-{provider_id[:8]}"}
        )
        
        # Associate with authenticated user if available
        if request.user.is_authenticated:
            machine.owner = request.user
            
        # Update machine specs and status
        machine.cpu_count = data.get('cpu_count', 1)
        machine.cpu_usage_percent = data['cpu_usage_percent']
        machine.memory_total_gb = data['memory_total_gb']
        machine.memory_used_gb = data['memory_used_gb']
        machine.memory_usage_percent = data['memory_usage_percent']
        machine.disk_total_gb = data['disk_total_gb']
        machine.disk_used_gb = data['disk_used_gb']
        machine.disk_usage_percent = data['disk_usage_percent']
        machine.os_name = data.get('os_name', '')
        machine.os_version = data.get('os_version', '')
        machine.is_online = True
        machine.last_heartbeat = timezone.now()
        machine.save()
        
        # Log this heartbeat for resource tracking history
        ProviderHeartbeatLog.objects.create(
            machine=machine,
            cpu_usage_percent=data['cpu_usage_percent'],
            memory_used_gb=data['memory_used_gb'],
            memory_usage_percent=data['memory_usage_percent'],
            disk_used_gb=data['disk_used_gb'],
            disk_usage_percent=data['disk_usage_percent']
        )
        
        return Response({
            "status": "success",
            "message": "Heartbeat received.",
            "provider_id": provider_id,
            "created": created
        }, status=status.HTTP_200_OK)

class ProviderMachineListView(generics.ListAPIView):
    """
    Endpoint to list all provider machines (e.g. for Renters to view available machines).
    Supports filtering by min_cpu, min_ram, and min_disk.
    Only returns online machines.
    """
    serializer_class = ProviderMachineSerializer
    permission_classes = (permissions.AllowAny,)

    def get_queryset(self):
        queryset = ProviderMachine.objects.filter(is_online=True).order_by('-last_heartbeat')
        
        min_cpu = self.request.query_params.get('min_cpu')
        min_ram = self.request.query_params.get('min_ram')
        min_disk = self.request.query_params.get('min_disk')

        if min_cpu:
            try:
                queryset = queryset.filter(cpu_count__gte=int(min_cpu))
            except ValueError:
                pass
        if min_ram:
            try:
                queryset = queryset.filter(memory_total_gb__gte=float(min_ram))
            except ValueError:
                pass
        if min_disk:
            try:
                queryset = queryset.filter(disk_total_gb__gte=float(min_disk))
            except ValueError:
                pass
                
        return queryset
