# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Compatibility module for optional drf-spectacular support.

Provides no-op decorators when drf-spectacular is not installed.

Made with love by Kartoza | https://kartoza.com
"""

try:
    from drf_spectacular.utils import (
        extend_schema,
        extend_schema_view,
        OpenApiParameter,
        OpenApiExample,
        OpenApiTypes,
    )
    HAS_SPECTACULAR = True
except ImportError:
    HAS_SPECTACULAR = False

    # Create no-op decorator factories
    def extend_schema(**kwargs):
        """No-op decorator when drf-spectacular is not available."""
        def decorator(func):
            return func
        return decorator

    def extend_schema_view(**kwargs):
        """No-op class decorator when drf-spectacular is not available."""
        def decorator(cls):
            return cls
        return decorator

    class OpenApiParameter:
        """Dummy class when drf-spectacular is not available."""
        def __init__(self, *args, **kwargs):
            pass

    class OpenApiExample:
        """Dummy class when drf-spectacular is not available."""
        def __init__(self, *args, **kwargs):
            pass

    class OpenApiTypes:
        """Dummy class with common OpenAPI types."""
        OBJECT = "object"
        STRING = "string"
        INT = "int"
        FLOAT = "float"
        BOOL = "bool"
        BINARY = "binary"
        DATE = "date"
        DATETIME = "datetime"
