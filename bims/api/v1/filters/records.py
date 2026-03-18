# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Filters for BiologicalCollectionRecord in API v1.
"""
from django.contrib.gis.geos import Polygon
from django.db.models import Q
from django_filters import rest_framework as filters

from bims.models.biological_collection_record import BiologicalCollectionRecord
from bims.models.location_site import LocationSite
from bims.models.taxonomy import Taxonomy
from bims.models.taxon_group import TaxonGroup
from bims.models.survey import Survey
from bims.models.iucn_status import IUCNStatus


class BoundingBoxFilter(filters.CharFilter):
    """
    Filter for bounding box queries on site geometry.

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
                Q(site__geometry_point__intersects=bbox_polygon)
                | Q(site__geometry_line__intersects=bbox_polygon)
                | Q(site__geometry_polygon__intersects=bbox_polygon)
                | Q(site__geometry_multipolygon__intersects=bbox_polygon)
            )
        except (ValueError, TypeError):
            return qs


class BiologicalCollectionRecordFilterSet(filters.FilterSet):
    """
    FilterSet for BiologicalCollectionRecord model.

    Provides comprehensive filtering for biological records.
    """

    # Site filters
    site = filters.ModelChoiceFilter(queryset=LocationSite.objects.all())
    site_name = filters.CharFilter(field_name="site__name", lookup_expr="icontains")
    site_code = filters.CharFilter(field_name="site__site_code", lookup_expr="icontains")

    # Taxonomy filters
    taxonomy = filters.ModelChoiceFilter(queryset=Taxonomy.objects.all())
    taxon_name = filters.CharFilter(method="filter_taxon_name")
    taxon_rank = filters.CharFilter(field_name="taxonomy__rank", lookup_expr="iexact")
    taxon_group = filters.ModelChoiceFilter(
        field_name="module_group",
        queryset=TaxonGroup.objects.all(),
    )

    # Conservation status filters
    iucn_status = filters.ModelChoiceFilter(
        field_name="taxonomy__iucn_status",
        queryset=IUCNStatus.objects.all(),
    )
    iucn_category = filters.CharFilter(
        field_name="taxonomy__iucn_status__category",
        lookup_expr="iexact",
    )

    # Endemism filters
    endemism = filters.CharFilter(
        field_name="taxonomy__endemism__name",
        lookup_expr="iexact",
    )

    # Survey filters
    survey = filters.ModelChoiceFilter(queryset=Survey.objects.all())

    # Date filters
    collection_date = filters.DateFilter()
    collection_date_after = filters.DateFilter(field_name="collection_date", lookup_expr="gte")
    collection_date_before = filters.DateFilter(field_name="collection_date", lookup_expr="lte")
    year = filters.NumberFilter(field_name="collection_date__year")
    year_from = filters.NumberFilter(field_name="collection_date__year", lookup_expr="gte")
    year_to = filters.NumberFilter(field_name="collection_date__year", lookup_expr="lte")

    # Collector filters
    collector = filters.CharFilter(lookup_expr="icontains")
    collector_user = filters.NumberFilter(field_name="collector_user__id")

    # Validation status
    validated = filters.BooleanFilter()
    present = filters.BooleanFilter()

    # Spatial filters
    bbox = BoundingBoxFilter()

    # Source reference filters
    source_reference = filters.NumberFilter(field_name="source_reference__id")
    source_collection = filters.CharFilter(lookup_expr="icontains")

    # Ecosystem filters
    ecosystem_type = filters.CharFilter(field_name="site__ecosystem_type", lookup_expr="iexact")

    # UUID filter
    uuid = filters.UUIDFilter()

    # Search filter
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = BiologicalCollectionRecord
        fields = [
            "site",
            "site_name",
            "site_code",
            "taxonomy",
            "taxon_name",
            "taxon_rank",
            "taxon_group",
            "iucn_status",
            "iucn_category",
            "endemism",
            "survey",
            "collection_date",
            "collection_date_after",
            "collection_date_before",
            "year",
            "year_from",
            "year_to",
            "collector",
            "collector_user",
            "validated",
            "present",
            "bbox",
            "source_reference",
            "source_collection",
            "ecosystem_type",
            "uuid",
            "search",
        ]

    def filter_taxon_name(self, queryset, name, value):
        """Filter by taxon name (scientific or canonical)."""
        if not value:
            return queryset
        return queryset.filter(
            Q(taxonomy__scientific_name__icontains=value)
            | Q(taxonomy__canonical_name__icontains=value)
            | Q(original_species_name__icontains=value)
        )

    def filter_search(self, queryset, name, value):
        """Search across multiple fields."""
        if not value:
            return queryset
        return queryset.filter(
            Q(site__name__icontains=value)
            | Q(site__site_code__icontains=value)
            | Q(taxonomy__scientific_name__icontains=value)
            | Q(taxonomy__canonical_name__icontains=value)
            | Q(original_species_name__icontains=value)
            | Q(collector__icontains=value)
            | Q(notes__icontains=value)
        )
