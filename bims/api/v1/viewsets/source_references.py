# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for SourceReference in API v1.
"""
from django.db.models import Count
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from bims.api.v1.pagination import LargeResultsSetPagination
from bims.api.v1.responses import success_response
from bims.api.v1.serializers.source_references import (
    SourceReferenceDetailSerializer,
    SourceReferenceSerializer,
)
from bims.api.v1.viewsets.base import ReadOnlyStandardViewSet
from bims.models.source_reference import SourceReference


class SourceReferenceViewSet(ReadOnlyStandardViewSet):
    """
    ViewSet for SourceReference read operations.

    Endpoints:
    - GET /api/v1/source-references/ - List source references
    - GET /api/v1/source-references/{id}/ - Get source reference detail
    - GET /api/v1/source-references/{id}/records/ - Get records for reference
    """

    queryset = SourceReference.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LargeResultsSetPagination

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "retrieve":
            return SourceReferenceDetailSerializer
        return SourceReferenceSerializer

    def get_queryset(self):
        """Optimize queryset with record count."""
        queryset = super().get_queryset()
        return queryset.annotate(record_count=Count("biologicalcollectionrecord")).order_by("-record_count")

    @action(detail=True, methods=["get"])
    def records(self, request, pk=None):
        """
        Get biological records using this source reference.
        """
        reference = self.get_object()

        from bims.api.v1.serializers.records import BiologicalCollectionRecordListSerializer

        records = reference.biologicalcollectionrecord_set.select_related("site", "taxonomy").all()

        page = self.paginate_queryset(records)
        if page is not None:
            serializer = BiologicalCollectionRecordListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BiologicalCollectionRecordListSerializer(records, many=True)
        return success_response(data=serializer.data, meta={"count": records.count()})

    @action(detail=False, methods=["get"])
    def by_type(self, request):
        """
        Get source references grouped by type.
        """
        queryset = self.get_queryset()

        # Group by reference type
        type_counts = (
            queryset.values("reference_type")
            .annotate(count=Count("id"), total_records=Count("biologicalcollectionrecord"))
            .order_by("-count")
        )

        return success_response(
            data=list(type_counts),
            meta={"total_types": len(type_counts)},
        )
