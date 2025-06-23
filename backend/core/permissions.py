from rest_framework import permissions

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only to the owner
        return obj.user == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admin users to edit.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission for owner or admin access
    """
    def has_object_permission(self, request, view, obj):
        return obj.user == request.user or request.user.is_staff

class IsVerifiedUser(permissions.BasePermission):
    """
    Permission for verified users only
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_verified
