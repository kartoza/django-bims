# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
ViewSets for API v1.

This module exports all ViewSets for the versioned API.
"""
from bims.api.v1.viewsets.base import StandardModelViewSet
from bims.api.v1.viewsets.sites import LocationSiteViewSet
from bims.api.v1.viewsets.records import BiologicalCollectionRecordViewSet
from bims.api.v1.viewsets.taxa import TaxonomyViewSet
from bims.api.v1.viewsets.taxon_groups import TaxonGroupViewSet
from bims.api.v1.viewsets.surveys import SurveyViewSet
from bims.api.v1.viewsets.source_references import SourceReferenceViewSet
from bims.api.v1.viewsets.boundaries import BoundaryViewSet, UserBoundaryViewSet
from bims.api.v1.viewsets.downloads import DownloadViewSet
from bims.api.v1.viewsets.tasks import TaskStatusViewSet

__all__ = [
    "StandardModelViewSet",
    "LocationSiteViewSet",
    "BiologicalCollectionRecordViewSet",
    "TaxonomyViewSet",
    "TaxonGroupViewSet",
    "SurveyViewSet",
    "SourceReferenceViewSet",
    "BoundaryViewSet",
    "UserBoundaryViewSet",
    "DownloadViewSet",
    "TaskStatusViewSet",
]
