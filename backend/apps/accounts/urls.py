from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import RegisterView, UserMeView, GoogleOAuthView, GitHubOAuthView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='auth_register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('oauth/google/', GoogleOAuthView.as_view(), name='oauth_google'),
    path('oauth/github/', GitHubOAuthView.as_view(), name='oauth_github'),
    path('me/', UserMeView.as_view(), name='auth_me'),
]
