from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from apps.providers.models import ProviderMachine

class RentalSession(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PROVISIONING = 'provisioning', 'Provisioning'
        RUNNING = 'running', 'Running'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
        STOPPED = 'stopped', 'Stopped'
        STOPPING = 'stopping', 'Stopping'

    renter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='rental_sessions'
    )
    provider_machine = models.ForeignKey(
        ProviderMachine,
        on_delete=models.CASCADE,
        related_name='rentals'
    )
    docker_image = models.CharField(max_length=255)
    command = models.TextField(blank=True, null=True)
    
    cpu_limit = models.FloatField()
    memory_limit_mb = models.IntegerField()
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    container_id = models.CharField(max_length=128, blank=True, null=True)
    error_reason = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        super().clean()
        
        # Validate that the requested machine is online
        if not self.provider_machine.is_online:
            raise ValidationError("Cannot rent a machine that is offline.")

        # Validate cpu_limit
        if self.cpu_limit <= 0:
            raise ValidationError("CPU limit must be greater than 0.")
        if self.cpu_limit > self.provider_machine.cpu_count:
            raise ValidationError(
                f"Requested CPU limit ({self.cpu_limit}) exceeds machine capacity ({self.provider_machine.cpu_count})."
            )

        # Validate memory_limit_mb (machine's total RAM is stored in GB, convert to MB)
        machine_memory_mb = self.provider_machine.memory_total_gb * 1024
        if self.memory_limit_mb <= 0:
            raise ValidationError("Memory limit must be greater than 0 MB.")
        if self.memory_limit_mb > machine_memory_mb:
            raise ValidationError(
                f"Requested Memory limit ({self.memory_limit_mb} MB) exceeds machine capacity ({int(machine_memory_mb)} MB)."
            )

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Session {self.id} - {self.renter.username} on {self.provider_machine.provider_id} ({self.status})"
