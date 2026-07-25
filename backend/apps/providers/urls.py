from django.urls import path
from .views import ProviderHeartbeatView, ProviderMachineListView

urlpatterns = [
    path('heartbeat/', ProviderHeartbeatView.as_view(), name='provider_heartbeat'),
    path('machines/', ProviderMachineListView.as_view(), name='provider_machines_list'),
]
