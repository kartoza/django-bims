# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""Pydantic schemas for biological collection record operations."""
from typing import Optional
from datetime import date
from pydantic import BaseModel, Field

from mcp_bims.schemas.common import PaginationParams


class BiologicalRecordSchema(BaseModel):
    """Schema for a biological collection record."""

    id: int = Field(..., description="Unique record identifier")
    uuid: Optional[str] = Field(default=None, description="Record UUID")
    site_name: Optional[str] = Field(default=None, description="Site name")
    site_code: Optional[str] = Field(default=None, description="Site code")
    taxon_name: Optional[str] = Field(default=None, description="Taxon canonical name")
    taxon_rank: Optional[str] = Field(default=None, description="Taxonomic rank")
    original_species_name: Optional[str] = Field(default=None, description="Original species name as recorded")
    collection_date: Optional[date] = Field(default=None, description="Collection date")
    collector_name: Optional[str] = Field(default=None, description="Collector name")
    abundance_number: Optional[float] = Field(default=None, description="Abundance count")
    present: bool = Field(default=True, description="Whether species was present")
    validated: bool = Field(default=False, description="Whether record is validated")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class RecordListParams(PaginationParams):
    """Parameters for listing biological records."""

    site: Optional[int] = Field(default=None, description="Filter by site ID")
    site_name: Optional[str] = Field(default=None, description="Filter by site name (partial match)")
    taxonomy: Optional[int] = Field(default=None, description="Filter by taxonomy ID")
    taxon_name: Optional[str] = Field(default=None, description="Filter by taxon name (partial match)")
    taxon_group: Optional[int] = Field(default=None, description="Filter by taxon group ID")
    iucn_category: Optional[str] = Field(default=None, description="Filter by IUCN category")
    endemism: Optional[str] = Field(default=None, description="Filter by endemism status")
    year_from: Optional[int] = Field(default=None, description="Filter by year (from)")
    year_to: Optional[int] = Field(default=None, description="Filter by year (to)")
    collector: Optional[str] = Field(default=None, description="Filter by collector name")
    validated: Optional[bool] = Field(default=None, description="Filter by validation status")
    bbox: Optional[str] = Field(default=None, description="Bounding box filter (west,south,east,north)")
    search: Optional[str] = Field(default=None, description="Search across multiple fields")


class RecordSearchParams(RecordListParams):
    """Extended parameters for searching biological records."""

    group_by: Optional[str] = Field(
        default=None,
        description="Group results by field (taxon, site, year)"
    )
