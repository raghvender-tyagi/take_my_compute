from django.urls import re_path
from apps.rentals import consumers

websocket_urlpatterns = [
    re_path(r'^ws/agent/$', consumers.AgentConsumer.as_asgi()),
    re_path(r'^ws/rentals/(?P<session_id>\d+)/$', consumers.RenterConsumer.as_asgi()),
]
