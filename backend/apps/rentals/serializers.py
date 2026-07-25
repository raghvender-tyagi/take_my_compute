from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import RentalSession
from apps.providers.models import ProviderMachine

class RentalSessionSerializer(serializers.ModelSerializer):
    renter_username = serializers.CharField(source='renter.username', read_only=True)
    provider_machine_id = serializers.CharField(source='provider_machine.provider_id', read_only=True)

    class Meta:
        model = RentalSession
        fields = [
            'id', 'renter', 'renter_username', 'provider_machine', 'provider_machine_id',
            'docker_image', 'command', 'cpu_limit', 'memory_limit_mb', 'status',
            'container_id', 'error_reason', 'started_at', 'ended_at', 'created_at'
        ]
        read_only_fields = [
            'id', 'renter', 'status', 'container_id', 'error_reason', 'started_at', 'ended_at', 'created_at'
        ]

    def validate(self, attrs):
        # We need to construct a temp model instance to leverage the clean() validation
        # or we can write the validation inline here. Leveraging model clean() is best.
        # But we must inject the renter (who is the request user).
        request = self.context.get('request')
        if not request or not request.user:
            raise serializers.ValidationError("User must be authenticated.")
            
        attrs['renter'] = request.user
        
        # Instantiate temporary model to run validation
        instance = RentalSession(**attrs)
        try:
            instance.clean()
        except DjangoValidationError as e:
            raise serializers.ValidationError(e.message_dict if hasattr(e, 'message_dict') else str(e))
            
        return attrs
