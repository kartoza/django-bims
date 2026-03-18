# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
URL configuration for API v1.

This module defines the URL patterns for the versioned API using DRF routers.
All endpoints are prefixed with /api/v1/ in the main URL configuration.

Made with love by Kartoza | https://kartoza.com
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from bims.api.v1.viewsets.sites import LocationSiteViewSet
from bims.api.v1.viewsets.records import BiologicalCollectionRecordViewSet
from bims.api.v1.viewsets.taxa import TaxonomyViewSet
from bims.api.v1.viewsets.taxon_groups import TaxonGroupViewSet
from bims.api.v1.viewsets.surveys import SurveyViewSet
from bims.api.v1.viewsets.source_references import SourceReferenceViewSet
from bims.api.v1.viewsets.boundaries import BoundaryViewSet, UserBoundaryViewSet
from bims.api.v1.viewsets.downloads import DownloadViewSet
from bims.api.v1.viewsets.tasks import TaskStatusViewSet
from bims.api.v1.viewsets.auth import AuthViewSet
from bims.api.v1.viewsets.taxon_proposals import TaxonProposalViewSet
from bims.api.v1.viewsets.taxa_management import TaxaManagementViewSet

app_name = "api-v1"

# Create router and register ViewSets
router = DefaultRouter()

# Core resources
router.register(r"sites", LocationSiteViewSet, basename="site")
router.register(r"records", BiologicalCollectionRecordViewSet, basename="record")
router.register(r"taxa", TaxonomyViewSet, basename="taxon")
router.register(r"taxon-groups", TaxonGroupViewSet, basename="taxon-group")
router.register(r"surveys", SurveyViewSet, basename="survey")

# Supporting resources
router.register(r"source-references", SourceReferenceViewSet, basename="source-reference")
router.register(r"boundaries", BoundaryViewSet, basename="boundary")
router.register(r"user-boundaries", UserBoundaryViewSet, basename="user-boundary")

# Async operations
router.register(r"downloads", DownloadViewSet, basename="download")
router.register(r"tasks", TaskStatusViewSet, basename="task")

# Authentication
router.register(r"auth", AuthViewSet, basename="auth")

# Taxa management (proposals, GBIF, batch operations)
router.register(r"taxon-proposals", TaxonProposalViewSet, basename="taxon-proposal")
router.register(r"taxa-management", TaxaManagementViewSet, basename="taxa-management")

urlpatterns = [
    # API endpoints
    path("", include(router.urls)),
]

# Add OpenAPI documentation endpoints if drf-spectacular is available
try:
    from drf_spectacular.views import (
        SpectacularAPIView,
        SpectacularSwaggerView,
        SpectacularRedocView,
    )

    urlpatterns += [
        # OpenAPI schema (JSON/YAML)
        path("schema/", SpectacularAPIView.as_view(), name="schema"),

        # Swagger UI - Interactive API documentation
        path(
            "docs/",
            SpectacularSwaggerView.as_view(url_name="api-v1:schema"),
            name="swagger-ui",
        ),

        # ReDoc - Alternative documentation view
        path(
            "redoc/",
            SpectacularRedocView.as_view(url_name="api-v1:schema"),
            name="redoc",
        ),
    ]
except ImportError:
    # drf-spectacular not installed, skip API documentation endpoints
    pass
