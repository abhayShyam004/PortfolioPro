"""
Unit tests for accounts app - authentication and user management.
"""

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
import json

User = get_user_model()


class UserModelTests(TestCase):
    """Tests for the custom User model."""
    
    def test_create_user(self):
        """Test creating a regular user."""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            subdomain='testuser'
        )
        self.assertEqual(user.username, 'testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.subdomain, 'testuser')
        self.assertEqual(user.role, User.Role.USER)
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_banned)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password('testpass123'))
    
    def test_create_superadmin(self):
        """Test creating a superadmin user."""
        user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        self.assertEqual(user.role, User.Role.SUPERADMIN)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
    
    def test_subdomain_uniqueness(self):
        """Test that subdomains must be unique."""
        User.objects.create_user(
            username='user1',
            email='user1@example.com',
            password='pass123',
            subdomain='mysubdomain'
        )
        # IntegrityError should be raised for duplicate subdomain
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username='user2',
                email='user2@example.com',
                password='pass123',
                subdomain='mysubdomain'  # Duplicate
            )
    
    def test_is_superadmin_property(self):
        """Test the is_superadmin property."""
        user = User.objects.create_user(
            username='regular',
            email='regular@example.com',
            password='pass123',
            subdomain='regular'
        )
        admin = User.objects.create_superuser(
            username='superadmin',
            email='super@example.com',
            password='pass123'
        )
        self.assertFalse(user.is_superadmin)
        self.assertTrue(admin.is_superadmin)


class AuthAPITests(APITestCase):
    """Tests for authentication API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPass123!',
            subdomain='testuser'
        )
    
    def test_register_user(self):
        """Test user registration endpoint."""
        url = reverse('accounts:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass123!',
            'password2': 'NewPass123!',
            'subdomain': 'newuser'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_register_duplicate_subdomain(self):
        """Test registration fails with duplicate subdomain."""
        url = reverse('accounts:register')
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'NewPass123!',
            'password2': 'NewPass123!',
            'subdomain': 'testuser'  # Already taken
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_login_success(self):
        """Test successful login."""
        url = reverse('accounts:login')
        data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
    
    def test_login_wrong_password(self):
        """Test login fails with wrong password."""
        url = reverse('accounts:login')
        data = {
            'username': 'testuser',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_inactive_user(self):
        """Test inactive user cannot login."""
        self.user.is_active = False
        self.user.save()
        
        url = reverse('accounts:login')
        data = {
            'username': 'testuser',
            'password': 'TestPass123!'
        }
        response = self.client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_check_subdomain_available(self):
        """Test subdomain availability check."""
        url = reverse('accounts:check_subdomain')
        
        # Available subdomain
        response = self.client.get(url, {'subdomain': 'newsubdomain'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['available'])
        
        # Taken subdomain
        response = self.client.get(url, {'subdomain': 'testuser'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['available'])
    
    def test_profile_requires_auth(self):
        """Test profile endpoint requires authentication."""
        url = reverse('accounts:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_profile_authenticated(self):
        """Test authenticated user can access profile."""
        self.client.force_authenticate(user=self.user)
        url = reverse('accounts:profile')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['username'], 'testuser')
    
    def test_token_refresh(self):
        """Test token refresh works."""
        # First login to get tokens
        login_url = reverse('accounts:login')
        login_response = self.client.post(login_url, {
            'username': 'testuser',
            'password': 'TestPass123!'
        }, format='json')
        
        refresh_token = login_response.data['refresh']
        
        # Try to refresh
        refresh_url = reverse('accounts:token_refresh')
        refresh_response = self.client.post(refresh_url, {
            'refresh': refresh_token
        }, format='json')
        
        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn('access', refresh_response.data)


class PasswordValidationTests(TestCase):
    """Tests for password validation."""
    
    def test_weak_password_rejected(self):
        """Test that weak passwords are rejected during registration."""
        client = APIClient()
        url = reverse('accounts:register')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'short',  # Too short
            'password2': 'short',
            'subdomain': 'newuser'
        }
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_password_mismatch_rejected(self):
        """Test that mismatched passwords are rejected."""
        client = APIClient()
        url = reverse('accounts:register')
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass123!',
            'password2': 'DifferentPass123!',  # Mismatch
            'subdomain': 'newuser'
        }
        response = client.post(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
