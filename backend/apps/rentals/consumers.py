import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import AccessToken

User = get_user_model()

class AgentConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for provider agents.
    Allows agents to connect, register by provider_id, receive assignments, and stream back logs.
    """
    async def connect(self):
        self.provider_id = None
        self.group_name = None
        await self.accept()

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except ValueError:
            await self.send(text_data=json.dumps({"error": "Invalid JSON format"}))
            return

        action = data.get("action")

        if action == "register":
            self.provider_id = data.get("provider_id")
            if not self.provider_id:
                await self.send(text_data=json.dumps({"error": "Missing provider_id"}))
                return
            
            self.group_name = f"agent_{self.provider_id}"
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )
            await self.send(text_data=json.dumps({
                "status": "registered",
                "message": f"Successfully registered agent: {self.provider_id}"
            }))

        elif action == "log_line":
            session_id = data.get("session_id")
            log_line = data.get("log_line")
            if session_id and log_line:
                # Forward log line to the renter group
                renter_group = f"rental_{session_id}"
                await self.channel_layer.group_send(
                    renter_group,
                    {
                        "type": "rental_log",
                        "session_id": session_id,
                        "log_line": log_line
                    }
                )

        elif action == "status_update":
            session_id = data.get("session_id")
            status = data.get("status")
            container_id = data.get("container_id")
            started_at = data.get("started_at")
            ended_at = data.get("ended_at")
            error_reason = data.get("error_reason")

            if session_id and status:
                # 1. Update the database state asynchronously
                await self.update_session_db(
                    session_id, status, container_id, started_at, ended_at, error_reason
                )

                # 2. Forward status update to the renter group
                renter_group = f"rental_{session_id}"
                await self.channel_layer.group_send(
                    renter_group,
                    {
                        "type": "rental_status",
                        "session_id": session_id,
                        "status": status,
                        "container_id": container_id,
                        "started_at": started_at,
                        "ended_at": ended_at,
                        "error_reason": error_reason
                    }
                )

    # Helper method to update database
    @database_sync_to_async
    def update_session_db(self, session_id, status, container_id=None, started_at=None, ended_at=None, error_reason=None):
        from .models import RentalSession
        try:
            session = RentalSession.objects.get(id=session_id)
            session.status = status
            if container_id:
                session.container_id = container_id
            if started_at:
                session.started_at = started_at
            if ended_at:
                session.ended_at = ended_at
            if error_reason:
                session.error_reason = error_reason
            session.save()
        except RentalSession.DoesNotExist:
            pass

    # Group message handlers
    async def rental_assign(self, event):
        """Called when a renter assigns a new task."""
        await self.send(text_data=json.dumps({
            "action": "run_task",
            "session_id": event["session_id"],
            "docker_image": event["docker_image"],
            "command": event.get("command"),
            "cpu_limit": event["cpu_limit"],
            "memory_limit_mb": event["memory_limit_mb"]
        }))

    async def rental_stop(self, event):
        """Called when a renter requests to stop a running task."""
        await self.send(text_data=json.dumps({
            "action": "stop_task",
            "session_id": event["session_id"]
        }))


class RenterConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for renters.
    Allows renters to connect to /ws/rentals/{session_id}/ and receive live updates & logs.
    """
    async def connect(self):
        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.group_name = f"rental_{self.session_id}"

        # Join rental session group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )

    # Group message handlers
    async def rental_log(self, event):
        await self.send(text_data=json.dumps({
            "type": "log",
            "session_id": event["session_id"],
            "log_line": event["log_line"]
        }))

    async def rental_status(self, event):
        await self.send(text_data=json.dumps({
            "type": "status",
            "session_id": event["session_id"],
            "status": event["status"],
            "container_id": event.get("container_id"),
            "started_at": event.get("started_at"),
            "ended_at": event.get("ended_at"),
            "error_reason": event.get("error_reason")
        }))
