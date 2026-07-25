from rest_framework import serializers
from .models import ProviderMachine, ProviderHeartbeatLog

class ProviderHeartbeatSerializer(serializers.Serializer):
    provider_id = serializers.CharField(max_length=100)
    cpu_count = serializers.IntegerField(default=1)
    cpu_usage_percent = serializers.FloatField()
    memory_total_gb = serializers.FloatField()
    memory_used_gb = serializers.FloatField()
    memory_usage_percent = serializers.FloatField()
    disk_total_gb = serializers.FloatField()
    disk_used_gb = serializers.FloatField()
    disk_usage_percent = serializers.FloatField()
    os_name = serializers.CharField(max_length=50, required=False, allow_blank=True)
    os_version = serializers.CharField(max_length=100, required=False, allow_blank=True)

class ProviderMachineSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = ProviderMachine
        fields = [
            'id', 'owner', 'owner_username', 'provider_id', 'name',
            'cpu_count', 'cpu_usage_percent', 'memory_total_gb', 'memory_used_gb',
            'memory_usage_percent', 'disk_total_gb', 'disk_used_gb',
            'disk_usage_percent', 'os_name', 'os_version', 'is_online',
            'last_heartbeat', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
