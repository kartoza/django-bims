# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for BiologicalCollectionRecord in API v1.
"""
from django.db.models import Count, Min, Max
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from bims.api.v1.filters.records import BiologicalCollectionRecordFilterSet
from bims.api.v1.pagination import LargeResultsSetPagination
from bims.api.v1.permissions import CanEditBiologicalRecord, CanValidate
from bims.api.v1.responses import (
    error_response,
    success_response,
)
from bims.api.v1.serializers.records import (
    BiologicalCollectionRecordCreateSerializer,
    BiologicalCollectionRecordDetailSerializer,
    BiologicalCollectionRecordListSerializer,
    BiologicalCollectionRecordSummarySerializer,
)
from bims.api.v1.viewsets.base import StandardModelViewSet
from bims.models.biological_collection_record import BiologicalCollectionRecord


class BiologicalCollectionRecordViewSet(StandardModelViewSet):
    """
    ViewSet for BiologicalCollectionRecord CRUD operations.

    Endpoints:
    - GET /api/v1/records/ - List records
    - POST /api/v1/records/ - Create record
    - GET /api/v1/records/{id}/ - Get record detail
    - PUT /api/v1/records/{id}/ - Update record
    - DELETE /api/v1/records/{id}/ - Delete record
    - GET /api/v1/records/summary/ - Get summary statistics
    - GET /api/v1/records/search/ - Advanced search
    - POST /api/v1/records/{id}/validate/ - Validate record
    """

    queryset = BiologicalCollectionRecord.objects.select_related(
        "site",
        "taxonomy",
        "survey",
        "source_reference",
        "collector_user",
        "sampling_method",
        "biotope",
        "specific_biotope",
        "substratum",
    ).all()
    filterset_class = BiologicalCollectionRecordFilterSet
    permission_classes = [IsAuthenticatedOrReadOnly, CanEditBiologicalRecord]
    pagination_class = LargeResultsSetPagination

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return BiologicalCollectionRecordListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return BiologicalCollectionRecordCreateSerializer
        return BiologicalCollectionRecordDetailSerializer

    def get_queryset(self):
        """Optimize queryset based on action."""
        queryset = super().get_queryset()

        # Order by collection date descending by default
        return queryset.order_by("-collection_date", "-created")

    @action(detail=False, methods=["get"])
    def summary(self, request):
        """
        Get summary statistics for biological collection records.

        Returns counts and aggregated data.
        """
        queryset = self.filter_queryset(self.get_queryset())

        total = queryset.count()
        validated = queryset.filter(validated=True).count()
        pending = total - validated
        species_count = queryset.values("taxonomy").distinct().count()
        site_count = queryset.values("site").distinct().count()

        date_range = queryset.aggregate(
            earliest=Min("collection_date"),
            latest=Max("collection_date"),
        )

        data = {
            "total_records": total,
            "validated_records": validated,
            "pending_records": pending,
            "species_count": species_count,
            "site_count": site_count,
            "date_range": {
                "earliest": date_range["earliest"].isoformat() if date_range["earliest"] else None,
                "latest": date_range["latest"].isoformat() if date_range["latest"] else None,
            },
        }

        serializer = BiologicalCollectionRecordSummarySerializer(data)
        return success_response(data=serializer.data)

    @action(detail=False, methods=["get"])
    def search(self, request):
        """
        Advanced search for biological records.

        This endpoint supports all filter parameters and provides
        optimized search functionality.
        """
        queryset = self.filter_queryset(self.get_queryset())

        # Get optional grouping parameter
        group_by = request.query_params.get("group_by")

        if group_by == "taxon":
            # Group results by taxonomy
            grouped = (
                queryset.values("taxonomy__id", "taxonomy__canonical_name", "taxonomy__scientific_name")
                .annotate(count=Count("id"))
                .order_by("-count")
            )
            return success_response(
                data=list(grouped),
                meta={"grouped_by": "taxon", "total_groups": len(grouped)},
            )

        elif group_by == "site":
            # Group results by site
            grouped = (
                queryset.values("site__id", "site__name", "site__site_code")
                .annotate(count=Count("id"))
                .order_by("-count")
            )
            return success_response(
                data=list(grouped),
                meta={"grouped_by": "site", "total_groups": len(grouped)},
            )

        elif group_by == "year":
            # Group results by year
            grouped = (
                queryset.values("collection_date__year").annotate(count=Count("id")).order_by("-collection_date__year")
            )
            return success_response(
                data=[{"year": g["collection_date__year"], "count": g["count"]} for g in grouped],
                meta={"grouped_by": "year", "total_groups": len(grouped)},
            )

        # Default: return paginated list
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = BiologicalCollectionRecordListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BiologicalCollectionRecordListSerializer(queryset, many=True)
        return success_response(data=serializer.data)

    @action(detail=True, methods=["post"], permission_classes=[CanValidate])
    def validate(self, request, pk=None):
        """
        Validate a biological collection record.

        Requires validator permissions.
        """
        try:
            record = self.get_object()
        except BiologicalCollectionRecord.DoesNotExist:
            return error_response(
                errors={"detail": "Record not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if record.validated:
            return error_response(
                errors={"detail": "Record is already validated"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        record.validated = True
        record.save()

        serializer = BiologicalCollectionRecordDetailSerializer(record)
        return success_response(data=serializer.data, meta={"validated": True})

    @action(detail=True, methods=["post"], permission_classes=[CanValidate])
    def reject(self, request, pk=None):
        """
        Reject a biological collection record.

        Requires validator permissions.
        """
        try:
            record = self.get_object()
        except BiologicalCollectionRecord.DoesNotExist:
            return error_response(
                errors={"detail": "Record not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        reason = request.data.get("reason", "")

        record.validated = False
        record.rejected = True
        if reason:
            record.additional_data = record.additional_data or {}
            record.additional_data["rejection_reason"] = reason
        record.save()

        serializer = BiologicalCollectionRecordDetailSerializer(record)
        return success_response(data=serializer.data, meta={"rejected": True, "reason": reason})

    @action(detail=False, methods=["get"])
    def by_site(self, request):
        """
        Get records grouped by site.

        Query params:
        - site_id: Filter by specific site ID
        """
        site_id = request.query_params.get("site_id")

        if site_id:
            queryset = self.get_queryset().filter(site_id=site_id)
        else:
            queryset = self.filter_queryset(self.get_queryset())

        # Group by site with counts
        sites_with_records = (
            queryset.values("site__id", "site__name", "site__site_code")
            .annotate(
                record_count=Count("id"),
                species_count=Count("taxonomy", distinct=True),
                earliest_date=Min("collection_date"),
                latest_date=Max("collection_date"),
            )
            .order_by("-record_count")
        )

        return success_response(
            data=list(sites_with_records),
            meta={"total_sites": len(sites_with_records)},
        )

    @action(detail=False, methods=["get"])
    def by_taxon(self, request):
        """
        Get records grouped by taxon.

        Query params:
        - taxonomy_id: Filter by specific taxonomy ID
        """
        taxonomy_id = request.query_params.get("taxonomy_id")

        if taxonomy_id:
            queryset = self.get_queryset().filter(taxonomy_id=taxonomy_id)
        else:
            queryset = self.filter_queryset(self.get_queryset())

        # Group by taxonomy with counts
        taxa_with_records = (
            queryset.values(
                "taxonomy__id",
                "taxonomy__canonical_name",
                "taxonomy__scientific_name",
                "taxonomy__rank",
            )
            .annotate(
                record_count=Count("id"),
                site_count=Count("site", distinct=True),
                earliest_date=Min("collection_date"),
                latest_date=Max("collection_date"),
            )
            .order_by("-record_count")
        )

        return success_response(
            data=list(taxa_with_records),
            meta={"total_taxa": len(taxa_with_records)},
        )
