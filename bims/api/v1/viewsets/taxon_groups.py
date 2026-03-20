# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for TaxonGroup in API v1.
"""
from django.db.models import Count, Q
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from bims.api.v1.permissions import IsSuperUserOrReadOnly
from bims.api.v1.responses import (
    error_response,
    success_response,
    validation_error_response,
)
from bims.api.v1.serializers.taxon_groups import (
    TaxonGroupCreateSerializer,
    TaxonGroupDetailSerializer,
    TaxonGroupSerializer,
)
from bims.api.v1.viewsets.base import StandardModelViewSet
from bims.models.taxon_group import TaxonGroup


class TaxonGroupViewSet(StandardModelViewSet):
    """
    ViewSet for TaxonGroup CRUD operations with approval workflow.

    Endpoints:
    - GET /api/v1/taxon-groups/ - List approved taxon groups (+ pending for staff)
    - POST /api/v1/taxon-groups/ - Propose new taxon group (authenticated)
    - GET /api/v1/taxon-groups/{id}/ - Get taxon group detail
    - PUT /api/v1/taxon-groups/{id}/ - Update taxon group (staff only)
    - DELETE /api/v1/taxon-groups/{id}/ - Delete taxon group (superuser only)
    - GET /api/v1/taxon-groups/{id}/taxa/ - Get taxa in group
    - GET /api/v1/taxon-groups/pending/ - List pending proposals (staff only)
    - POST /api/v1/taxon-groups/{id}/approve/ - Approve taxon group (staff only)
    - POST /api/v1/taxon-groups/{id}/reject/ - Reject taxon group (staff only)
    """

    queryset = TaxonGroup.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_permissions(self):
        """Return appropriate permissions based on action."""
        if self.action in ["approve", "reject", "pending"]:
            return [IsSuperUserOrReadOnly()]
        if self.action in ["update", "partial_update", "destroy"]:
            return [IsSuperUserOrReadOnly()]
        return super().get_permissions()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "retrieve":
            return TaxonGroupDetailSerializer
        if self.action in ["create", "update", "partial_update"]:
            return TaxonGroupCreateSerializer
        return TaxonGroupSerializer

    def get_queryset(self):
        """
        Filter queryset based on user permissions.

        - Regular users see only approved groups
        - Staff/superusers see all groups (approved + pending)
        - Users can see their own pending proposals
        """
        queryset = super().get_queryset()
        queryset = queryset.annotate(taxa_count=Count("taxonomies"))

        user = self.request.user

        # Staff see everything
        if user.is_authenticated and (user.is_staff or user.is_superuser):
            return queryset.order_by("display_order", "name")

        # Regular users see approved groups + their own proposals
        if user.is_authenticated:
            queryset = queryset.filter(
                Q(is_approved=True) | Q(proposed_by=user)
            )
        else:
            queryset = queryset.filter(is_approved=True)

        return queryset.order_by("display_order", "name")

    def perform_create(self, serializer):
        """Set proposed_by and is_approved=False for new groups."""
        user = self.request.user

        # Staff can create pre-approved groups
        if user.is_staff or user.is_superuser:
            serializer.save(
                proposed_by=user,
                is_approved=True,
                approved_by=user,
                approved_at=timezone.now(),
            )
        else:
            # Regular users create proposals that need approval
            serializer.save(
                proposed_by=user,
                is_approved=False,
            )

    @action(detail=True, methods=["get"])
    def taxa(self, request, pk=None):
        """
        Get all taxa in this taxon group.
        """
        group = self.get_object()

        from bims.api.v1.serializers.taxa import TaxonomyListSerializer

        taxa = group.taxonomies.select_related("iucn_status", "endemism").all()

        # Apply pagination
        page = self.paginate_queryset(taxa)
        if page is not None:
            serializer = TaxonomyListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TaxonomyListSerializer(taxa, many=True)
        return success_response(data=serializer.data, meta={"count": taxa.count()})

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get summary of all taxon groups.
        """
        groups = self.get_queryset().filter(is_approved=True)

        data = [
            {
                "id": g.id,
                "name": g.name,
                "category": g.category,
                "taxa_count": g.taxa_count,
            }
            for g in groups
        ]

        return success_response(
            data=data,
            meta={"total_groups": len(data)},
        )

    @action(detail=False, methods=["get"], permission_classes=[IsSuperUserOrReadOnly])
    def pending(self, request):
        """
        List pending taxon group proposals.

        Only accessible by staff/superusers.
        """
        pending_groups = TaxonGroup.objects.filter(
            is_approved=False,
            rejection_reason__isnull=True,
        ).annotate(taxa_count=Count("taxonomies")).order_by("-id")

        serializer = TaxonGroupSerializer(pending_groups, many=True)

        return success_response(
            data=serializer.data,
            meta={"count": pending_groups.count()},
        )

    @action(detail=True, methods=["post"], permission_classes=[IsSuperUserOrReadOnly])
    def approve(self, request, pk=None):
        """
        Approve a pending taxon group.

        Only accessible by staff/superusers.
        """
        try:
            group = self.get_object()
        except TaxonGroup.DoesNotExist:
            return error_response(
                errors={"detail": "Taxon group not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if group.is_approved:
            return error_response(
                errors={"detail": "Taxon group is already approved"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        group.is_approved = True
        group.approved_by = request.user
        group.approved_at = timezone.now()
        group.rejection_reason = None
        group.save()

        serializer = TaxonGroupDetailSerializer(group)
        return success_response(
            data=serializer.data,
            meta={"approved": True, "approved_by": request.user.username},
        )

    @action(detail=True, methods=["post"], permission_classes=[IsSuperUserOrReadOnly])
    def reject(self, request, pk=None):
        """
        Reject a pending taxon group.

        Body:
        - reason: Rejection reason (required)

        Only accessible by staff/superusers.
        """
        try:
            group = self.get_object()
        except TaxonGroup.DoesNotExist:
            return error_response(
                errors={"detail": "Taxon group not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        reason = request.data.get("reason")
        if not reason:
            return validation_error_response({"reason": "Rejection reason is required"})

        group.is_approved = False
        group.rejection_reason = reason
        group.save()

        serializer = TaxonGroupDetailSerializer(group)
        return success_response(
            data=serializer.data,
            meta={"rejected": True, "reason": reason},
        )
