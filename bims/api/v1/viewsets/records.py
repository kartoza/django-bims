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
        return queryset.order_by("-collection_date", "-id")

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

    @action(detail=False, methods=["post"], permission_classes=[CanValidate], url_path="bulk-validate")
    def bulk_validate(self, request):
        """
        Bulk validate multiple biological collection records.

        Body:
        - ids: List of record IDs to validate
        """
        ids = request.data.get("ids", [])

        if not ids:
            from bims.api.v1.responses import validation_error_response
            return validation_error_response({"detail": "ids is required"})

        records = BiologicalCollectionRecord.objects.filter(id__in=ids, validated=False)
        count = records.count()

        records.update(validated=True, rejected=False)

        return success_response(
            data={"validated_count": count},
            meta={"record_ids": ids},
        )

    @action(detail=False, methods=["post"], permission_classes=[CanValidate], url_path="bulk-reject")
    def bulk_reject(self, request):
        """
        Bulk reject multiple biological collection records.

        Body:
        - ids: List of record IDs to reject
        - reason: Rejection reason (optional)
        """
        ids = request.data.get("ids", [])
        reason = request.data.get("reason", "")

        if not ids:
            from bims.api.v1.responses import validation_error_response
            return validation_error_response({"detail": "ids is required"})

        records = BiologicalCollectionRecord.objects.filter(id__in=ids)
        count = records.count()

        records.update(validated=False, rejected=True)

        return success_response(
            data={"rejected_count": count},
            meta={"record_ids": ids, "reason": reason},
        )

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

    @action(detail=False, methods=["get"], url_path="filter-summary")
    def filter_summary(self, request):
        """
        Get summary statistics for the current filter including biodiversity breakdown.

        Returns:
        - Total sites, occurrences, taxa
        - Biodiversity data grouped by taxon module (Fish, Invertebrates, Algae etc.)
        - Origin, endemism, and conservation status breakdowns per module
        """
        from django.db.models import F, Value, Case, When, CharField
        from bims.models import TaxonGroup
        from bims.enums import TaxonomicGroupCategory

        queryset = self.filter_queryset(self.get_queryset())

        # Get overall summary
        total_occurrences = queryset.count()
        total_sites = queryset.values("site").distinct().count()
        total_taxa = queryset.values("taxonomy").distinct().count()

        # Date range
        date_range = queryset.aggregate(
            earliest=Min("collection_date"),
            latest=Max("collection_date"),
        )

        # Get biodiversity breakdown by module
        modules = TaxonGroup.objects.filter(
            category=TaxonomicGroupCategory.SPECIES_MODULE.name
        ).order_by('display_order')

        biodiversity_data = {}

        for module in modules:
            module_records = queryset.filter(module_group=module)
            module_count = module_records.count()

            if module_count == 0:
                continue

            # Get origin breakdown
            origin_counts = list(
                module_records.annotate(
                    origin_name=Case(
                        When(taxonomy__origin__isnull=True, then=Value('Unknown')),
                        default=F('taxonomy__origin__category'),
                        output_field=CharField()
                    )
                ).values('origin_name').annotate(count=Count('id')).order_by('-count')
            )

            # Get endemism breakdown
            endemism_counts = list(
                module_records.annotate(
                    endemism_name=Case(
                        When(taxonomy__endemism__isnull=False, then=F('taxonomy__endemism__name')),
                        default=Value('Unknown'),
                        output_field=CharField()
                    )
                ).values('endemism_name').annotate(count=Count('id')).order_by('-count')
            )

            # Get conservation status breakdown
            cons_status_counts = list(
                module_records.annotate(
                    iucn_category=Case(
                        When(
                            taxonomy__iucn_status__isnull=False,
                            then=F('taxonomy__iucn_status__category')
                        ),
                        default=Value('NE'),
                        output_field=CharField()
                    )
                ).values('iucn_category').annotate(count=Count('id')).order_by('-count')
            )

            # Get module icon URL
            icon_url = None
            if module.logo:
                icon_url = module.logo.name

            biodiversity_data[module.name] = {
                "module_id": module.id,
                "icon": icon_url,
                "occurrences": module_count,
                "number_of_sites": module_records.values("site").distinct().count(),
                "number_of_taxa": module_records.values("taxonomy").distinct().count(),
                "origin": [{"name": o["origin_name"], "count": o["count"]} for o in origin_counts],
                "endemism": [{"name": e["endemism_name"], "count": e["count"]} for e in endemism_counts],
                "cons_status": [{"name": c["iucn_category"], "count": c["count"]} for c in cons_status_counts],
            }

        # Get species list (top 20 by occurrence count)
        species_list = list(
            queryset.values(
                "taxonomy__id",
                "taxonomy__canonical_name",
                "taxonomy__rank",
            )
            .annotate(
                occurrence_count=Count("id"),
                site_count=Count("site", distinct=True),
            )
            .order_by("-occurrence_count")[:20]
        )

        return success_response(
            data={
                "total_sites": total_sites,
                "total_occurrences": total_occurrences,
                "total_taxa": total_taxa,
                "date_range": {
                    "earliest": date_range["earliest"].isoformat() if date_range["earliest"] else None,
                    "latest": date_range["latest"].isoformat() if date_range["latest"] else None,
                },
                "biodiversity_data": biodiversity_data,
                "species_list": [
                    {
                        "id": s["taxonomy__id"],
                        "name": s["taxonomy__canonical_name"],
                        "rank": s["taxonomy__rank"],
                        "occurrences": s["occurrence_count"],
                        "sites": s["site_count"],
                    }
                    for s in species_list
                ],
            },
            meta={
                "module_count": len(biodiversity_data),
            },
        )
