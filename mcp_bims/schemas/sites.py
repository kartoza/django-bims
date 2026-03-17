# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""Pydantic schemas for location site operations."""
from typing import Optional
from pydantic import BaseModel, Field

from mcp_bims.schemas.common import PaginationParams, Coordinates


class LocationSiteSchema(BaseModel):
    """Schema for a location site."""

    id: int = Field(..., description="Unique site identifier")
    name: str = Field(..., description="Site name")
    site_code: str = Field(default="", description="Site code")
    site_description: Optional[str] = Field(default=None, description="Site description")
    geometry: Optional[str] = Field(default=None, description="GeoJSON geometry")
    river_name: Optional[str] = Field(default=None, description="River name if applicable")
    ecosystem_type: Optional[str] = Field(default=None, description="Ecosystem type")
    wetland_name: Optional[str] = Field(default=None, description="Wetland name if applicable")
    owner_name: Optional[str] = Field(default=None, description="Owner's name")
    validated: bool = Field(default=False, description="Whether site is validated")


class LocationSiteListParams(PaginationParams):
    """Parameters for listing location sites."""

    name: Optional[str] = Field(default=None, description="Filter by name (partial match)")
    site_code: Optional[str] = Field(default=None, description="Filter by site code (partial match)")
    ecosystem_type: Optional[str] = Field(default=None, description="Filter by ecosystem type")
    river_name: Optional[str] = Field(default=None, description="Filter by river name")
    validated: Optional[bool] = Field(default=None, description="Filter by validation status")
    bbox: Optional[str] = Field(default=None, description="Bounding box filter (west,south,east,north)")
    search: Optional[str] = Field(default=None, description="Search across multiple fields")


class LocationSiteCreateParams(BaseModel):
    """Parameters for creating a location site."""

    name: str = Field(..., description="Site name", min_length=1, max_length=300)
    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    location_type_id: int = Field(..., description="Location type ID")
    site_code: Optional[str] = Field(default=None, description="Site code")
    site_description: Optional[str] = Field(default=None, description="Site description")
    ecosystem_type: Optional[str] = Field(default=None, description="Ecosystem type")
    wetland_name: Optional[str] = Field(default=None, description="Wetland name")
    refined_geomorphological: Optional[str] = Field(default=None, description="Refined geomorphological zone")


class NearbySearchParams(BaseModel):
    """Parameters for finding nearby sites."""

    latitude: float = Field(..., ge=-90, le=90, description="Center latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Center longitude")
    radius: float = Field(default=10000, ge=0, description="Search radius in meters")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum results to return")


class CoordinateSearchParams(BaseModel):
    """Parameters for finding a site by coordinates."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")
    tolerance: float = Field(default=0.0001, ge=0, description="Coordinate tolerance in degrees")
