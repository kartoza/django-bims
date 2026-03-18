# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
OpenAPI schema configuration for BIMS API v1.

This module configures drf-spectacular for beautiful API documentation.

Made with love by Kartoza | https://kartoza.com
"""
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.plumbing import build_basic_type
from drf_spectacular.types import OpenApiTypes


class SessionAuthenticationScheme(OpenApiAuthenticationExtension):
    """Authentication scheme for Django session authentication."""

    target_class = "rest_framework.authentication.SessionAuthentication"
    name = "sessionAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "cookie",
            "name": "sessionid",
            "description": "Django session cookie authentication",
        }


class TokenAuthenticationScheme(OpenApiAuthenticationExtension):
    """Authentication scheme for DRF Token authentication."""

    target_class = "rest_framework.authentication.TokenAuthentication"
    name = "tokenAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "apiKey",
            "in": "header",
            "name": "Authorization",
            "description": "Token-based authentication. Use format: Token <your-token>",
        }


# Spectacular settings to be imported into Django settings
SPECTACULAR_SETTINGS = {
    "TITLE": "BIMS API",
    "DESCRIPTION": """
# Biodiversity Information Management System API

Welcome to the **BIMS API v1** documentation. This API provides programmatic access
to biodiversity data managed by the BIMS platform.

## Overview

BIMS (Biodiversity Information Management System) is an open-source platform for managing,
analyzing, and sharing biodiversity data, with a focus on freshwater ecosystems.

## Features

- 🗺️ **Location Sites** - Manage monitoring locations with geospatial data
- 🐟 **Biological Records** - Store and query species occurrence data
- 🌿 **Taxonomy** - Access taxonomic information and hierarchies
- 📊 **Analytics** - Generate summaries and statistics
- 📥 **Downloads** - Request data exports in various formats
- ✅ **Validation** - Manage data quality workflows

## Authentication

The API supports multiple authentication methods:

### Session Authentication
Use your browser session after logging into BIMS. Ideal for web-based integrations.

### Token Authentication
For programmatic access, use token authentication:
```
Authorization: Token your-api-token-here
```

To obtain a token, authenticate via `/api/v1/auth/token/` or generate one from your profile.

## Response Format

All API responses follow a consistent format:

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "count": 100,
    "page": 1,
    "page_size": 20,
    "total_pages": 5
  },
  "errors": null
}
```

## Rate Limiting

API requests are rate-limited to ensure fair usage:
- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour

## Support

- 📚 [Documentation](https://freshwaterbiodiversity.org/docs/)
- 🐛 [Report Issues](https://github.com/kartoza/django-bims/issues)
- 💬 [Contact Us](/contact/)

---

Made with ❤️ by [Kartoza](https://kartoza.com) | [GitHub](https://github.com/kartoza/django-bims)
    """,
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    # Contact information
    "CONTACT": {
        "name": "Kartoza",
        "url": "https://kartoza.com",
        "email": "info@kartoza.com",
    },
    # License
    "LICENSE": {
        "name": "AGPL-3.0",
        "url": "https://www.gnu.org/licenses/agpl-3.0.html",
    },
    # External documentation
    "EXTERNAL_DOCS": {
        "description": "BIMS Documentation",
        "url": "https://freshwaterbiodiversity.org/docs/",
    },
    # Tags for organizing endpoints
    "TAGS": [
        {
            "name": "Sites",
            "description": "Location sites and monitoring points. Sites are the primary geographic entities where biodiversity surveys are conducted.",
        },
        {
            "name": "Records",
            "description": "Biological collection records (species occurrences). Each record represents an observation of a species at a specific location and time.",
        },
        {
            "name": "Taxa",
            "description": "Taxonomic information and species data. Access species names, classifications, conservation status, and images.",
        },
        {
            "name": "Taxon Groups",
            "description": "Taxon groups/modules (e.g., Fish, Invertebrates, Algae). Groups organize taxa for filtering and analysis.",
        },
        {
            "name": "Surveys",
            "description": "Site visits and survey data. Surveys represent field visits to sites where data is collected.",
        },
        {
            "name": "Source References",
            "description": "Bibliographic references and data sources. Track the provenance of biodiversity data.",
        },
        {
            "name": "Boundaries",
            "description": "Geographic boundaries for spatial filtering. Includes administrative regions and user-defined areas.",
        },
        {
            "name": "Downloads",
            "description": "Data export and download operations. Request and track asynchronous data exports.",
        },
        {
            "name": "Tasks",
            "description": "Background task status. Monitor long-running operations like data exports.",
        },
    ],
    # Schema customization
    "COMPONENT_SPLIT_REQUEST": True,
    "COMPONENT_NO_READ_ONLY_REQUIRED": True,
    # Sorting
    "SORT_OPERATIONS": True,
    "SORT_OPERATION_PARAMETERS": True,
    # Enum handling
    "ENUM_NAME_OVERRIDES": {
        "ConservationStatusEnum": [
            "LC",
            "NT",
            "VU",
            "EN",
            "CR",
            "EW",
            "EX",
            "DD",
            "NE",
        ],
        "EcosystemTypeEnum": [
            "river",
            "wetland",
            "estuary",
            "dam",
            "lake",
            "coastal",
            "marine",
        ],
    },
    # Preprocessing hooks
    "PREPROCESSING_HOOKS": [
        "drf_spectacular.hooks.preprocess_exclude_path_format",
    ],
    # Postprocessing hooks
    "POSTPROCESSING_HOOKS": [
        "drf_spectacular.hooks.postprocess_schema_enums",
    ],
    # Security schemes
    "SECURITY": [
        {"sessionAuth": []},
        {"tokenAuth": []},
    ],
    # Swagger UI settings
    "SWAGGER_UI_SETTINGS": {
        "deepLinking": True,
        "persistAuthorization": True,
        "displayOperationId": False,
        "filter": True,
        "docExpansion": "list",
        "defaultModelsExpandDepth": 2,
        "defaultModelExpandDepth": 2,
        "syntaxHighlight.theme": "monokai",
        "tryItOutEnabled": True,
    },
    # ReDoc settings
    "REDOC_UI_SETTINGS": {
        "hideDownloadButton": False,
        "expandResponses": "200,201",
        "pathInMiddlePanel": True,
        "nativeScrollbars": True,
    },
    # Custom CSS for branding
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "REDOC_DIST": "SIDECAR",
}
