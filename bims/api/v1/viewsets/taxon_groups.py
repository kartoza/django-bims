# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for TaxonGroup in API v1.
"""
from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from bims.api.v1.permissions import IsSuperUserOrReadOnly
from bims.api.v1.responses import success_response
from bims.api.v1.serializers.taxon_groups import (
    TaxonGroupCreateSerializer,
    TaxonGroupDetailSerializer,
    TaxonGroupSerializer,
)
from bims.api.v1.viewsets.base import StandardModelViewSet
from bims.models.taxon_group import TaxonGroup


class TaxonGroupViewSet(StandardModelViewSet):
    """
    ViewSet for TaxonGroup CRUD operations.

    Endpoints:
    - GET /api/v1/taxon-groups/ - List taxon groups
    - POST /api/v1/taxon-groups/ - Create taxon group (staff only)
    - GET /api/v1/taxon-groups/{id}/ - Get taxon group detail
    - PUT /api/v1/taxon-groups/{id}/ - Update taxon group (staff only)
    - DELETE /api/v1/taxon-groups/{id}/ - Delete taxon group (superuser only)
    - GET /api/v1/taxon-groups/{id}/taxa/ - Get taxa in group
    """

    queryset = TaxonGroup.objects.all()
    permission_classes = [IsSuperUserOrReadOnly]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "retrieve":
            return TaxonGroupDetailSerializer
        if self.action in ["create", "update", "partial_update"]:
            return TaxonGroupCreateSerializer
        return TaxonGroupSerializer

    def get_queryset(self):
        """Optimize queryset with taxa count."""
        queryset = super().get_queryset()
        return queryset.annotate(taxa_count=Count("taxonomies")).order_by("display_order", "name")

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
        groups = self.get_queryset()

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
