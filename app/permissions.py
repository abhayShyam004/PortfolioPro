"""
Object-level permissions for multi-tenant portfolio platform.
These ensure users can only access their own data.
"""

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Object-level permission to only allow owners to access their own objects.
    Assumes the model instance has a `user` attribute.
    """
    message = "You do not have permission to access this resource."
    
    def has_object_permission(self, request, view, obj):
        # Check if object has user attribute
        if hasattr(obj, 'user'):
            return obj.user == request.user
        # Check if object has user_id attribute
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to only allow owners to edit their own objects.
    Read-only access is allowed for any authenticated request.
    """
    message = "You can only modify your own resources."
    
    def has_object_permission(self, request, view, obj):
        # Read permissions allowed for any request (GET, HEAD, OPTIONS)
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only for owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        return False


class IsSuperAdmin(permissions.BasePermission):
    """
    Allows access only to superadmin users.
    """
    message = "This action requires superadmin privileges."
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'is_superadmin') and
            request.user.is_superadmin
        )


class IsSuperAdminOrOwner(permissions.BasePermission):
    """
    Allows access to superadmins or the owner of the object.
    """
    message = "You must be a superadmin or the owner of this resource."
    
    def has_object_permission(self, request, view, obj):
        # Superadmins can access everything
        if hasattr(request.user, 'is_superadmin') and request.user.is_superadmin:
            return True
        
        # Otherwise, must be owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'user_id'):
            return obj.user_id == request.user.id
        return False


class IsOwnerForWriteElseAuthenticated(permissions.BasePermission):
    """
    Allow authenticated users to read, but only owners can write.
    Useful for public portfolio views.
    """
    def has_permission(self, request, view):
        # Must be authenticated
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Read is allowed
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write requires ownership
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return False
