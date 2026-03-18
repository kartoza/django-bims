# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSets for Boundary models in API v1.
"""
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from bims.api.v1.pagination import LargeResultsSetPagination
from bims.api.v1.permissions import IsOwnerOrReadOnly
from bims.api.v1.responses import error_response, success_response
from bims.api.v1.serializers.boundaries import (
    BoundaryGeoSerializer,
    BoundarySerializer,
    UserBoundaryCreateSerializer,
    UserBoundarySerializer,
)
from bims.api.v1.viewsets.base import ReadOnlyStandardViewSet, StandardModelViewSet
from bims.models.boundary import Boundary
from bims.models.user_boundary import UserBoundary


class BoundaryViewSet(ReadOnlyStandardViewSet):
    """
    ViewSet for Boundary read operations (system boundaries).

    Boundaries are read-only as they represent system-configured geographic boundaries.

    Endpoints:
    - GET /api/v1/boundaries/ - List boundaries
    - GET /api/v1/boundaries/{id}/ - Get boundary detail
    - GET /api/v1/boundaries/{id}/geojson/ - Get boundary as GeoJSON
    """

    queryset = Boundary.objects.all()
    serializer_class = BoundarySerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LargeResultsSetPagination

    def get_queryset(self):
        """Filter and order queryset."""
        queryset = super().get_queryset()

        # Filter by type if provided
        boundary_type = self.request.query_params.get("type")
        if boundary_type:
            queryset = queryset.filter(type__iexact=boundary_type)

        return queryset.order_by("type", "name")

    @action(detail=True, methods=["get"])
    def geojson(self, request, pk=None):
        """
        Get boundary as GeoJSON feature.
        """
        boundary = self.get_object()
        serializer = BoundaryGeoSerializer(boundary)
        return success_response(data=serializer.data)

    @action(detail=False, methods=["get"])
    def types(self, request):
        """
        Get list of boundary types.
        """
        types = Boundary.objects.values_list("type", flat=True).distinct()
        return success_response(
            data=list(types),
            meta={"count": len(types)},
        )


class UserBoundaryViewSet(StandardModelViewSet):
    """
    ViewSet for UserBoundary CRUD operations.

    Endpoints:
    - GET /api/v1/user-boundaries/ - List user's boundaries
    - POST /api/v1/user-boundaries/ - Create boundary
    - GET /api/v1/user-boundaries/{id}/ - Get boundary detail
    - PUT /api/v1/user-boundaries/{id}/ - Update boundary
    - DELETE /api/v1/user-boundaries/{id}/ - Delete boundary
    """

    queryset = UserBoundary.objects.select_related("user").all()
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action in ["create", "update", "partial_update"]:
            return UserBoundaryCreateSerializer
        return UserBoundarySerializer

    def get_queryset(self):
        """Filter to only show user's own boundaries."""
        queryset = super().get_queryset()

        # Non-staff users can only see their own boundaries
        if not self.request.user.is_staff:
            queryset = queryset.filter(user=self.request.user)

        return queryset.order_by("-created")

    def perform_create(self, serializer):
        """Set the user when creating."""
        serializer.save(user=self.request.user)
