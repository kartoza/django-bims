# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for LocationSite in API v1.

Made with love by Kartoza | https://kartoza.com
"""
from django.contrib.gis.geos import Point
from django.contrib.gis.db.models.functions import Distance
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from bims.api.v1.compat import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiTypes,
)

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


@extend_schema_view(
    list=extend_schema(
        summary="List location sites",
        description="""
Retrieve a paginated list of location sites (monitoring points).

Sites are the primary geographic entities where biodiversity surveys are conducted.
Each site has a unique code, geographic coordinates, and can be associated with
rivers, wetlands, or other ecosystem types.

### Filtering

You can filter sites using the following query parameters:
- `search`: Search in site code and name
- `ecosystem_type`: Filter by ecosystem type (river, wetland, estuary, dam, lake)
- `validated`: Filter by validation status (true/false)
- `river`: Filter by river name
- `taxon_group`: Filter by taxon group ID (sites with records from this group)

### Example

```
GET /api/v1/sites/?ecosystem_type=river&validated=true
```
        """,
        tags=["Sites"],
        responses={200: LocationSiteListSerializer(many=True)},
    ),
    retrieve=extend_schema(
        summary="Get site details",
        description="""
Retrieve detailed information about a specific location site.

Includes full site metadata, coordinates, associated river/wetland information,
and recent survey data.
        """,
        tags=["Sites"],
        responses={200: LocationSiteDetailSerializer},
    ),
    create=extend_schema(
        summary="Create a location site",
        description="""
Create a new location site (monitoring point).

### Required Fields
- `site_code`: Unique identifier for the site
- `name`: Human-readable name
- `latitude` and `longitude`: Geographic coordinates (WGS84)

### Optional Fields
- `description`: Site description
- `ecosystem_type`: Type of ecosystem
- `river_name`: Associated river (if applicable)

The site will be created with `validated=False` and require validation
by a staff member before being fully active.
        """,
        tags=["Sites"],
        request=LocationSiteCreateSerializer,
        responses={201: LocationSiteDetailSerializer},
        examples=[
            OpenApiExample(
                "Example Site",
                value={
                    "site_code": "SITE001",
                    "name": "Orange River Site 1",
                    "latitude": -28.4792,
                    "longitude": 16.9946,
                    "ecosystem_type": "river",
                    "river_name": "Orange River",
                    "description": "Monitoring site near the Orange River mouth",
                },
            ),
        ],
    ),
    update=extend_schema(
        summary="Update a location site",
        description="Update all fields of an existing location site.",
        tags=["Sites"],
    ),
    partial_update=extend_schema(
        summary="Partially update a location site",
        description="Update specific fields of an existing location site.",
        tags=["Sites"],
    ),
    destroy=extend_schema(
        summary="Delete a location site",
        description="""
Delete a location site.

**Warning**: This will also delete all associated surveys and biological records.
This action requires appropriate permissions.
        """,
        tags=["Sites"],
    ),
)
class LocationSiteViewSet(StandardModelViewSet):
    """
    ViewSet for managing location sites (monitoring points).

    Location sites are the fundamental geographic entities in BIMS where
    biodiversity surveys are conducted. Each site has:

    - A unique site code and name
    - Geographic coordinates (point location)
    - Ecosystem classification (river, wetland, estuary, etc.)
    - Associated environmental context
    - Linked biological records from surveys
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

    @extend_schema(
        summary="Get site summary statistics",
        description="""
Get aggregated statistics about location sites.

Returns counts of:
- Total sites
- Validated vs pending sites
- Sites with biological records
- Breakdown by ecosystem type
        """,
        tags=["Sites"],
        parameters=[
            OpenApiParameter(
                name="ecosystem_type",
                type=str,
                description="Filter summary by ecosystem type",
            ),
            OpenApiParameter(
                name="validated",
                type=bool,
                description="Filter summary by validation status",
            ),
        ],
        responses={
            200: OpenApiTypes.OBJECT,
        },
        examples=[
            OpenApiExample(
                "Summary Response",
                value={
                    "success": True,
                    "data": {
                        "total_sites": 1500,
                        "validated_sites": 1200,
                        "pending_sites": 300,
                        "sites_with_records": 1100,
                        "ecosystem_type_counts": {
                            "river": 800,
                            "wetland": 400,
                            "estuary": 200,
                            "dam": 100,
                        },
                    },
                },
            ),
        ],
    )
    @action(detail=False, methods=["get"])
    def summary(self, request):
        """Get summary statistics for location sites."""
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

    @extend_schema(
        summary="Find nearby sites",
        description="""
Find location sites near a given coordinate.

Useful for finding existing sites when adding new data or exploring
nearby monitoring locations.
        """,
        tags=["Sites"],
        parameters=[
            OpenApiParameter(
                name="lat",
                type=float,
                required=True,
                description="Latitude of the center point (decimal degrees, WGS84)",
                examples=[
                    OpenApiExample("Cape Town", value=-33.9249),
                    OpenApiExample("Johannesburg", value=-26.2041),
                ],
            ),
            OpenApiParameter(
                name="lon",
                type=float,
                required=True,
                description="Longitude of the center point (decimal degrees, WGS84)",
                examples=[
                    OpenApiExample("Cape Town", value=18.4241),
                    OpenApiExample("Johannesburg", value=28.0473),
                ],
            ),
            OpenApiParameter(
                name="radius",
                type=float,
                default=10000,
                description="Search radius in meters (default: 10000)",
            ),
            OpenApiParameter(
                name="limit",
                type=int,
                default=10,
                description="Maximum number of results (default: 10)",
            ),
        ],
        responses={200: LocationSiteListSerializer(many=True)},
    )
    @action(detail=False, methods=["get"])
    def nearby(self, request):
        """Get sites near a given coordinate."""
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

    @extend_schema(
        summary="Find site by coordinates",
        description="""
Find a location site at specific coordinates.

Searches for sites within a small tolerance of the given coordinates.
Useful for checking if a site already exists at a location.
        """,
        tags=["Sites"],
        parameters=[
            OpenApiParameter(
                name="lat",
                type=float,
                required=True,
                description="Latitude (decimal degrees)",
            ),
            OpenApiParameter(
                name="lon",
                type=float,
                required=True,
                description="Longitude (decimal degrees)",
            ),
            OpenApiParameter(
                name="tolerance",
                type=float,
                default=0.0001,
                description="Coordinate tolerance in degrees (default: 0.0001 ≈ 11 meters)",
            ),
        ],
        responses={200: LocationSiteDetailSerializer},
    )
    @action(detail=False, methods=["get"])
    def coordinates(self, request):
        """Get site by exact coordinates."""
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

    @extend_schema(
        summary="Validate a site",
        description="""
Mark a location site as validated.

**Requires validation permissions.**

Validation confirms that the site information has been reviewed and
is correct. Only validated sites appear in public searches by default.
        """,
        tags=["Sites"],
        request=None,
        responses={
            200: LocationSiteDetailSerializer,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
            404: OpenApiTypes.OBJECT,
        },
    )
    @action(detail=True, methods=["post"], permission_classes=[CanValidate])
    def validate(self, request, pk=None):
        """Validate a location site."""
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

    @extend_schema(
        summary="Reject a site",
        description="""
Reject a location site validation.

**Requires validation permissions.**

Rejected sites are flagged and require correction before resubmission.
        """,
        tags=["Sites"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "reason": {
                        "type": "string",
                        "description": "Reason for rejection",
                    },
                },
            },
        },
        responses={200: LocationSiteDetailSerializer},
    )
    @action(detail=True, methods=["post"], permission_classes=[CanValidate])
    def reject(self, request, pk=None):
        """Reject a location site validation."""
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

    @extend_schema(
        summary="Bulk validate sites",
        description="""
Validate multiple location sites at once.

**Requires validation permissions.**

Provide a list of site IDs in the request body.
        """,
        tags=["Sites"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of site IDs to validate",
                    },
                },
                "required": ["ids"],
            },
        },
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["post"], permission_classes=[CanValidate], url_path="bulk-validate")
    def bulk_validate(self, request):
        """Bulk validate multiple location sites."""
        ids = request.data.get("ids", [])

        if not ids:
            return validation_error_response({"detail": "ids is required"})

        sites = LocationSite.objects.filter(id__in=ids, validated=False)
        count = sites.count()

        sites.update(validated=True, rejected=False)

        return success_response(
            data={"validated_count": count},
            meta={"site_ids": ids},
        )

    @extend_schema(
        summary="Bulk reject sites",
        description="""
Reject multiple location sites at once.

**Requires validation permissions.**

Provide a list of site IDs and an optional rejection reason.
        """,
        tags=["Sites"],
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of site IDs to reject",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Reason for rejection",
                    },
                },
                "required": ["ids"],
            },
        },
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["post"], permission_classes=[CanValidate], url_path="bulk-reject")
    def bulk_reject(self, request):
        """Bulk reject multiple location sites."""
        ids = request.data.get("ids", [])
        reason = request.data.get("reason", "")

        if not ids:
            return validation_error_response({"detail": "ids is required"})

        sites = LocationSite.objects.filter(id__in=ids)
        count = sites.count()

        sites.update(validated=False, rejected=True)

        return success_response(
            data={"rejected_count": count},
            meta={"site_ids": ids, "reason": reason},
        )

    @extend_schema(
        summary="Get minimal site points for map rendering",
        description="""
Get all location sites as minimal point data for map rendering.

Returns only the essential data needed for map display:
- UUID (unique identifier)
- Longitude
- Latitude

This endpoint is optimized for performance and data security - it does not
expose any other site metadata. Use the detail endpoint to get full site info
when a point is selected.

Supports filtering by taxon_group to show only sites with records from
specific taxon groups.
        """,
        tags=["Sites"],
        parameters=[
            OpenApiParameter(
                name="taxon_group",
                type=int,
                description="Filter by taxon group ID (only sites with records from this group)",
            ),
        ],
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["get"], url_path="map-points")
    def map_points(self, request):
        """Get minimal site data for map rendering (location + UUID + record count)."""
        from django.db.models import Count

        queryset = LocationSite.objects.filter(
            geometry_point__isnull=False
        )

        # Filter by taxon group if provided
        taxon_group = request.query_params.get("taxon_group")
        if taxon_group:
            try:
                taxon_group_id = int(taxon_group)
                queryset = queryset.filter(
                    biological_collection_record__module_group_id=taxon_group_id
                )
            except ValueError:
                pass

        # Annotate with record count and get minimal data
        queryset = queryset.annotate(
            record_count=Count("biological_collection_record")
        ).filter(
            record_count__gt=0  # Only sites with records
        ).values_list("uuid", "longitude", "latitude", "record_count")

        # Format as array of [uuid, lon, lat, count] for minimal payload
        data = [
            [str(uuid), float(lon), float(lat), count]
            for uuid, lon, lat, count in queryset
            if lon and lat
        ]

        return success_response(
            data=data,
            meta={
                "count": len(data),
                "format": ["uuid", "longitude", "latitude", "record_count"],
            },
        )

    @extend_schema(
        summary="Get site surveys",
        description="""
Get all surveys (site visits) conducted at this location site.

Surveys are ordered by date, most recent first.
        """,
        tags=["Sites"],
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["get"])
    def surveys(self, request, pk=None):
        """Get all surveys for a location site."""
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

    @extend_schema(
        summary="Get site records",
        description="""
Get all biological collection records from this location site.

Records are paginated and include taxonomy information.
        """,
        tags=["Sites"],
        parameters=[
            OpenApiParameter(name="page", type=int, description="Page number"),
            OpenApiParameter(name="page_size", type=int, description="Results per page"),
        ],
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=True, methods=["get"])
    def records(self, request, pk=None):
        """Get all biological records for a location site."""
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
