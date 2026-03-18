# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for Taxonomy in API v1.
"""
from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from bims.api.v1.filters.taxa import TaxonomyFilterSet
from bims.api.v1.pagination import LargeResultsSetPagination
from bims.api.v1.permissions import CanValidate, IsSuperUserOrReadOnly
from bims.api.v1.responses import (
    error_response,
    success_response,
    validation_error_response,
)
from bims.api.v1.serializers.taxa import (
    TaxonomyCreateSerializer,
    TaxonomyDetailSerializer,
    TaxonomyListSerializer,
    TaxonomyTreeSerializer,
)
from bims.api.v1.viewsets.base import StandardModelViewSet
from bims.models.taxonomy import Taxonomy


class TaxonomyViewSet(StandardModelViewSet):
    """
    ViewSet for Taxonomy CRUD operations.

    Endpoints:
    - GET /api/v1/taxa/ - List taxa
    - POST /api/v1/taxa/ - Create taxon
    - GET /api/v1/taxa/{id}/ - Get taxon detail
    - PUT /api/v1/taxa/{id}/ - Update taxon
    - DELETE /api/v1/taxa/{id}/ - Delete taxon
    - GET /api/v1/taxa/{id}/tree/ - Get taxon tree
    - GET /api/v1/taxa/{id}/images/ - Get taxon images
    - GET /api/v1/taxa/find/ - Find taxon by name
    - GET /api/v1/taxa/proposals/ - List pending proposals
    - POST /api/v1/taxa/{id}/validate/ - Validate taxon
    """

    queryset = Taxonomy.objects.select_related(
        "parent",
        "iucn_status",
        "national_conservation_status",
        "endemism",
    ).all()
    filterset_class = TaxonomyFilterSet
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LargeResultsSetPagination

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return TaxonomyListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return TaxonomyCreateSerializer
        elif self.action == "tree":
            return TaxonomyTreeSerializer
        return TaxonomyDetailSerializer

    def get_queryset(self):
        """Optimize queryset based on action."""
        queryset = super().get_queryset()

        if self.action == "list":
            # Add record count annotation
            queryset = queryset.annotate(record_count=Count("biologicalcollectionrecord"))

        return queryset.order_by("canonical_name", "scientific_name")

    @action(detail=True, methods=["get"])
    def tree(self, request, pk=None):
        """
        Get taxonomy tree starting from this taxon.

        Query params:
        - direction: 'up' for ancestors, 'down' for descendants (default: 'down')
        - depth: Maximum tree depth (default: 10)
        """
        try:
            taxon = self.get_object()
        except Taxonomy.DoesNotExist:
            return error_response(
                errors={"detail": "Taxon not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        direction = request.query_params.get("direction", "down")
        depth = int(request.query_params.get("depth", 10))

        if direction == "up":
            # Get ancestors
            ancestors = []
            current = taxon
            visited = set()

            while current and len(ancestors) < depth:
                if current.id in visited:
                    break
                visited.add(current.id)
                ancestors.insert(
                    0,
                    {
                        "id": current.id,
                        "name": current.canonical_name or current.scientific_name,
                        "rank": current.rank,
                    },
                )
                current = current.parent

            return success_response(
                data=ancestors,
                meta={"direction": "up", "depth": len(ancestors)},
            )

        else:
            # Get descendants tree
            def build_tree(node, current_depth):
                if current_depth >= depth:
                    return None

                children = Taxonomy.objects.filter(parent=node).select_related("parent")
                children_data = []

                for child in children:
                    child_tree = build_tree(child, current_depth + 1)
                    child_data = {
                        "id": child.id,
                        "name": child.canonical_name or child.scientific_name,
                        "rank": child.rank,
                        "children": child_tree or [],
                    }
                    children_data.append(child_data)

                return children_data

            tree_data = {
                "id": taxon.id,
                "name": taxon.canonical_name or taxon.scientific_name,
                "rank": taxon.rank,
                "children": build_tree(taxon, 0) or [],
            }

            return success_response(
                data=tree_data,
                meta={"direction": "down", "max_depth": depth},
            )

    @action(detail=True, methods=["get"])
    def images(self, request, pk=None):
        """
        Get images for a taxon.
        """
        try:
            taxon = self.get_object()
        except Taxonomy.DoesNotExist:
            return error_response(
                errors={"detail": "Taxon not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        # Get taxon images if the model exists
        try:
            from bims.models.taxonomy import TaxonImage

            images = TaxonImage.objects.filter(taxonomy=taxon)
            data = [
                {
                    "id": img.id,
                    "url": img.source if hasattr(img, "source") else None,
                    "title": getattr(img, "title", None),
                }
                for img in images
            ]
        except ImportError:
            data = []

        return success_response(data=data, meta={"count": len(data)})

    @action(detail=False, methods=["get"])
    def find(self, request):
        """
        Find taxon by name with autocomplete support.

        Query params:
        - q: Search query (required)
        - rank: Filter by rank
        - limit: Maximum results (default: 20)
        """
        query = request.query_params.get("q")
        rank = request.query_params.get("rank")
        limit = int(request.query_params.get("limit", 20))

        if not query:
            return validation_error_response({"detail": "Query parameter 'q' is required"})

        queryset = Taxonomy.objects.filter(
            models.Q(scientific_name__icontains=query)
            | models.Q(canonical_name__icontains=query)
            | models.Q(vernacular_names__name__icontains=query)
        ).distinct()

        if rank:
            queryset = queryset.filter(rank__iexact=rank)

        queryset = queryset.select_related("iucn_status", "endemism")[:limit]

        serializer = TaxonomyListSerializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            meta={"query": query, "count": len(serializer.data)},
        )

    @action(detail=False, methods=["get"])
    def proposals(self, request):
        """
        List pending taxonomy proposals.

        Requires authentication.
        """
        if not request.user.is_authenticated:
            return error_response(
                errors={"detail": "Authentication required"},
                status_code=status.HTTP_401_UNAUTHORIZED,
            )

        # Get taxa with pending validation
        queryset = Taxonomy.objects.filter(validated=False).select_related(
            "parent",
            "iucn_status",
            "owner",
        )

        # Staff/superusers see all, others see their own
        if not request.user.is_staff and not request.user.is_superuser:
            queryset = queryset.filter(owner=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TaxonomyListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = TaxonomyListSerializer(queryset, many=True)
        return success_response(data=serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[CanValidate])
    def validate(self, request, pk=None):
        """
        Validate a taxonomy record.

        Requires validator permissions.
        """
        try:
            taxon = self.get_object()
        except Taxonomy.DoesNotExist:
            return error_response(
                errors={"detail": "Taxon not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if taxon.validated:
            return error_response(
                errors={"detail": "Taxon is already validated"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        taxon.validated = True
        taxon.save()

        serializer = TaxonomyDetailSerializer(taxon)
        return success_response(data=serializer.data, meta={"validated": True})

    @action(detail=True, methods=["post"], permission_classes=[CanValidate])
    def reject(self, request, pk=None):
        """
        Reject a taxonomy record.

        Requires validator permissions.
        """
        try:
            taxon = self.get_object()
        except Taxonomy.DoesNotExist:
            return error_response(
                errors={"detail": "Taxon not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        reason = request.data.get("reason", "")

        taxon.validated = False
        taxon.rejected = True
        if reason:
            taxon.additional_data = taxon.additional_data or {}
            taxon.additional_data["rejection_reason"] = reason
        taxon.save()

        serializer = TaxonomyDetailSerializer(taxon)
        return success_response(data=serializer.data, meta={"rejected": True, "reason": reason})

    @action(detail=True, methods=["get"])
    def records(self, request, pk=None):
        """
        Get biological records for this taxon.
        """
        try:
            taxon = self.get_object()
        except Taxonomy.DoesNotExist:
            return error_response(
                errors={"detail": "Taxon not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        from bims.api.v1.serializers.records import BiologicalCollectionRecordListSerializer

        records = taxon.biologicalcollectionrecord_set.select_related("site", "survey").all()

        page = self.paginate_queryset(records)
        if page is not None:
            serializer = BiologicalCollectionRecordListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BiologicalCollectionRecordListSerializer(records, many=True)
        return success_response(data=serializer.data, meta={"count": records.count()})


# Import models for filter
from django.db import models
