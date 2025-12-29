from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model

User = get_user_model()


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom admin for the User model.
    Extends Django's UserAdmin with custom fields.
    """
    list_display = [
        'username', 'email', 'subdomain', 'role', 
        'is_active', 'is_banned', 'email_verified', 'created_at'
    ]
    list_filter = ['role', 'is_active', 'is_banned', 'email_verified', 'created_at']
    search_fields = ['username', 'email', 'subdomain', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Portfolio', {'fields': ('subdomain', 'role')}),
        ('Status', {'fields': ('is_active', 'is_banned', 'email_verified')}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'subdomain', 'password1', 'password2', 'role'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at', 'last_login', 'date_joined']
