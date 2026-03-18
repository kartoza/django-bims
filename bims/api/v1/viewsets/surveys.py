# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSet for Survey in API v1.
"""
from django.db.models import Count
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from bims.api.v1.filters.surveys import SurveyFilterSet
from bims.api.v1.pagination import LargeResultsSetPagination
from bims.api.v1.permissions import CanValidate, IsOwnerOrReadOnly
from bims.api.v1.responses import (
    error_response,
    success_response,
    validation_error_response,
)
from bims.api.v1.serializers.surveys import (
    SurveyCreateSerializer,
    SurveyDetailSerializer,
    SurveyListSerializer,
)
from bims.api.v1.viewsets.base import StandardModelViewSet
from bims.models.survey import Survey


class SurveyViewSet(StandardModelViewSet):
    """
    ViewSet for Survey CRUD operations.

    Endpoints:
    - GET /api/v1/surveys/ - List surveys
    - POST /api/v1/surveys/ - Create survey
    - GET /api/v1/surveys/{id}/ - Get survey detail
    - PUT /api/v1/surveys/{id}/ - Update survey
    - DELETE /api/v1/surveys/{id}/ - Delete survey
    - POST /api/v1/surveys/bulk-validate/ - Bulk validate surveys
    - POST /api/v1/surveys/bulk-reject/ - Bulk reject surveys
    """

    queryset = Survey.objects.select_related("site", "collector_user", "owner").all()
    filterset_class = SurveyFilterSet
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrReadOnly]
    pagination_class = LargeResultsSetPagination

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return SurveyListSerializer
        elif self.action in ["create", "update", "partial_update"]:
            return SurveyCreateSerializer
        return SurveyDetailSerializer

    def get_queryset(self):
        """Optimize queryset with record count."""
        queryset = super().get_queryset()
        return queryset.annotate(record_count=Count("biological_collection_record")).order_by("-date", "-created")

    @action(detail=True, methods=["post"], permission_classes=[CanValidate])
    def validate(self, request, pk=None):
        """
        Validate a survey.
        """
        try:
            survey = self.get_object()
        except Survey.DoesNotExist:
            return error_response(
                errors={"detail": "Survey not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        if survey.validated:
            return error_response(
                errors={"detail": "Survey is already validated"},
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        survey.validated = True
        survey.save()

        # Also validate all records in this survey
        survey.biological_collection_record.update(validated=True)

        serializer = SurveyDetailSerializer(survey)
        return success_response(data=serializer.data, meta={"validated": True})

    @action(detail=True, methods=["post"], permission_classes=[CanValidate])
    def reject(self, request, pk=None):
        """
        Reject a survey.
        """
        try:
            survey = self.get_object()
        except Survey.DoesNotExist:
            return error_response(
                errors={"detail": "Survey not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        reason = request.data.get("reason", "")

        survey.validated = False
        survey.rejected = True
        survey.save()

        serializer = SurveyDetailSerializer(survey)
        return success_response(data=serializer.data, meta={"rejected": True, "reason": reason})

    @action(detail=False, methods=["post"], permission_classes=[CanValidate])
    def bulk_validate(self, request):
        """
        Bulk validate multiple surveys.

        Body:
        - survey_ids: List of survey IDs to validate
        """
        survey_ids = request.data.get("survey_ids", [])

        if not survey_ids:
            return validation_error_response({"detail": "survey_ids is required"})

        surveys = Survey.objects.filter(id__in=survey_ids, validated=False)
        count = surveys.count()

        # Validate surveys
        surveys.update(validated=True)

        # Validate all records in these surveys
        from bims.models.biological_collection_record import BiologicalCollectionRecord

        BiologicalCollectionRecord.objects.filter(survey_id__in=survey_ids).update(validated=True)

        return success_response(
            data={"validated_count": count},
            meta={"survey_ids": survey_ids},
        )

    @action(detail=False, methods=["post"], permission_classes=[CanValidate])
    def bulk_reject(self, request):
        """
        Bulk reject multiple surveys.

        Body:
        - survey_ids: List of survey IDs to reject
        - reason: Rejection reason (optional)
        """
        survey_ids = request.data.get("survey_ids", [])
        reason = request.data.get("reason", "")

        if not survey_ids:
            return validation_error_response({"detail": "survey_ids is required"})

        surveys = Survey.objects.filter(id__in=survey_ids)
        count = surveys.count()

        # Reject surveys
        surveys.update(validated=False, rejected=True)

        return success_response(
            data={"rejected_count": count},
            meta={"survey_ids": survey_ids, "reason": reason},
        )

    @action(detail=True, methods=["get"])
    def records(self, request, pk=None):
        """
        Get all biological records for a survey.
        """
        try:
            survey = self.get_object()
        except Survey.DoesNotExist:
            return error_response(
                errors={"detail": "Survey not found"},
                status_code=status.HTTP_404_NOT_FOUND,
            )

        from bims.api.v1.serializers.records import BiologicalCollectionRecordListSerializer

        records = survey.biological_collection_record.select_related("taxonomy", "site").all()

        page = self.paginate_queryset(records)
        if page is not None:
            serializer = BiologicalCollectionRecordListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = BiologicalCollectionRecordListSerializer(records, many=True)
        return success_response(data=serializer.data, meta={"count": records.count()})
