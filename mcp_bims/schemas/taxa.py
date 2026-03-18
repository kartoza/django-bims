# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""Pydantic schemas for taxonomy operations."""
from typing import Optional, Literal
from pydantic import BaseModel, Field

from mcp_bims.schemas.common import PaginationParams


class TaxonomySchema(BaseModel):
    """Schema for a taxonomy record."""

    id: int = Field(..., description="Unique taxonomy identifier")
    scientific_name: str = Field(..., description="Scientific name")
    canonical_name: Optional[str] = Field(default=None, description="Canonical name")
    rank: str = Field(..., description="Taxonomic rank")
    taxonomic_status: Optional[str] = Field(default=None, description="Taxonomic status")
    iucn_status: Optional[str] = Field(default=None, description="IUCN conservation status")
    endemism: Optional[str] = Field(default=None, description="Endemism status")
    common_name: Optional[str] = Field(default=None, description="Common/vernacular name")
    gbif_key: Optional[int] = Field(default=None, description="GBIF taxon key")
    verified: bool = Field(default=False, description="Whether taxon is verified")
    record_count: Optional[int] = Field(default=None, description="Number of biological records")


class TaxonListParams(PaginationParams):
    """Parameters for listing taxonomy records."""

    name: Optional[str] = Field(default=None, description="Filter by name (partial match)")
    rank: Optional[str] = Field(default=None, description="Filter by taxonomic rank")
    taxon_group: Optional[int] = Field(default=None, description="Filter by taxon group ID")
    iucn_category: Optional[str] = Field(default=None, description="Filter by IUCN category")
    endemism: Optional[str] = Field(default=None, description="Filter by endemism status")
    validated: Optional[bool] = Field(default=None, description="Filter by validation status")
    has_gbif_key: Optional[bool] = Field(default=None, description="Filter by having GBIF key")
    search: Optional[str] = Field(default=None, description="Search across multiple fields")


class TaxonFindParams(BaseModel):
    """Parameters for finding a taxon by name."""

    query: str = Field(..., description="Search query (name)", min_length=1)
    rank: Optional[str] = Field(default=None, description="Filter by taxonomic rank")
    limit: int = Field(default=20, ge=1, le=100, description="Maximum results to return")


class TaxonTreeParams(BaseModel):
    """Parameters for getting taxonomy tree."""

    taxon_id: int = Field(..., description="Starting taxon ID")
    direction: Literal["up", "down"] = Field(
        default="down",
        description="Tree direction: 'up' for ancestors, 'down' for descendants"
    )
    depth: int = Field(default=10, ge=1, le=20, description="Maximum tree depth")


class TaxonGroupSchema(BaseModel):
    """Schema for a taxon group."""

    id: int = Field(..., description="Unique group identifier")
    name: str = Field(..., description="Group name")
    singular_name: Optional[str] = Field(default=None, description="Singular form of name")
    category: Optional[str] = Field(default=None, description="Group category")
    display_order: int = Field(default=0, description="Display order")
    taxa_count: int = Field(default=0, description="Number of taxa in group")
    logo_url: Optional[str] = Field(default=None, description="Group logo URL")
