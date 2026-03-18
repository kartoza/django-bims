# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Base ViewSet classes for API v1.

Provides standardized ViewSet behavior with consistent response formatting.
"""
from rest_framework import status, viewsets
from rest_framework.response import Response

from bims.api.v1.pagination import StandardResultsSetPagination
from bims.api.v1.responses import (
    created_response,
    error_response,
    no_content_response,
    not_found_response,
    success_response,
)


class StandardModelViewSet(viewsets.ModelViewSet):
    """
    A ModelViewSet that returns standardized responses.

    All responses follow the format:
    {
        "success": true/false,
        "data": {...} or [...],
        "meta": {...} or null,
        "errors": {...} or null
    }
    """

    pagination_class = StandardResultsSetPagination

    def retrieve(self, request, *args, **kwargs):
        """Get a single resource with standardized response."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return success_response(data=serializer.data)
        except Exception:
            return not_found_response()

    def create(self, request, *args, **kwargs):
        """Create a resource with standardized response."""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            self.perform_create(serializer)
            return created_response(data=serializer.data)
        return error_response(
            errors=serializer.errors,
            message="Validation failed",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def update(self, request, *args, **kwargs):
        """Update a resource with standardized response."""
        partial = kwargs.pop("partial", False)
        try:
            instance = self.get_object()
        except Exception:
            return not_found_response()

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        if serializer.is_valid():
            self.perform_update(serializer)
            return success_response(data=serializer.data)
        return error_response(
            errors=serializer.errors,
            message="Validation failed",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    def destroy(self, request, *args, **kwargs):
        """Delete a resource with standardized response."""
        try:
            instance = self.get_object()
            self.perform_destroy(instance)
            return no_content_response()
        except Exception:
            return not_found_response()

    def list(self, request, *args, **kwargs):
        """
        List resources with standardized pagination.

        Note: Pagination is handled by StandardResultsSetPagination
        which already formats the response correctly.
        """
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        # Unpaginated response
        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)


class ReadOnlyStandardViewSet(viewsets.ReadOnlyModelViewSet):
    """
    A read-only ViewSet with standardized responses.

    Only provides list and retrieve actions.
    """

    pagination_class = StandardResultsSetPagination

    def retrieve(self, request, *args, **kwargs):
        """Get a single resource with standardized response."""
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return success_response(data=serializer.data)
        except Exception:
            return not_found_response()

    def list(self, request, *args, **kwargs):
        """List resources with standardized pagination."""
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return success_response(data=serializer.data)
