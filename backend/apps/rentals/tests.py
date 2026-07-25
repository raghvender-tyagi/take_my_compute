from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from apps.providers.models import ProviderMachine
from .models import RentalSession

User = get_user_model()

class RentalSessionTestCase(APITestCase):
    def setUp(self):
        # 1. Create a provider user and their registered machine
        self.provider_user = User.objects.create_user(
            username="provider1",
            password="testpassword",
            email="p1@example.com",
            role="provider"
        )
        self.machine = ProviderMachine.objects.create(
            owner=self.provider_user,
            provider_id="host-alpha",
            cpu_count=4,
            memory_total_gb=16.0,
            disk_total_gb=100.0,
            is_online=True
        )

        # 2. Create a renter user
        self.renter_user = User.objects.create_user(
            username="renter1",
            password="testpassword",
            email="r1@example.com",
            role="renter"
        )

    def test_rental_resource_limit_validation(self):
        """Verify that renting resources exceeding host limits raises ValidationError."""
        # CPU Limit Exceeded (4 is maximum, requesting 5)
        session = RentalSession(
            renter=self.renter_user,
            provider_machine=self.machine,
            docker_image="ubuntu:latest",
            cpu_limit=5.0,
            memory_limit_mb=4096,
            status=RentalSession.Status.PENDING
        )
        with self.assertRaises(ValidationError) as context:
            session.clean()
        self.assertIn("exceeds machine capacity", str(context.exception))

        # RAM Limit Exceeded (16GB = 16384MB is maximum, requesting 17000MB)
        session2 = RentalSession(
            renter=self.renter_user,
            provider_machine=self.machine,
            docker_image="ubuntu:latest",
            cpu_limit=2.0,
            memory_limit_mb=17000,
            status=RentalSession.Status.PENDING
        )
        with self.assertRaises(ValidationError) as context:
            session2.clean()
        self.assertIn("exceeds machine capacity", str(context.exception))

    def test_valid_rental_lifecycle_and_api(self):
        """Verify creation of a valid rental session, state transition, and REST endpoint updates."""
        # 1. Create session (should default to PENDING status)
        session = RentalSession.objects.create(
            renter=self.renter_user,
            provider_machine=self.machine,
            docker_image="python:alpine",
            command="python -c 'print(123)'",
            cpu_limit=2.0,
            memory_limit_mb=2048,
            status=RentalSession.Status.PENDING
        )
        self.assertEqual(session.status, RentalSession.Status.PENDING)

        # 2. Authenticate Renter via SimpleJWT token
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.renter_user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')

        # 3. Request session stop (changes state to STOPPING)
        response = self.client.post(f"/api/rentals/{session.id}/stop/")
        self.assertEqual(response.status_code, 200)
        
        session.refresh_from_db()
        self.assertEqual(session.status, RentalSession.Status.STOPPING)

        # 4. Agent updates state via agent-update endpoint
        # The agent changes status to running and reports container_id
        update_response = self.client.patch(
            f"/api/rentals/{session.id}/agent-update/",
            data={
                "status": "running",
                "container_id": "abc123xyz456"
            },
            content_type="application/json"
        )
        self.assertEqual(update_response.status_code, 200)
        
        session.refresh_from_db()
        self.assertEqual(session.status, RentalSession.Status.RUNNING)
        self.assertEqual(session.container_id, "abc123xyz456")
