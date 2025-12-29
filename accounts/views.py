from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

from .serializers import (
    RegisterSerializer, 
    UserSerializer, 
    UserProfileUpdateSerializer,
    ChangePasswordSerializer
)

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom JWT token serializer that includes user data in response.
    """
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        
        # Add custom claims to token
        token['username'] = user.username
        token['subdomain'] = user.subdomain
        token['role'] = user.role
        
        return token
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Check if user is banned
        if self.user.is_banned:
            from rest_framework import serializers
            raise serializers.ValidationError({
                "detail": "Your account has been suspended. Please contact support."
            })
        
        # Add user data to response
        data['user'] = UserSerializer(self.user).data
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that returns user data along with tokens.
    
    POST /api/auth/login/
    {
        "username": "user",
        "password": "pass"
    }
    
    Returns:
    {
        "access": "...",
        "refresh": "...",
        "user": { ... }
    }
    """
    serializer_class = CustomTokenObtainPairSerializer


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint.
    Creates a new user and returns JWT tokens.
    
    POST /api/auth/register/
    {
        "username": "newuser",
        "email": "user@example.com",
        "password": "securepassword123",
        "password2": "securepassword123",
        "subdomain": "newuser"
    }
    
    Returns:
    {
        "message": "Registration successful",
        "user": { ... },
        "tokens": {
            "access": "...",
            "refresh": "..."
        }
    }
    """
    queryset = User.objects.all()
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for the new user
        refresh = RefreshToken.for_user(user)
        
        # NOTE: Portfolio creation will be added in Phase 2 when models have user FK
        # self._create_default_portfolio(user)
        
        return Response({
            'message': 'Registration successful. Welcome to PortfolioPro!',
            'user': UserSerializer(user).data,
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            }
        }, status=status.HTTP_201_CREATED)


class LogoutView(APIView):
    """
    Logout endpoint that blacklists the refresh token.
    
    POST /api/auth/logout/
    {
        "refresh": "..."
    }
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response(
                    {'error': 'Refresh token is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response(
                {'message': 'Successfully logged out'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST
            )


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update the current user's profile.
    
    GET /api/auth/profile/
    Returns current user data.
    
    PATCH /api/auth/profile/
    Updates user profile fields.
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserProfileUpdateSerializer
        return UserSerializer
    
    def get_object(self):
        return self.request.user


class ChangePasswordView(generics.GenericAPIView):
    """
    Change password for the authenticated user.
    
    POST /api/auth/change-password/
    {
        "old_password": "...",
        "new_password": "...",
        "new_password2": "..."
    }
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Update password
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response(
            {'message': 'Password changed successfully'},
            status=status.HTTP_200_OK
        )


class CheckSubdomainView(APIView):
    """
    Check if a subdomain is available.
    
    GET /api/auth/check-subdomain/?subdomain=myname
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        subdomain = request.query_params.get('subdomain', '').lower().strip()
        
        if not subdomain:
            return Response(
                {'error': 'Subdomain parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if subdomain exists
        exists = User.objects.filter(subdomain__iexact=subdomain).exists()
        
        # Check reserved subdomains
        reserved = {
            'www', 'api', 'admin', 'static', 'media', 'app', 'mail', 'ftp',
            'blog', 'help', 'support', 'status', 'docs', 'developer', 'dev',
            'staging', 'test', 'demo', 'login', 'register', 'signup', 'auth'
        }
        is_reserved = subdomain in reserved
        
        available = not exists and not is_reserved
        
        return Response({
            'subdomain': subdomain,
            'available': available,
            'message': 'Subdomain is available' if available else 'Subdomain is not available'
        })
