from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RentalSessionViewSet

router = DefaultRouter()
router.register(r'', RentalSessionViewSet, basename='rental')

urlpatterns = [
    path('', include(router.urls)),
]
