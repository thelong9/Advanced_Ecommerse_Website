"""
Custom permissions for the API.
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: only the owner of an object can edit it.
    Assumes the model has a 'user' field.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions for any request (GET, HEAD, OPTIONS)
        if request.method in SAFE_METHODS:
            return True
        # Write permissions only for the owner
        return obj.user == request.user


class IsAdminOrReadOnly(BasePermission):
    """
    Allow read access to everyone, but write access only to admin users.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff
