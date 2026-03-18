# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""MCP tools for location site operations."""
from typing import Any

from mcp.types import Tool

from mcp_bims.clients import BimsClient

# Tool registry
TOOLS = {
    "list_location_sites",
    "get_location_site",
    "get_nearby_sites",
    "get_site_by_coordinates",
    "create_location_site",
    "merge_sites",
    "get_site_surveys",
    "get_site_records",
}


def get_tools() -> list[Tool]:
    """Return list of location site tools."""
    return [
        Tool(
            name="list_location_sites",
            description="List location sites with optional filters. Returns paginated results.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "default": 1, "description": "Page number"},
                    "page_size": {"type": "integer", "default": 20, "description": "Items per page"},
                    "name": {"type": "string", "description": "Filter by site name (partial match)"},
                    "site_code": {"type": "string", "description": "Filter by site code"},
                    "ecosystem_type": {"type": "string", "description": "Filter by ecosystem type"},
                    "river_name": {"type": "string", "description": "Filter by river name"},
                    "validated": {"type": "boolean", "description": "Filter by validation status"},
                    "bbox": {"type": "string", "description": "Bounding box (west,south,east,north)"},
                    "search": {"type": "string", "description": "Search across multiple fields"},
                },
            },
        ),
        Tool(
            name="get_location_site",
            description="Get detailed information about a specific location site.",
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {"type": "integer", "description": "Site ID"},
                },
                "required": ["site_id"],
            },
        ),
        Tool(
            name="get_nearby_sites",
            description="Find location sites near a given coordinate.",
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "Latitude (-90 to 90)"},
                    "longitude": {"type": "number", "description": "Longitude (-180 to 180)"},
                    "radius": {"type": "number", "default": 10000, "description": "Search radius in meters"},
                    "limit": {"type": "integer", "default": 10, "description": "Maximum results"},
                },
                "required": ["latitude", "longitude"],
            },
        ),
        Tool(
            name="get_site_by_coordinates",
            description="Find a location site at exact coordinates.",
            inputSchema={
                "type": "object",
                "properties": {
                    "latitude": {"type": "number", "description": "Latitude"},
                    "longitude": {"type": "number", "description": "Longitude"},
                    "tolerance": {"type": "number", "default": 0.0001, "description": "Coordinate tolerance"},
                },
                "required": ["latitude", "longitude"],
            },
        ),
        Tool(
            name="create_location_site",
            description="Create a new location site.",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Site name"},
                    "latitude": {"type": "number", "description": "Latitude"},
                    "longitude": {"type": "number", "description": "Longitude"},
                    "location_type_id": {"type": "integer", "description": "Location type ID"},
                    "site_code": {"type": "string", "description": "Site code"},
                    "site_description": {"type": "string", "description": "Site description"},
                    "ecosystem_type": {"type": "string", "description": "Ecosystem type"},
                },
                "required": ["name", "latitude", "longitude", "location_type_id"],
            },
        ),
        Tool(
            name="merge_sites",
            description="Merge multiple location sites into one.",
            inputSchema={
                "type": "object",
                "properties": {
                    "primary_site_id": {"type": "integer", "description": "Primary site to keep"},
                    "merge_site_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "Site IDs to merge into primary",
                    },
                },
                "required": ["primary_site_id", "merge_site_ids"],
            },
        ),
        Tool(
            name="get_site_surveys",
            description="Get all surveys for a location site.",
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {"type": "integer", "description": "Site ID"},
                },
                "required": ["site_id"],
            },
        ),
        Tool(
            name="get_site_records",
            description="Get biological records for a location site.",
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {"type": "integer", "description": "Site ID"},
                    "page": {"type": "integer", "default": 1, "description": "Page number"},
                    "page_size": {"type": "integer", "default": 20, "description": "Items per page"},
                },
                "required": ["site_id"],
            },
        ),
    ]


async def handle_tool(client: BimsClient, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle a location site tool call."""

    if name == "list_location_sites":
        return await client.list_sites(**arguments)

    elif name == "get_location_site":
        return await client.get_site(arguments["site_id"])

    elif name == "get_nearby_sites":
        params = {
            "lat": arguments["latitude"],
            "lon": arguments["longitude"],
            "radius": arguments.get("radius", 10000),
            "limit": arguments.get("limit", 10),
        }
        return await client.get("sites/nearby/", params)

    elif name == "get_site_by_coordinates":
        params = {
            "lat": arguments["latitude"],
            "lon": arguments["longitude"],
            "tolerance": arguments.get("tolerance", 0.0001),
        }
        return await client.get("sites/coordinates/", params)

    elif name == "create_location_site":
        return await client.post("sites/", arguments)

    elif name == "merge_sites":
        return await client.post("merge-sites/", {
            "primary_site": arguments["primary_site_id"],
            "merge_sites": arguments["merge_site_ids"],
        })

    elif name == "get_site_surveys":
        return await client.get(f"sites/{arguments['site_id']}/surveys/")

    elif name == "get_site_records":
        site_id = arguments.pop("site_id")
        return await client.get(f"sites/{site_id}/records/", arguments)

    else:
        raise ValueError(f"Unknown tool: {name}")
