# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Standardized API response helpers for API v1.

Provides consistent response format across all endpoints.
"""
from collections import OrderedDict
from typing import Any

from rest_framework import status
from rest_framework.response import Response


def success_response(
    data: Any = None,
    meta: dict | None = None,
    status_code: int = status.HTTP_200_OK,
) -> Response:
    """
    Create a standardized success response.

    Args:
        data: The response data (can be dict, list, or any serializable value)
        meta: Optional metadata dictionary
        status_code: HTTP status code (default: 200)

    Returns:
        Response object with standardized format
    """
    response_data = OrderedDict(
        [
            ("success", True),
            ("data", data),
            ("meta", meta),
            ("errors", None),
        ]
    )
    return Response(response_data, status=status_code)


def error_response(
    errors: Any,
    message: str | None = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> Response:
    """
    Create a standardized error response.

    Args:
        errors: Error details (can be dict, list, or string)
        message: Optional human-readable error message
        status_code: HTTP status code (default: 400)

    Returns:
        Response object with standardized error format
    """
    error_data = errors
    if message:
        if isinstance(errors, dict):
            error_data = {"message": message, "details": errors}
        else:
            error_data = {"message": message, "details": errors}

    response_data = OrderedDict(
        [
            ("success", False),
            ("data", None),
            ("meta", None),
            ("errors", error_data),
        ]
    )
    return Response(response_data, status=status_code)


def created_response(data: Any = None, meta: dict | None = None) -> Response:
    """Create a standardized 201 Created response."""
    return success_response(data=data, meta=meta, status_code=status.HTTP_201_CREATED)


def no_content_response() -> Response:
    """Create a standardized 204 No Content response."""
    return Response(status=status.HTTP_204_NO_CONTENT)


def not_found_response(message: str = "Resource not found") -> Response:
    """Create a standardized 404 Not Found response."""
    return error_response(
        errors={"detail": message},
        status_code=status.HTTP_404_NOT_FOUND,
    )


def validation_error_response(errors: dict) -> Response:
    """Create a standardized 400 Validation Error response."""
    return error_response(
        errors=errors,
        message="Validation failed",
        status_code=status.HTTP_400_BAD_REQUEST,
    )


def permission_denied_response(message: str = "Permission denied") -> Response:
    """Create a standardized 403 Forbidden response."""
    return error_response(
        errors={"detail": message},
        status_code=status.HTTP_403_FORBIDDEN,
    )


def server_error_response(message: str = "Internal server error") -> Response:
    """Create a standardized 500 Internal Server Error response."""
    return error_response(
        errors={"detail": message},
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
