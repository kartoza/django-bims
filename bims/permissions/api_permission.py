from rest_framework.permissions import BasePermission
from django.contrib.auth.models import Permission
from bims.models.taxon import Taxon


class IsValidator(BasePermission):
    """
    Allows access only to validators.
    """
    def has_permission(self, request, view):
        if request.user.is_active and request.user.is_superuser:
            return True
        if request.user.is_anonymous:
            return False
        return Permission.objects.filter(
                group__user=request.user,
                codename__contains='can_validate').exists()


class AllowedTaxon(object):
    """
    Get allowed taxon.
    """

    def get(self, user):
        """Return taxon that user has permission to validate."""

        if user.is_active and user.is_superuser:
            return Taxon.objects.all()

        all_data_flag = 'data'

        permissions = Permission.objects.filter(
                group__user=user,
                codename__contains='can_validate').values('name')
        allowed_classes = []

        for permission in permissions:
            try:
                class_name = permission['name'].split(' ')[2]
                if class_name.lower() == all_data_flag:
                    return Taxon.objects.all()
            except (ValueError, KeyError):
                continue
            allowed_classes.append(class_name)

        taxa = Taxon.objects.filter(taxon_class__in=allowed_classes)
        return taxa
