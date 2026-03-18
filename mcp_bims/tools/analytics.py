# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""MCP tools for analytics and export operations."""
from typing import Any

from mcp.types import Tool

from mcp_bims.clients import BimsClient

# Tool registry
TOOLS = {
    "get_module_summary",
    "get_site_summary",
    "get_conservation_status_chart",
    "get_endemism_chart",
    "request_csv_download",
    "request_checklist_download",
    "get_download_status",
}


def get_tools() -> list[Tool]:
    """Return list of analytics and export tools."""
    return [
        Tool(
            name="get_module_summary",
            description="Get summary statistics for BIMS modules (taxon groups).",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="get_site_summary",
            description="Get summary statistics for location sites.",
            inputSchema={
                "type": "object",
                "properties": {
                    "bbox": {"type": "string", "description": "Bounding box filter"},
                    "ecosystem_type": {"type": "string", "description": "Filter by ecosystem type"},
                },
            },
        ),
        Tool(
            name="get_conservation_status_chart",
            description="Get conservation status distribution data for charts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon_group": {"type": "integer", "description": "Filter by taxon group"},
                    "bbox": {"type": "string", "description": "Bounding box filter"},
                },
            },
        ),
        Tool(
            name="get_endemism_chart",
            description="Get endemism distribution data for charts.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon_group": {"type": "integer", "description": "Filter by taxon group"},
                    "bbox": {"type": "string", "description": "Bounding box filter"},
                },
            },
        ),
        Tool(
            name="request_csv_download",
            description="Request an async CSV download of biological records.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon_group": {"type": "integer", "description": "Filter by taxon group"},
                    "year_from": {"type": "integer", "description": "Filter by year (from)"},
                    "year_to": {"type": "integer", "description": "Filter by year (to)"},
                    "bbox": {"type": "string", "description": "Bounding box filter"},
                    "validated": {"type": "boolean", "description": "Only validated records"},
                },
            },
        ),
        Tool(
            name="request_checklist_download",
            description="Request an async checklist download for a taxon group.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon_group_id": {"type": "integer", "description": "Taxon group ID"},
                    "boundary_id": {"type": "integer", "description": "Optional boundary ID"},
                },
                "required": ["taxon_group_id"],
            },
        ),
        Tool(
            name="get_download_status",
            description="Check the status of an async download request.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_id": {"type": "string", "description": "Task ID from download request"},
                },
                "required": ["task_id"],
            },
        ),
    ]


async def handle_tool(client: BimsClient, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle an analytics/export tool call."""

    if name == "get_module_summary":
        return await client.get("taxon-groups/summary/")

    elif name == "get_site_summary":
        return await client.get("sites/summary/", arguments)

    elif name == "get_conservation_status_chart":
        return await client.get("location-sites-cons-chart-data/", arguments)

    elif name == "get_endemism_chart":
        return await client.get("location-sites-endemism-chart-data/", arguments)

    elif name == "request_csv_download":
        return await client.request_download("csv", arguments)

    elif name == "request_checklist_download":
        return await client.request_download("checklist", arguments)

    elif name == "get_download_status":
        return await client.get_task_status(arguments["task_id"])

    else:
        raise ValueError(f"Unknown tool: {name}")
