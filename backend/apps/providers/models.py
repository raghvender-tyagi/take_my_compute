from django.db import models
from django.conf import settings

class ProviderMachine(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='machines',
        null=True,
        blank=True
    )
    provider_id = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100, blank=True)
    
    # System specifications and real-time usage (updated by heartbeats)
    cpu_count = models.IntegerField(default=1)
    cpu_usage_percent = models.FloatField(default=0.0)
    
    memory_total_gb = models.FloatField(default=0.0)
    memory_used_gb = models.FloatField(default=0.0)
    memory_usage_percent = models.FloatField(default=0.0)
    
    disk_total_gb = models.FloatField(default=0.0)
    disk_used_gb = models.FloatField(default=0.0)
    disk_usage_percent = models.FloatField(default=0.0)
    
    os_name = models.CharField(max_length=50, blank=True)
    os_version = models.CharField(max_length=100, blank=True)
    
    is_online = models.BooleanField(default=False)
    last_heartbeat = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.provider_id} - {self.name or 'Unnamed'}"

class ProviderHeartbeatLog(models.Model):
    machine = models.ForeignKey(
        ProviderMachine,
        on_delete=models.CASCADE,
        related_name='heartbeats'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    cpu_usage_percent = models.FloatField()
    memory_used_gb = models.FloatField()
    memory_usage_percent = models.FloatField()
    disk_used_gb = models.FloatField()
    disk_usage_percent = models.FloatField()

    def __str__(self):
        return f"{self.machine.provider_id} @ {self.timestamp}"
