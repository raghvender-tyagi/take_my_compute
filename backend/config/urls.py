"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include

from apps.providers.views import ProviderMachineListView
from apps.rentals import views as rental_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/providers/', include('apps.providers.urls')),
    path('api/machines/', ProviderMachineListView.as_view(), name='api_machines_list'),
    path('api/rentals/', include('apps.rentals.urls')),
    
    # Renter UI Dashboard Views
    path('rentals/browse/', rental_views.browse_machines, name='renter_browse'),
    path('rentals/launch/<int:machine_id>/', rental_views.launch_session, name='renter_launch'),
    path('rentals/monitor/<int:session_id>/', rental_views.monitor_session, name='renter_monitor'),
    path('rentals/list/', rental_views.rentals_list, name='renter_sessions_list'),
]
