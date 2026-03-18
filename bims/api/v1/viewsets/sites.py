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
- ID (unique identifier)
- Longitude
- Latitude
- Record count (matching current filters)

This endpoint is optimized for performance and data security - it does not
expose any other site metadata. Use the detail endpoint to get full site info
when a point is selected.

Supports all search filters - points are hidden if they have no records matching
the current filter criteria.

**Caching**: Results are cached in Redis for 5 minutes to reduce database load.
The cache key is based on the filter parameters.
        """,
        tags=["Sites"],
        parameters=[
            OpenApiParameter(
                name="taxon_group",
                type=int,
                description="Filter by taxon group ID (only sites with records from this group)",
            ),
            OpenApiParameter(
                name="year_from",
                type=int,
                description="Filter by collection date year (from)",
            ),
            OpenApiParameter(
                name="year_to",
                type=int,
                description="Filter by collection date year (to)",
            ),
            OpenApiParameter(
                name="iucn_category",
                type=str,
                description="Filter by IUCN category (comma-separated: CR,EN,VU)",
            ),
            OpenApiParameter(
                name="endemism",
                type=str,
                description="Filter by endemism (comma-separated)",
            ),
            OpenApiParameter(
                name="collector",
                type=str,
                description="Filter by collector name (comma-separated)",
            ),
            OpenApiParameter(
                name="validated",
                type=bool,
                description="Filter by validation status",
            ),
            OpenApiParameter(
                name="search",
                type=str,
                description="Search in taxon name or site code",
            ),
            OpenApiParameter(
                name="boundary",
                type=int,
                description="Filter by boundary ID (sites within boundary)",
            ),
            OpenApiParameter(
                name="bbox",
                type=str,
                description="Bounding box filter: west,south,east,north",
            ),
            OpenApiParameter(
                name="nocache",
                type=bool,
                description="Bypass cache and fetch fresh data",
            ),
        ],
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["get"], url_path="map-points")
    def map_points(self, request):
        """Get minimal site data for map rendering (location + ID + record count)."""
        import hashlib
        from django.core.cache import cache
        from django.db.models import Count
        from django.contrib.gis.geos import Polygon

        # Cache settings
        CACHE_TIMEOUT = 300  # 5 minutes
        CACHE_PREFIX = "map_points"
        CACHE_VERSION_KEY = "map_points_version"

        # Get current cache version (incremented on invalidation)
        cache_version = cache.get(CACHE_VERSION_KEY, 1)

        # Build cache key from query parameters
        cache_params = {
            "taxon_group": request.query_params.get("taxon_group", ""),
            "year_from": request.query_params.get("year_from", ""),
            "year_to": request.query_params.get("year_to", ""),
            "iucn_category": request.query_params.get("iucn_category", ""),
            "endemism": request.query_params.get("endemism", ""),
            "collector": request.query_params.get("collector", ""),
            "validated": request.query_params.get("validated", ""),
            "search": request.query_params.get("search", ""),
            "boundary": request.query_params.get("boundary", ""),
            "bbox": request.query_params.get("bbox", ""),
        }

        # Create a stable hash of the parameters including version
        param_string = "&".join(f"{k}={v}" for k, v in sorted(cache_params.items()) if v)
        cache_key = f"{CACHE_PREFIX}:v{cache_version}:{hashlib.md5(param_string.encode()).hexdigest()}"

        # Check if we should bypass cache
        nocache = request.query_params.get("nocache", "").lower() in ("true", "1")

        # Try to get from cache
        if not nocache:
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return success_response(
                    data=cached_data["data"],
                    meta={
                        **cached_data["meta"],
                        "cached": True,
                        "cache_key": cache_key,
                    },
                )

        queryset = LocationSite.objects.filter(
            geometry_point__isnull=False
        )

        # Build record filter conditions for counting
        record_filter = Q()
        has_filters = False

        # Filter by taxon group if provided
        taxon_group = request.query_params.get("taxon_group")
        if taxon_group:
            try:
                taxon_group_id = int(taxon_group)
                record_filter &= Q(biological_collection_record__module_group_id=taxon_group_id)
                has_filters = True
            except ValueError:
                pass

        # Filter by date range
        year_from = request.query_params.get("year_from")
        if year_from:
            try:
                year_from_int = int(year_from)
                record_filter &= Q(biological_collection_record__collection_date__year__gte=year_from_int)
                has_filters = True
            except ValueError:
                pass

        year_to = request.query_params.get("year_to")
        if year_to:
            try:
                year_to_int = int(year_to)
                record_filter &= Q(biological_collection_record__collection_date__year__lte=year_to_int)
                has_filters = True
            except ValueError:
                pass

        # Filter by IUCN category
        iucn_category = request.query_params.get("iucn_category")
        if iucn_category:
            categories = [c.strip() for c in iucn_category.split(",") if c.strip()]
            if categories:
                record_filter &= Q(biological_collection_record__taxonomy__iucn_status__category__in=categories)
                has_filters = True

        # Filter by endemism
        endemism = request.query_params.get("endemism")
        if endemism:
            endemism_names = [e.strip() for e in endemism.split(",") if e.strip()]
            if endemism_names:
                record_filter &= Q(biological_collection_record__taxonomy__endemism__name__in=endemism_names)
                has_filters = True

        # Filter by collector
        collector = request.query_params.get("collector")
        if collector:
            collectors = [c.strip() for c in collector.split(",") if c.strip()]
            if collectors:
                collector_q = Q()
                for c in collectors:
                    collector_q |= Q(biological_collection_record__collector__icontains=c)
                record_filter &= collector_q
                has_filters = True

        # Filter by validation status
        validated = request.query_params.get("validated")
        if validated is not None:
            if validated.lower() in ("true", "1"):
                record_filter &= Q(biological_collection_record__validated=True)
                has_filters = True
            elif validated.lower() in ("false", "0"):
                record_filter &= Q(biological_collection_record__validated=False)
                has_filters = True

        # Filter by search (taxon name or site code)
        search = request.query_params.get("search")
        if search:
            search_q = Q(
                biological_collection_record__taxonomy__canonical_name__icontains=search
            ) | Q(
                biological_collection_record__taxonomy__scientific_name__icontains=search
            ) | Q(
                site_code__icontains=search
            ) | Q(
                name__icontains=search
            )
            record_filter &= search_q
            has_filters = True

        # Filter by boundary
        boundary_id = request.query_params.get("boundary")
        if boundary_id:
            try:
                boundary_id_int = int(boundary_id)
                from bims.models.boundary import Boundary
                try:
                    boundary = Boundary.objects.get(id=boundary_id_int)
                    if boundary.geometry:
                        queryset = queryset.filter(geometry_point__within=boundary.geometry)
                except Boundary.DoesNotExist:
                    pass
            except ValueError:
                pass

        # Filter by bounding box
        bbox = request.query_params.get("bbox")
        if bbox:
            try:
                west, south, east, north = [float(x.strip()) for x in bbox.split(",")]
                bbox_polygon = Polygon.from_bbox((west, south, east, north))
                bbox_polygon.srid = 4326
                queryset = queryset.filter(geometry_point__within=bbox_polygon)
            except (ValueError, TypeError):
                pass

        # Annotate with filtered record count
        if has_filters:
            # Count only records matching the filters
            queryset = queryset.annotate(
                rec_count=Count("biological_collection_record", filter=record_filter)
            )
            # Only show sites with matching records when filters are active
            queryset = queryset.filter(rec_count__gt=0)
        else:
            # No filters - show all sites with their total record count
            queryset = queryset.annotate(
                rec_count=Count("biological_collection_record")
            )

        queryset = queryset.values_list("id", "longitude", "latitude", "rec_count")

        # Format as array of [id, lon, lat, count] for minimal payload
        data = [
            [site_id, float(lon), float(lat), count]
            for site_id, lon, lat, count in queryset
            if lon and lat
        ]

        meta = {
            "count": len(data),
            "format": ["id", "longitude", "latitude", "record_count"],
            "filtered": has_filters,
        }

        # Cache the results
        cache.set(
            cache_key,
            {"data": data, "meta": meta},
            CACHE_TIMEOUT
        )

        return success_response(
            data=data,
            meta={
                **meta,
                "cached": False,
                "cache_key": cache_key,
            },
        )

    @extend_schema(
        summary="Get map points cache version",
        description="""
Get the current cache version for map points.

Clients can use this to check if their local cache is still valid.
If the server version is higher than the client's cached version,
the client should refetch the data.
        """,
        tags=["Sites"],
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["get"], url_path="map-cache-version")
    def map_cache_version(self, request):
        """Get the current map points cache version."""
        from django.core.cache import cache

        CACHE_VERSION_KEY = "map_points_version"
        current_version = cache.get(CACHE_VERSION_KEY, 1)

        return success_response(
            data={"version": current_version},
            meta={"cache_key": CACHE_VERSION_KEY},
        )

    @extend_schema(
        summary="Clear map points cache",
        description="""
Clear the cached map points data.

**Requires staff permissions.**

Use this endpoint after bulk data imports or updates to ensure fresh data
is displayed on the map.

This uses version-based cache invalidation which works with any cache backend
(Redis, Memcached, etc.).
        """,
        tags=["Sites"],
        responses={200: OpenApiTypes.OBJECT},
    )
    @action(detail=False, methods=["post"], url_path="clear-map-cache")
    def clear_map_cache(self, request):
        """Clear all cached map points data by incrementing the cache version."""
        from django.core.cache import cache

        if not request.user.is_staff:
            return error_response(
                errors={"detail": "Staff permission required"},
                status_code=status.HTTP_403_FORBIDDEN,
            )

        CACHE_VERSION_KEY = "map_points_version"

        try:
            # Increment the cache version - this effectively invalidates all cached entries
            # because they'll have the old version in their key
            current_version = cache.get(CACHE_VERSION_KEY, 1)
            new_version = current_version + 1
            cache.set(CACHE_VERSION_KEY, new_version, None)  # No timeout - persist indefinitely

            return success_response(
                data={"cleared": True},
                meta={
                    "method": "version_increment",
                    "previous_version": current_version,
                    "new_version": new_version,
                },
            )
        except Exception as e:
            return error_response(
                errors={"detail": f"Failed to clear cache: {str(e)}"},
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
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
