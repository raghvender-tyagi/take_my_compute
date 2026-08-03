from django.urls import path
from django.contrib.auth.views import LoginView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView, UserMeView, GoogleOAuthView, GitHubOAuthView, register_view

urlpatterns = [
    # HTML pages
    path('register/', register_view, name='register'),
    path('login/', LoginView.as_view(template_name='accounts/login.html'), name='login'),
    # API endpoints
    path('api/register/', RegisterView.as_view(), name='auth_register'),
    path('api/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/oauth/google/', GoogleOAuthView.as_view(), name='oauth_google'),
    path('api/oauth/github/', GitHubOAuthView.as_view(), name='oauth_github'),
    path('api/me/', UserMeView.as_view(), name='auth_me'),
]
