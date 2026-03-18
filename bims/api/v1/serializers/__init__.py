# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Serializers for API v1.

This module exports all serializers for the versioned API.
"""
from bims.api.v1.serializers.sites import (
    LocationSiteListSerializer,
    LocationSiteDetailSerializer,
    LocationSiteCreateSerializer,
    LocationSiteSummarySerializer,
)
from bims.api.v1.serializers.records import (
    BiologicalCollectionRecordListSerializer,
    BiologicalCollectionRecordDetailSerializer,
    BiologicalCollectionRecordCreateSerializer,
)
from bims.api.v1.serializers.taxa import (
    TaxonomyListSerializer,
    TaxonomyDetailSerializer,
    TaxonomyTreeSerializer,
)
from bims.api.v1.serializers.taxon_groups import TaxonGroupSerializer
from bims.api.v1.serializers.surveys import (
    SurveyListSerializer,
    SurveyDetailSerializer,
)
from bims.api.v1.serializers.source_references import SourceReferenceSerializer
from bims.api.v1.serializers.boundaries import (
    BoundarySerializer,
    UserBoundarySerializer,
)

__all__ = [
    # Sites
    "LocationSiteListSerializer",
    "LocationSiteDetailSerializer",
    "LocationSiteCreateSerializer",
    "LocationSiteSummarySerializer",
    # Records
    "BiologicalCollectionRecordListSerializer",
    "BiologicalCollectionRecordDetailSerializer",
    "BiologicalCollectionRecordCreateSerializer",
    # Taxa
    "TaxonomyListSerializer",
    "TaxonomyDetailSerializer",
    "TaxonomyTreeSerializer",
    # Taxon Groups
    "TaxonGroupSerializer",
    # Surveys
    "SurveyListSerializer",
    "SurveyDetailSerializer",
    # Source References
    "SourceReferenceSerializer",
    # Boundaries
    "BoundarySerializer",
    "UserBoundarySerializer",
]
