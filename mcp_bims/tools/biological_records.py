# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""MCP tools for biological collection record operations."""
from typing import Any

from mcp.types import Tool

from mcp_bims.clients import BimsClient

# Tool registry
TOOLS = {
    "list_biological_records",
    "get_biological_record",
    "search_biological_records",
    "get_records_by_site",
    "get_records_by_taxon",
    "get_records_summary",
}


def get_tools() -> list[Tool]:
    """Return list of biological record tools."""
    return [
        Tool(
            name="list_biological_records",
            description="List biological collection records with optional filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "default": 1},
                    "page_size": {"type": "integer", "default": 20},
                    "site": {"type": "integer", "description": "Filter by site ID"},
                    "site_name": {"type": "string", "description": "Filter by site name"},
                    "taxonomy": {"type": "integer", "description": "Filter by taxonomy ID"},
                    "taxon_name": {"type": "string", "description": "Filter by taxon name"},
                    "taxon_group": {"type": "integer", "description": "Filter by taxon group"},
                    "iucn_category": {"type": "string", "description": "Filter by IUCN category"},
                    "endemism": {"type": "string", "description": "Filter by endemism"},
                    "year_from": {"type": "integer", "description": "Filter by year (from)"},
                    "year_to": {"type": "integer", "description": "Filter by year (to)"},
                    "collector": {"type": "string", "description": "Filter by collector"},
                    "validated": {"type": "boolean", "description": "Filter by validation status"},
                    "bbox": {"type": "string", "description": "Bounding box filter"},
                    "search": {"type": "string", "description": "Search across fields"},
                },
            },
        ),
        Tool(
            name="get_biological_record",
            description="Get detailed information about a specific biological collection record.",
            inputSchema={
                "type": "object",
                "properties": {
                    "record_id": {"type": "integer", "description": "Record ID"},
                },
                "required": ["record_id"],
            },
        ),
        Tool(
            name="search_biological_records",
            description="Advanced search for biological records with optional grouping.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "default": 1},
                    "page_size": {"type": "integer", "default": 20},
                    "group_by": {
                        "type": "string",
                        "enum": ["taxon", "site", "year"],
                        "description": "Group results by field",
                    },
                    "site_name": {"type": "string"},
                    "taxon_name": {"type": "string"},
                    "taxon_group": {"type": "integer"},
                    "iucn_category": {"type": "string"},
                    "endemism": {"type": "string"},
                    "year_from": {"type": "integer"},
                    "year_to": {"type": "integer"},
                    "bbox": {"type": "string"},
                    "search": {"type": "string"},
                },
            },
        ),
        Tool(
            name="get_records_by_site",
            description="Get biological records grouped by site.",
            inputSchema={
                "type": "object",
                "properties": {
                    "site_id": {"type": "integer", "description": "Optional site ID to filter"},
                },
            },
        ),
        Tool(
            name="get_records_by_taxon",
            description="Get biological records grouped by taxon.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxonomy_id": {"type": "integer", "description": "Optional taxonomy ID to filter"},
                },
            },
        ),
        Tool(
            name="get_records_summary",
            description="Get summary statistics for biological records.",
            inputSchema={
                "type": "object",
                "properties": {
                    "site": {"type": "integer", "description": "Filter by site ID"},
                    "taxonomy": {"type": "integer", "description": "Filter by taxonomy ID"},
                    "taxon_group": {"type": "integer", "description": "Filter by taxon group"},
                    "year_from": {"type": "integer"},
                    "year_to": {"type": "integer"},
                    "bbox": {"type": "string"},
                },
            },
        ),
    ]


async def handle_tool(client: BimsClient, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle a biological record tool call."""

    if name == "list_biological_records":
        return await client.list_records(**arguments)

    elif name == "get_biological_record":
        return await client.get_record(arguments["record_id"])

    elif name == "search_biological_records":
        return await client.search_records(**arguments)

    elif name == "get_records_by_site":
        params = {}
        if "site_id" in arguments:
            params["site_id"] = arguments["site_id"]
        return await client.get("records/by_site/", params)

    elif name == "get_records_by_taxon":
        params = {}
        if "taxonomy_id" in arguments:
            params["taxonomy_id"] = arguments["taxonomy_id"]
        return await client.get("records/by_taxon/", params)

    elif name == "get_records_summary":
        return await client.get("records/summary/", arguments)

    else:
        raise ValueError(f"Unknown tool: {name}")
