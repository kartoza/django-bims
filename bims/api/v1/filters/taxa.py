# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Filters for Taxonomy in API v1.
"""
from django.db.models import Q
from django_filters import rest_framework as filters

from bims.models.taxonomy import Taxonomy
from bims.models.taxon_group import TaxonGroup
from bims.models.iucn_status import IUCNStatus
from bims.models.endemism import Endemism


class TaxonomyFilterSet(filters.FilterSet):
    """
    FilterSet for Taxonomy model.

    Provides comprehensive filtering for taxonomy records.
    """

    # Name filters
    scientific_name = filters.CharFilter(lookup_expr="icontains")
    canonical_name = filters.CharFilter(lookup_expr="icontains")
    name = filters.CharFilter(method="filter_name")

    # Rank filter
    rank = filters.CharFilter(lookup_expr="iexact")
    rank_in = filters.BaseInFilter(field_name="rank")

    # Taxonomic status
    taxonomic_status = filters.CharFilter(lookup_expr="iexact")

    # Hierarchy filters
    parent = filters.ModelChoiceFilter(queryset=Taxonomy.objects.all())
    has_parent = filters.BooleanFilter(field_name="parent", lookup_expr="isnull", exclude=True)

    # Taxon group filter - filter by the related taxon group's ID
    # Note: the through model field is 'taxongroup' (no underscore)
    taxon_group = filters.NumberFilter(
        field_name="taxongrouptaxonomy__taxongroup__id",
    )

    # Conservation status filters
    iucn_status = filters.ModelChoiceFilter(queryset=IUCNStatus.objects.all())
    iucn_category = filters.CharFilter(field_name="iucn_status__category", lookup_expr="iexact")
    national_status = filters.ModelChoiceFilter(
        field_name="national_conservation_status",
        queryset=IUCNStatus.objects.all(),
    )

    # Endemism filter
    endemism = filters.ModelChoiceFilter(queryset=Endemism.objects.all())
    endemism_name = filters.CharFilter(field_name="endemism__name", lookup_expr="iexact")

    # Origin filter
    origin = filters.CharFilter(lookup_expr="iexact")

    # External ID filters
    gbif_key = filters.NumberFilter()
    has_gbif_key = filters.BooleanFilter(field_name="gbif_key", lookup_expr="isnull", exclude=True)

    # Validation filters
    validated = filters.BooleanFilter()
    verified = filters.BooleanFilter()

    # Tag filters
    tag = filters.CharFilter(method="filter_tag")

    # Search filter
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Taxonomy
        fields = [
            "scientific_name",
            "canonical_name",
            "name",
            "rank",
            "rank_in",
            "taxonomic_status",
            "parent",
            "has_parent",
            "taxon_group",
            "iucn_status",
            "iucn_category",
            "national_status",
            "endemism",
            "endemism_name",
            "origin",
            "gbif_key",
            "has_gbif_key",
            "validated",
            "verified",
            "tag",
            "search",
        ]

    def filter_name(self, queryset, name, value):
        """Filter by scientific or canonical name."""
        if not value:
            return queryset
        return queryset.filter(Q(scientific_name__icontains=value) | Q(canonical_name__icontains=value))

    def filter_tag(self, queryset, name, value):
        """Filter by tag name."""
        if not value:
            return queryset
        return queryset.filter(tags__name__icontains=value)

    def filter_search(self, queryset, name, value):
        """Search across multiple fields."""
        if not value:
            return queryset
        return queryset.filter(
            Q(scientific_name__icontains=value)
            | Q(canonical_name__icontains=value)
            | Q(vernacular_names__name__icontains=value)
        ).distinct()
