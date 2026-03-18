# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for autocomplete endpoints in API v1.

Made with love by Kartoza | https://kartoza.com
"""
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from bims.api.v1.responses import success_response
from bims.models import BiologicalCollectionRecord, Taxonomy, LocationSite


User = get_user_model()


class AutocompleteViewSet(viewsets.ViewSet):
    """
    ViewSet for autocomplete/typeahead endpoints.

    Endpoints:
    - GET /api/v1/autocomplete/collectors/ - Autocomplete collectors
    - GET /api/v1/autocomplete/taxa/ - Autocomplete taxa
    - GET /api/v1/autocomplete/sites/ - Autocomplete sites
    """

    permission_classes = [AllowAny]

    @action(detail=False, methods=["get"])
    def collectors(self, request):
        """
        Autocomplete for collector names.

        Query params:
        - q: Search query (required, min 2 chars)
        - limit: Max results (default 10)
        """
        query = request.query_params.get("q", "").strip()
        limit = int(request.query_params.get("limit", 10))

        if len(query) < 2:
            return success_response(data=[])

        # Search in collector field and collector_user
        collectors = (
            BiologicalCollectionRecord.objects
            .filter(
                Q(collector__icontains=query) |
                Q(collector_user__first_name__icontains=query) |
                Q(collector_user__last_name__icontains=query)
            )
            .values("collector")
            .annotate(count=Count("id"))
            .order_by("-count")[:limit]
        )

        data = [
            {"id": idx + 1, "name": c["collector"]}
            for idx, c in enumerate(collectors)
            if c["collector"]
        ]

        return success_response(data=data)

    @action(detail=False, methods=["get"])
    def taxa(self, request):
        """
        Autocomplete for taxa names.

        Query params:
        - q: Search query (required, min 2 chars)
        - limit: Max results (default 10)
        - rank: Filter by taxonomic rank
        """
        query = request.query_params.get("q", "").strip()
        limit = int(request.query_params.get("limit", 10))
        rank = request.query_params.get("rank")

        if len(query) < 2:
            return success_response(data=[])

        queryset = Taxonomy.objects.filter(
            Q(canonical_name__icontains=query) |
            Q(scientific_name__icontains=query)
        )

        if rank:
            queryset = queryset.filter(rank__iexact=rank)

        taxa = queryset.values("id", "canonical_name", "scientific_name", "rank")[:limit]

        data = [
            {
                "id": t["id"],
                "name": t["canonical_name"] or t["scientific_name"],
                "scientific_name": t["scientific_name"],
                "rank": t["rank"],
            }
            for t in taxa
        ]

        return success_response(data=data)

    @action(detail=False, methods=["get"])
    def sites(self, request):
        """
        Autocomplete for site names/codes.

        Query params:
        - q: Search query (required, min 2 chars)
        - limit: Max results (default 10)
        """
        query = request.query_params.get("q", "").strip()
        limit = int(request.query_params.get("limit", 10))

        if len(query) < 2:
            return success_response(data=[])

        sites = LocationSite.objects.filter(
            Q(site_code__icontains=query) |
            Q(name__icontains=query) |
            Q(site_description__icontains=query)
        ).values("id", "site_code", "name")[:limit]

        data = [
            {
                "id": s["id"],
                "code": s["site_code"],
                "name": s["name"] or s["site_code"],
            }
            for s in sites
        ]

        return success_response(data=data)
