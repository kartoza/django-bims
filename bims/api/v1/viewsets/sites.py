# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for LocationSite in API v1.
"""
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from bims.api.v1.filters.sites import LocationSiteFilterSet
from bims.api.v1.pagination import LargeResultsSetPagination
from bims.api.v1.permissions import CanEditLocationSite, CanValidate
from bims.api.v1.responses import (
    error_response,
    success_response,
    validation_error_response,
)
from bims.api.v1.serializers.sites import (
    LocationSiteCreateSerializer,
    LocationSiteDetailSerializer,
    LocationSiteListSerializer,
    LocationSiteSummarySerializer,
)
from bims.api.v1.viewsets.base import StandardModelViewSet
from bims.models.location_site import LocationSite


class LocationSiteViewSet(StandardModelViewSet):
    """
    ViewSet for LocationSite CRUD operations.

    Endpoints:
    - GET /api/v1/sites/ - List sites
    - POST /api/v1/sites/ - Create site
    - GET /api/v1/sites/{id}/ - Get site detail
    - PUT /api/v1/sites/{id}/ - Update site
    - DELETE /api/v1/sites/{id}/ - Delete site
    - GET /api/v1/sites/summary/ - Get summary statistics
    - GET /api/v1/sites/nearby/ - Get nearby sites
    - GET /api/v1/sites/coordinates/ - Get site by coordinates
    - POST /api/v1/sites/{id}/validate/ - Validate site
    """

    queryset = LocationSite.objects.select_related("location_type", "owner", "river").all()
    filterset_class = LocationSiteFilterSet
    permission_classes = [IsAuthenticatedOrReadOnly, CanEditLocationSite]
    pagination_class = LargeResultsSetPagination

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return LocationSiteListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return LocationSiteCreateSerializer
        return LocationSiteDetailSerializer

    def get_queryset(self):
        """Optimize queryset based on action."""
        queryset = super().get_queryset()

        if self.action == "list":
            # Add annotation for record count if needed
            queryset = queryset.annotate(record_count=Count("biological_collection_record"))

        return queryset

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get summary statistics for location sites.

        Returns counts of total, validated, pending sites and ecosystem breakdown.
        """
        queryset = self.filter_queryset(self.get_queryset())

        total = queryset.count()
        validated = queryset.filter(validated=True).count()
        pending = total - validated
        with_records = queryset.filter(biological_collection_record__isnull=False).distinct().count()

        # Ecosystem type breakdown
        ecosystem_counts = dict(
            queryset.exclude(ecosystem_type__isnull=True)
            .exclude(ecosystem_type="")
            .values_list("ecosystem_type")
            .annotate(count=Count("id"))
        )

        data = {
            "total_sites": total,
            "validated_sites": validated,
            "pending_sites": pending,
            "sites_with_records": with_records,
            "ecosystem_type_counts": ecosystem_counts,
        }

        serializer = LocationSiteSummarySerializer(data)
        return success_response(data=serializer.data)

    @action(detail=False, methods=["get"])
    def nearby(self, request):
        """
        Get sites near a given coordinate.

        Query params:
        - lat: Latitude (required)
        - lon: Longitude (required)
        - radius: Search radius in meters (default: 10000)
        - limit: Maximum results (default: 10)
        """
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        radius = request.query_params.get("radius", 10000)
        limit = request.query_params.get("limit", 10)

        if not lat or not lon:
            return validation_error_response({"detail": "lat and lon parameters are required"})

        try:
            lat = float(lat)
            lon = float(lon)
            radius = float(radius)
            limit = int(limit)
        except ValueError:
            return validation_error_response({"detail": "Invalid coordinate or parameter values"})

        point = Point(lon, lat, srid=4326)

        queryset = (
            LocationSite.objects.filter(geometry_point__isnull=False)
            .annotate(distance=Distance("geometry_point", point))
            .filter(distance__lte=radius)
            .order_by("distance")[:limit]
        )

        serializer = LocationSiteListSerializer(queryset, many=True)
        return success_response(
            data=serializer.data,
            meta={
                "center": {"lat": lat, "lon": lon},
                "radius": radius,
                "count": len(serializer.data),
            },
        )

    @action(detail=False, methods=["get"])
    def coordinates(self, request):
        """
        Get site by exact coordinates.

        Query params:
        - lat: Latitude (required)
        - lon: Longitude (required)
        - tolerance: Coordinate tolerance in degrees (default: 0.0001)
        """
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        tolerance = request.query_params.get("tolerance", 0.0001)

        if not lat or not lon:
            return validation_error_response({"detail": "lat and lon parameters are required"})

        try:
            lat = float(lat)
            lon = float(lon)
            tolerance = float(tolerance)
        except ValueError:
            return validation_error_response({"detail": "Invalid coordinate values"})

        queryset = LocationSite.objects.filter(
            geometry_point__isnull=False,
            latitude__gte=lat - tolerance,
            latitude__lte=lat + tolerance,
            longitude__gte=lon - tolerance,
            longitude__lte=lon + tolerance,
        )

        if not queryset.exists():
            return success_response(data=None, meta={"found": False})

        serializer = LocationSiteDetailSerializer(queryset.first())
        return success_response(data=serializer.data, meta={"found": True})

    @action(detail=True, methods=["post"], permission_classes=[CanValidate])
    def validate(self, request, pk=None):
        """
        Validate a location site.

        Requires validator permissions.
        """
        try:
            site = self.get_object()
        except LocationSite.DoesNotExist:
            return error_response(
                errors={"detail": "Site not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if site.validated:
            return error_response(
                errors={"detail": "Site is already validated"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        site.validated = True
        site.save()

        serializer = LocationSiteDetailSerializer(site)
        return success_response(data=serializer.data, meta={"validated": True})

    @action(detail=True, methods=["post"], permission_classes=[CanValidate])
    def reject(self, request, pk=None):
        """
        Reject a location site validation.

        Requires validator permissions.
        Body:
        - reason: Rejection reason (optional)
        """
        try:
            site = self.get_object()
        except LocationSite.DoesNotExist:
            return error_response(
                errors={"detail": "Site not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        reason = request.data.get("reason", "")

        site.validated = False
        site.rejected = True
        if reason:
            site.additional_data = site.additional_data or {}
            site.additional_data["rejection_reason"] = reason
        site.save()

        serializer = LocationSiteDetailSerializer(site)
        return success_response(data=serializer.data, meta={"rejected": True, "reason": reason})

    @action(detail=True, methods=["get"])
    def surveys(self, request, pk=None):
        """
        Get all surveys for a location site.
        """
        try:
            site = self.get_object()
        except LocationSite.DoesNotExist:
            return error_response(
                errors={"detail": "Site not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        from bims.api.v1.serializers.surveys import SurveyListSerializer

        surveys = site.survey_set.all().order_by("-date")
        serializer = SurveyListSerializer(surveys, many=True)
        return success_response(data=serializer.data, meta={"count": surveys.count()})

    @action(detail=True, methods=["get"])
    def records(self, request, pk=None):
        """
        Get all biological records for a location site.
        """
        try:
            site = self.get_object()
        except LocationSite.DoesNotExist:
            return error_response(
                errors={"detail": "Site not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        from bims.api.v1.serializers.records import BiologicalCollectionRecordListSerializer

        records = site.biological_collection_record.select_related("taxonomy", "survey").all()

        # Apply pagination
        page = self.paginate_queryset(records)
        if page is not None:
            serializer = BiologicalCollectionRecordListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BiologicalCollectionRecordListSerializer(records, many=True)
        return success_response(data=serializer.data, meta={"count": records.count()})
