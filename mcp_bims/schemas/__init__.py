# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""Pydantic schemas for MCP tool inputs and outputs."""

from mcp_bims.schemas.sites import (
    LocationSiteSchema,
    LocationSiteListParams,
    LocationSiteCreateParams,
    NearbySearchParams,
    CoordinateSearchParams,
)
from mcp_bims.schemas.records import (
    BiologicalRecordSchema,
    RecordListParams,
    RecordSearchParams,
)
from mcp_bims.schemas.taxa import (
    TaxonomySchema,
    TaxonListParams,
    TaxonFindParams,
    TaxonTreeParams,
)
from mcp_bims.schemas.common import (
    PaginationParams,
    BoundingBox,
    ValidationResult,
    TaskStatus,
)

__all__ = [
    # Sites
    "LocationSiteSchema",
    "LocationSiteListParams",
    "LocationSiteCreateParams",
    "NearbySearchParams",
    "CoordinateSearchParams",
    # Records
    "BiologicalRecordSchema",
    "RecordListParams",
    "RecordSearchParams",
    # Taxa
    "TaxonomySchema",
    "TaxonListParams",
    "TaxonFindParams",
    "TaxonTreeParams",
    # Common
    "PaginationParams",
    "BoundingBox",
    "ValidationResult",
    "TaskStatus",
]
