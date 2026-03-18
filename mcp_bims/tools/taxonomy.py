# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""MCP tools for taxonomy operations."""
from typing import Any

from mcp.types import Tool

from mcp_bims.clients import BimsClient

# Tool registry
TOOLS = {
    "list_taxa",
    "get_taxon",
    "find_taxon",
    "get_taxon_tree",
    "get_taxon_images",
    "list_taxon_groups",
    "get_taxon_records",
}


def get_tools() -> list[Tool]:
    """Return list of taxonomy tools."""
    return [
        Tool(
            name="list_taxa",
            description="List taxonomy records with optional filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "default": 1},
                    "page_size": {"type": "integer", "default": 20},
                    "name": {"type": "string", "description": "Filter by name (partial match)"},
                    "rank": {"type": "string", "description": "Filter by taxonomic rank"},
                    "taxon_group": {"type": "integer", "description": "Filter by taxon group ID"},
                    "iucn_category": {"type": "string", "description": "Filter by IUCN category"},
                    "endemism": {"type": "string", "description": "Filter by endemism status"},
                    "validated": {"type": "boolean", "description": "Filter by validation status"},
                    "has_gbif_key": {"type": "boolean", "description": "Filter by GBIF key presence"},
                    "search": {"type": "string", "description": "Search across fields"},
                },
            },
        ),
        Tool(
            name="get_taxon",
            description="Get detailed information about a specific taxon.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon_id": {"type": "integer", "description": "Taxon ID"},
                },
                "required": ["taxon_id"],
            },
        ),
        Tool(
            name="find_taxon",
            description="Find a taxon by name with autocomplete support.",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query (name)"},
                    "rank": {"type": "string", "description": "Filter by taxonomic rank"},
                    "limit": {"type": "integer", "default": 20, "description": "Maximum results"},
                },
                "required": ["query"],
            },
        ),
        Tool(
            name="get_taxon_tree",
            description="Get the taxonomy tree for a taxon (ancestors or descendants).",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon_id": {"type": "integer", "description": "Starting taxon ID"},
                    "direction": {
                        "type": "string",
                        "enum": ["up", "down"],
                        "default": "down",
                        "description": "'up' for ancestors, 'down' for descendants",
                    },
                    "depth": {"type": "integer", "default": 10, "description": "Maximum tree depth"},
                },
                "required": ["taxon_id"],
            },
        ),
        Tool(
            name="get_taxon_images",
            description="Get images for a taxon.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon_id": {"type": "integer", "description": "Taxon ID"},
                },
                "required": ["taxon_id"],
            },
        ),
        Tool(
            name="list_taxon_groups",
            description="List all available taxon groups (modules).",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_taxon_records",
            description="Get biological records for a specific taxon.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon_id": {"type": "integer", "description": "Taxon ID"},
                    "page": {"type": "integer", "default": 1},
                    "page_size": {"type": "integer", "default": 20},
                },
                "required": ["taxon_id"],
            },
        ),
    ]


async def handle_tool(client: BimsClient, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle a taxonomy tool call."""

    if name == "list_taxa":
        return await client.list_taxa(**arguments)

    elif name == "get_taxon":
        return await client.get_taxon(arguments["taxon_id"])

    elif name == "find_taxon":
        return await client.find_taxon(
            arguments["query"],
            arguments.get("rank"),
        )

    elif name == "get_taxon_tree":
        return await client.get_taxon_tree(
            arguments["taxon_id"],
            arguments.get("direction", "down"),
            arguments.get("depth", 10),
        )

    elif name == "get_taxon_images":
        return await client.get(f"taxa/{arguments['taxon_id']}/images/")

    elif name == "list_taxon_groups":
        return await client.list_taxon_groups()

    elif name == "get_taxon_records":
        taxon_id = arguments.pop("taxon_id")
        return await client.get(f"taxa/{taxon_id}/records/", arguments)

    else:
        raise ValueError(f"Unknown tool: {name}")
