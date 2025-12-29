from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator


class UserManager(BaseUserManager):
    """Custom user manager that handles subdomain and role for superusers."""
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        if not username:
            raise ValueError('The Username must be set')
        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', 'SUPERADMIN')
        
        # Generate subdomain from username if not provided
        if 'subdomain' not in extra_fields:
            extra_fields['subdomain'] = username.lower().replace(' ', '')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(username, email, password, **extra_fields)


class User(AbstractUser):
    """
    Custom User model for multi-tenant portfolio platform.
    Extends Django's AbstractUser with additional fields for multi-tenancy.
    """
    
    class Role(models.TextChoices):
        USER = 'USER', 'Portfolio Owner'
        SUPERADMIN = 'SUPERADMIN', 'Platform Admin'
    
    # Role field for access control
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
        help_text="User role for access control"
    )
    
    # Subdomain for multi-tenancy (e.g., 'abhay' for abhay.portfoliopro.site)
    subdomain = models.CharField(
        max_length=50, 
        unique=True,
        db_index=True,
        validators=[
            RegexValidator(
                regex=r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$',
                message='Subdomain must be lowercase alphanumeric with optional hyphens (not at start/end)',
            )
        ],
        help_text="Unique subdomain for portfolio (e.g., 'abhay' for abhay.portfoliopro.site)"
    )
    
    # Account status
    is_banned = models.BooleanField(
        default=False,
        help_text="If banned, user cannot access their portfolio or admin panel"
    )
    email_verified = models.BooleanField(
        default=False,
        help_text="Whether the user has verified their email address"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Custom manager
    objects = UserManager()
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['subdomain']),
            models.Index(fields=['email']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.username} ({self.subdomain})"
    
    @property
    def is_superadmin(self):
        """Check if user has superadmin privileges."""
        return self.role == self.Role.SUPERADMIN
    
    @property
    def is_portfolio_owner(self):
        """Check if user is a regular portfolio owner."""
        return self.role == self.Role.USER
    
    def can_access_portfolio(self):
        """Check if user can access their portfolio."""
        return self.is_active and not self.is_banned
