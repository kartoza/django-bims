from rest_framework.permissions import BasePermission


class IsValidator(BasePermission):
    """
    Allows access only to validators.
    """
    def has_permission(self, request, view):
        return request.user.has_perm('bims.can_validate_data')
