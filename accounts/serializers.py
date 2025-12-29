from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    Validates passwords, subdomain format, and creates user with default portfolio data.
    """
    password = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'},
        help_text="Password must be at least 10 characters with letters and numbers"
    )
    password2 = serializers.CharField(
        write_only=True, 
        required=True,
        style={'input_type': 'password'},
        help_text="Confirm password"
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'subdomain', 'first_name', 'last_name']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
        }
    
    def validate_subdomain(self, value):
        """Validate subdomain format and uniqueness."""
        value = value.lower().strip()
        
        # Check length
        if len(value) < 3:
            raise serializers.ValidationError(
                "Subdomain must be at least 3 characters long."
            )
        if len(value) > 50:
            raise serializers.ValidationError(
                "Subdomain cannot exceed 50 characters."
            )
        
        # Check format: lowercase alphanumeric with hyphens (not at start/end)
        if not re.match(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$', value):
            raise serializers.ValidationError(
                "Subdomain must be lowercase alphanumeric. Hyphens allowed but not at start/end."
            )
        
        # Reserved subdomains
        reserved = {
            'www', 'api', 'admin', 'static', 'media', 'app', 'mail', 'ftp',
            'blog', 'help', 'support', 'status', 'docs', 'developer', 'dev',
            'staging', 'test', 'demo', 'login', 'register', 'signup', 'auth'
        }
        if value in reserved:
            raise serializers.ValidationError(
                f"'{value}' is a reserved subdomain and cannot be used."
            )
        
        return value
    
    def validate_email(self, value):
        """Validate email uniqueness."""
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower()
    
    def validate_password(self, value):
        """Validate password strength using Django's validators."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, attrs):
        """Validate that passwords match."""
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({
                "password2": "Passwords do not match."
            })
        return attrs
    
    def create(self, validated_data):
        """Create user and remove password2 from data."""
        validated_data.pop('password2')
        password = validated_data.pop('password')
        
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile data.
    Read-only for sensitive fields, allows updates to profile info.
    """
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'subdomain', 'role',
            'first_name', 'last_name', 'is_active', 'is_banned',
            'email_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'username', 'subdomain', 'role', 'is_active', 
            'is_banned', 'email_verified', 'created_at', 'updated_at'
        ]


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    Limited fields that users can modify.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
    
    def validate_email(self, value):
        """Validate email uniqueness excluding current user."""
        user = self.context.get('request').user
        if User.objects.filter(email__iexact=value).exclude(pk=user.pk).exists():
            raise serializers.ValidationError(
                "A user with this email already exists."
            )
        return value.lower()


class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer for password change.
    Requires old password verification.
    """
    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    new_password2 = serializers.CharField(
        required=True,
        write_only=True,
        style={'input_type': 'password'}
    )
    
    def validate_new_password(self, value):
        """Validate new password strength."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value
    
    def validate(self, attrs):
        """Validate old password and that new passwords match."""
        user = self.context.get('request').user
        
        if not user.check_password(attrs['old_password']):
            raise serializers.ValidationError({
                "old_password": "Current password is incorrect."
            })
        
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({
                "new_password2": "New passwords do not match."
            })
        
        if attrs['old_password'] == attrs['new_password']:
            raise serializers.ValidationError({
                "new_password": "New password must be different from current password."
            })
        
        return attrs
