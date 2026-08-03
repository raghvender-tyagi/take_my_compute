from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

from .serializers import RegisterSerializer, UserSerializer
from django.shortcuts import render, redirect
from django.contrib.auth import login
from .forms import RegisterForm

User = get_user_model()

def register_view(request):
    """HTML registration page using custom RegisterForm."""
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('renter_browse')
    else:
        form = RegisterForm()
    return render(request, "accounts/register.html", {"form": form})

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Automatically generate JWT tokens on successful registration
        refresh = RefreshToken.for_user(user)
        return Response({
            "user": UserSerializer(user).data,
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }, status=status.HTTP_201_CREATED)

class UserMeView(generics.RetrieveAPIView):
    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

class GoogleOAuthView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        # Placeholder for Google OAuth token exchange
        # Normally, verify request.data.get('id_token') and fetch user info
        return Response({
            "detail": "Google OAuth endpoint stub. Token exchange will happen here.",
            "access": "google_access_token_placeholder",
            "refresh": "google_refresh_token_placeholder"
        }, status=status.HTTP_200_OK)

class GitHubOAuthView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request, *args, **kwargs):
        # Placeholder for GitHub OAuth code exchange
        # Normally, verify request.data.get('code') and fetch user info
        return Response({
            "detail": "GitHub OAuth endpoint stub. Code exchange will happen here.",
            "access": "github_access_token_placeholder",
            "refresh": "github_refresh_token_placeholder"
        }, status=status.HTTP_200_OK)
