# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""Common Pydantic schemas used across the MCP server."""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class PaginationParams(BaseModel):
    """Common pagination parameters."""

    page: int = Field(default=1, ge=1, description="Page number")
    page_size: int = Field(default=20, ge=1, le=100, description="Number of items per page")


class BoundingBox(BaseModel):
    """Geographic bounding box."""

    west: float = Field(..., ge=-180, le=180, description="Western longitude")
    south: float = Field(..., ge=-90, le=90, description="Southern latitude")
    east: float = Field(..., ge=-180, le=180, description="Eastern longitude")
    north: float = Field(..., ge=-90, le=90, description="Northern latitude")

    def to_string(self) -> str:
        """Convert to comma-separated string format."""
        return f"{self.west},{self.south},{self.east},{self.north}"


class Coordinates(BaseModel):
    """Geographic coordinates."""

    latitude: float = Field(..., ge=-90, le=90, description="Latitude")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude")


class ValidationResult(BaseModel):
    """Result of a validation operation."""

    success: bool = Field(..., description="Whether validation succeeded")
    validated_count: int = Field(default=0, description="Number of items validated")
    message: str = Field(default="", description="Status message")


class TaskStatus(BaseModel):
    """Status of an async task."""

    task_id: str = Field(..., description="Unique task identifier")
    status: Literal["PENDING", "STARTED", "SUCCESS", "FAILURE", "REVOKED"] = Field(
        ..., description="Current task status"
    )
    ready: bool = Field(..., description="Whether task has completed")
    result: Optional[dict] = Field(default=None, description="Task result if completed")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    progress: Optional[int] = Field(default=None, description="Progress percentage if available")


class ApiResponse(BaseModel):
    """Standard API response wrapper."""

    success: bool = Field(..., description="Whether the request succeeded")
    data: Optional[dict] = Field(default=None, description="Response data")
    meta: Optional[dict] = Field(default=None, description="Response metadata")
    errors: Optional[dict] = Field(default=None, description="Error details if failed")
