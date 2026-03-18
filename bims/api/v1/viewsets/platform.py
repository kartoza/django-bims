# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for platform-wide statistics in API v1.

Made with love by Kartoza | https://kartoza.com
"""
from django.contrib.auth import get_user_model
from django.db.models import Count
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny

from bims.api.v1.responses import success_response
from bims.models import LocationSite, BiologicalCollectionRecord, Taxonomy


User = get_user_model()


class PlatformViewSet(viewsets.ViewSet):
    """
    ViewSet for platform-wide statistics and information.

    Endpoints:
    - GET /api/v1/platform/stats/ - Get platform statistics for landing page
    """

    permission_classes = [AllowAny]

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """
        Get platform-wide statistics for the landing page.

        Returns counts for sites, records, taxa, and contributors.
        """
        # Count location sites
        total_sites = LocationSite.objects.count()

        # Count biological records (occurrences)
        total_records = BiologicalCollectionRecord.objects.count()

        # Count unique taxa
        total_taxa = Taxonomy.objects.filter(
            biologicalcollectionrecord__isnull=False
        ).distinct().count()

        # Count contributors (users who have uploaded data)
        total_contributors = User.objects.filter(
            is_active=True
        ).annotate(
            record_count=Count("biologicalcollectionrecord")
        ).filter(
            record_count__gt=0
        ).count()

        # If no contributors found via records, count users with collector entries
        if total_contributors == 0:
            total_contributors = User.objects.filter(is_active=True).count()

        return success_response(
            data={
                "total_sites": total_sites,
                "total_records": total_records,
                "total_taxa": total_taxa,
                "total_contributors": total_contributors,
            }
        )
