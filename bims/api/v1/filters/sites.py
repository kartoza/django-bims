# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Filters for LocationSite in API v1.
"""
from django.contrib.gis.geos import Polygon
from django.db.models import Q
from django_filters import rest_framework as filters

from bims.models.location_site import LocationSite
from bims.models.location_type import LocationType


class BoundingBoxFilter(filters.CharFilter):
    """
    Filter for bounding box queries.

    Accepts bbox as comma-separated coordinates: west,south,east,north
    """

    def filter(self, qs, value):
        if not value:
            return qs

        try:
            coords = [float(c) for c in value.split(",")]
            if len(coords) != 4:
                return qs

            west, south, east, north = coords
            bbox_polygon = Polygon.from_bbox((west, south, east, north))

            return qs.filter(
                Q(geometry_point__intersects=bbox_polygon)
                | Q(geometry_line__intersects=bbox_polygon)
                | Q(geometry_polygon__intersects=bbox_polygon)
                | Q(geometry_multipolygon__intersects=bbox_polygon)
            )
        except (ValueError, TypeError):
            return qs


class LocationSiteFilterSet(filters.FilterSet):
    """
    FilterSet for LocationSite model.

    Provides comprehensive filtering for location sites.
    """

    # Basic filters
    name = filters.CharFilter(lookup_expr="icontains")
    site_code = filters.CharFilter(lookup_expr="icontains")
    site_description = filters.CharFilter(lookup_expr="icontains")
    uuid = filters.UUIDFilter()

    # Foreign key filters
    location_type = filters.ModelChoiceFilter(queryset=LocationType.objects.all())
    location_type_name = filters.CharFilter(field_name="location_type__name", lookup_expr="icontains")

    # Ecosystem filters
    ecosystem_type = filters.CharFilter(lookup_expr="exact")

    # River filters
    river_name = filters.CharFilter(method="filter_river_name")

    # Owner filters
    owner = filters.NumberFilter(field_name="owner__id")
    owner_username = filters.CharFilter(field_name="owner__username", lookup_expr="icontains")

    # Validation status
    validated = filters.BooleanFilter()

    # Spatial filters
    bbox = BoundingBoxFilter()

    # Date filters
    created_after = filters.DateFilter(field_name="created", lookup_expr="gte")
    created_before = filters.DateFilter(field_name="created", lookup_expr="lte")
    modified_after = filters.DateFilter(field_name="modified", lookup_expr="gte")
    modified_before = filters.DateFilter(field_name="modified", lookup_expr="lte")

    # Search filter (searches multiple fields)
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = LocationSite
        fields = [
            "name",
            "site_code",
            "site_description",
            "uuid",
            "location_type",
            "location_type_name",
            "ecosystem_type",
            "river_name",
            "owner",
            "owner_username",
            "validated",
            "bbox",
            "created_after",
            "created_before",
            "modified_after",
            "modified_before",
            "search",
        ]

    def filter_river_name(self, queryset, name, value):
        """Filter by river name (checks both legacy and river FK)."""
        if not value:
            return queryset
        return queryset.filter(Q(legacy_river_name__icontains=value) | Q(river__name__icontains=value))

    def filter_search(self, queryset, name, value):
        """Search across multiple fields."""
        if not value:
            return queryset
        return queryset.filter(
            Q(name__icontains=value)
            | Q(site_code__icontains=value)
            | Q(site_description__icontains=value)
            | Q(legacy_river_name__icontains=value)
            | Q(river__name__icontains=value)
        )
