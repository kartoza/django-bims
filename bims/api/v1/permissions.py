# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Permission classes for API v1.

Provides granular permission control for different operations.
"""
from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission to allow owners to edit their own objects.

    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed for any request
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner
        return hasattr(obj, "owner") and obj.owner == request.user


class IsValidatorOrReadOnly(permissions.BasePermission):
    """
    Permission for validation operations.

    Only users with validator role can perform validation actions.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        # Check if user has validator permission
        if not request.user.is_authenticated:
            return False

        # Superusers always have permission
        if request.user.is_superuser:
            return True

        # Check for validator group membership
        return request.user.groups.filter(name__icontains="validator").exists()


class IsSuperUserOrReadOnly(permissions.BasePermission):
    """
    Permission that only allows superusers to make changes.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_superuser


class CanEditLocationSite(permissions.BasePermission):
    """
    Permission for editing location sites.

    Users can edit sites they own or if they are staff/superuser.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user.is_authenticated:
            return False

        # Superusers and staff can edit any site
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Site owners can edit their sites
        return hasattr(obj, "owner") and obj.owner == request.user


class CanEditBiologicalRecord(permissions.BasePermission):
    """
    Permission for editing biological collection records.

    Users can edit records they collected or if they are staff/superuser.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True

        if not request.user.is_authenticated:
            return False

        # Superusers and staff can edit any record
        if request.user.is_superuser or request.user.is_staff:
            return True

        # Collectors can edit their records
        if hasattr(obj, "collector_user") and obj.collector_user == request.user:
            return True

        # Site owners can edit records on their sites
        if hasattr(obj, "site") and hasattr(obj.site, "owner"):
            return obj.site.owner == request.user

        return False


class CanValidate(permissions.BasePermission):
    """
    Permission specifically for validation endpoints.

    Only authenticated users in validation groups can validate.
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        # Check for validator group
        return request.user.groups.filter(name__icontains="validator").exists()


class IsExpertOrSuperuser(permissions.BasePermission):
    """
    Permission for expert-level operations on taxon groups.

    Allows access to:
    - Superusers (always)
    - Staff members
    - Taxon group experts (checked per-taxon-group)
    """

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser or request.user.is_staff:
            return True

        # Check if user is an expert for any taxon group
        from bims.models.taxon_group import TaxonGroup
        return TaxonGroup.objects.filter(experts=request.user).exists()

    def has_object_permission(self, request, view, obj):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser or request.user.is_staff:
            return True

        # Check if user is expert for the object's taxon group
        if hasattr(obj, 'taxon_group') and obj.taxon_group:
            return request.user in obj.taxon_group.experts.all()

        return False
