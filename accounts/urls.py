from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    CustomTokenObtainPairView,
    LogoutView,
    ProfileView,
    ChangePasswordView,
    CheckSubdomainView,
)

app_name = 'accounts'

urlpatterns = [
    # Registration
    path('register/', RegisterView.as_view(), name='register'),
    
    # Login (JWT token obtain)
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    
    # Token refresh
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Logout (blacklist refresh token)
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # User profile
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Change password
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    
    # Check subdomain availability
    path('check-subdomain/', CheckSubdomainView.as_view(), name='check_subdomain'),
]
