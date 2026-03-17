# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Filters for Survey in API v1.
"""
from django.db.models import Q
from django_filters import rest_framework as filters

from bims.models.survey import Survey
from bims.models.location_site import LocationSite


class SurveyFilterSet(filters.FilterSet):
    """
    FilterSet for Survey model.
    """

    # Site filters
    site = filters.ModelChoiceFilter(queryset=LocationSite.objects.all())
    site_name = filters.CharFilter(field_name="site__name", lookup_expr="icontains")
    site_code = filters.CharFilter(field_name="site__site_code", lookup_expr="icontains")

    # Date filters
    date = filters.DateFilter()
    date_after = filters.DateFilter(field_name="date", lookup_expr="gte")
    date_before = filters.DateFilter(field_name="date", lookup_expr="lte")
    year = filters.NumberFilter(field_name="date__year")

    # Collector filters
    collector = filters.CharFilter(field_name="collector_string", lookup_expr="icontains")
    collector_user = filters.NumberFilter(field_name="collector_user__id")

    # Owner filter
    owner = filters.NumberFilter(field_name="owner__id")

    # Validation status
    validated = filters.BooleanFilter()

    # UUID filter
    uuid = filters.UUIDFilter()

    # Search filter
    search = filters.CharFilter(method="filter_search")

    class Meta:
        model = Survey
        fields = [
            "site",
            "site_name",
            "site_code",
            "date",
            "date_after",
            "date_before",
            "year",
            "collector",
            "collector_user",
            "owner",
            "validated",
            "uuid",
            "search",
        ]

    def filter_search(self, queryset, name, value):
        """Search across multiple fields."""
        if not value:
            return queryset
        return queryset.filter(
            Q(site__name__icontains=value) | Q(site__site_code__icontains=value) | Q(collector_string__icontains=value)
        )
