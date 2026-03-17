# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Pagination classes for API v1.

Provides standardized pagination with consistent response format.
"""
from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class that wraps results in a consistent format.

    Response format:
    {
        "success": true,
        "data": [...],
        "meta": {
            "count": 100,
            "page": 1,
            "page_size": 20,
            "total_pages": 5,
            "next": "http://api/v1/resource/?page=2",
            "previous": null
        },
        "errors": null
    }
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 1000

    def get_paginated_response(self, data):
        return Response(
            OrderedDict(
                [
                    ("success", True),
                    ("data", data),
                    (
                        "meta",
                        OrderedDict(
                            [
                                ("count", self.page.paginator.count),
                                ("page", self.page.number),
                                ("page_size", self.get_page_size(self.request)),
                                ("total_pages", self.page.paginator.num_pages),
                                ("next", self.get_next_link()),
                                ("previous", self.get_previous_link()),
                            ]
                        ),
                    ),
                    ("errors", None),
                ]
            )
        )

    def get_paginated_response_schema(self, schema):
        """Return OpenAPI schema for paginated responses."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "example": True},
                "data": schema,
                "meta": {
                    "type": "object",
                    "properties": {
                        "count": {
                            "type": "integer",
                            "example": 100,
                            "description": "Total number of items",
                        },
                        "page": {
                            "type": "integer",
                            "example": 1,
                            "description": "Current page number",
                        },
                        "page_size": {
                            "type": "integer",
                            "example": 20,
                            "description": "Number of items per page",
                        },
                        "total_pages": {
                            "type": "integer",
                            "example": 5,
                            "description": "Total number of pages",
                        },
                        "next": {
                            "type": "string",
                            "nullable": True,
                            "description": "URL for next page",
                        },
                        "previous": {
                            "type": "string",
                            "nullable": True,
                            "description": "URL for previous page",
                        },
                    },
                },
                "errors": {"nullable": True, "example": None},
            },
        }


class LargeResultsSetPagination(StandardResultsSetPagination):
    """Pagination for endpoints that may return large datasets."""

    page_size = 100
    max_page_size = 5000


class SmallResultsSetPagination(StandardResultsSetPagination):
    """Pagination for endpoints with small result sets (e.g., autocomplete)."""

    page_size = 10
    max_page_size = 50
