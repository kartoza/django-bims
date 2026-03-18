# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""MCP tools for validation operations."""
from typing import Any

from mcp.types import Tool

from mcp_bims.clients import BimsClient

# Tool registry
TOOLS = {
    "validate_site_visit",
    "reject_site_visit",
    "get_pending_validations",
    "bulk_validate",
    "bulk_reject",
    "validate_taxon",
    "reject_taxon",
    "get_validation_summary",
}


def get_tools() -> list[Tool]:
    """Return list of validation tools."""
    return [
        Tool(
            name="validate_site_visit",
            description="Validate a site visit (survey) record.",
            inputSchema={
                "type": "object",
                "properties": {
                    "survey_id": {"type": "integer", "description": "Survey ID to validate"},
                    "comment": {"type": "string", "description": "Optional validation comment"},
                },
                "required": ["survey_id"],
            },
        ),
        Tool(
            name="reject_site_visit",
            description="Reject a site visit (survey) record.",
            inputSchema={
                "type": "object",
                "properties": {
                    "survey_id": {"type": "integer", "description": "Survey ID to reject"},
                    "reason": {"type": "string", "description": "Reason for rejection"},
                },
                "required": ["survey_id", "reason"],
            },
        ),
        Tool(
            name="get_pending_validations",
            description="Get list of records pending validation.",
            inputSchema={
                "type": "object",
                "properties": {
                    "page": {"type": "integer", "default": 1},
                    "page_size": {"type": "integer", "default": 20},
                    "type": {
                        "type": "string",
                        "enum": ["survey", "taxon", "site"],
                        "description": "Type of records to list",
                    },
                    "taxon_group": {"type": "integer", "description": "Filter by taxon group"},
                },
            },
        ),
        Tool(
            name="bulk_validate",
            description="Validate multiple records at once.",
            inputSchema={
                "type": "object",
                "properties": {
                    "survey_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of survey IDs to validate",
                    },
                    "comment": {"type": "string", "description": "Optional bulk validation comment"},
                },
                "required": ["survey_ids"],
            },
        ),
        Tool(
            name="bulk_reject",
            description="Reject multiple records at once.",
            inputSchema={
                "type": "object",
                "properties": {
                    "survey_ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of survey IDs to reject",
                    },
                    "reason": {"type": "string", "description": "Reason for rejection"},
                },
                "required": ["survey_ids", "reason"],
            },
        ),
        Tool(
            name="validate_taxon",
            description="Validate a taxon record.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon_id": {"type": "integer", "description": "Taxon ID to validate"},
                    "comment": {"type": "string", "description": "Optional validation comment"},
                },
                "required": ["taxon_id"],
            },
        ),
        Tool(
            name="reject_taxon",
            description="Reject a taxon record.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon_id": {"type": "integer", "description": "Taxon ID to reject"},
                    "reason": {"type": "string", "description": "Reason for rejection"},
                },
                "required": ["taxon_id", "reason"],
            },
        ),
        Tool(
            name="get_validation_summary",
            description="Get summary of validation status across the system.",
            inputSchema={
                "type": "object",
                "properties": {
                    "taxon_group": {"type": "integer", "description": "Filter by taxon group"},
                },
            },
        ),
    ]


async def handle_tool(client: BimsClient, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    """Handle a validation tool call."""

    if name == "validate_site_visit":
        survey_id = arguments["survey_id"]
        data = {"comment": arguments.get("comment", "")}
        return await client.post(f"surveys/{survey_id}/validate/", data)

    elif name == "reject_site_visit":
        survey_id = arguments["survey_id"]
        data = {"reason": arguments["reason"]}
        return await client.post(f"surveys/{survey_id}/reject/", data)

    elif name == "get_pending_validations":
        params = {
            "page": arguments.get("page", 1),
            "page_size": arguments.get("page_size", 20),
            "validated": False,
        }
        if "type" in arguments:
            params["type"] = arguments["type"]
        if "taxon_group" in arguments:
            params["taxon_group"] = arguments["taxon_group"]
        return await client.get("surveys/pending/", params)

    elif name == "bulk_validate":
        data = {
            "survey_ids": arguments["survey_ids"],
            "comment": arguments.get("comment", ""),
        }
        return await client.post("surveys/bulk/validate/", data)

    elif name == "bulk_reject":
        data = {
            "survey_ids": arguments["survey_ids"],
            "reason": arguments["reason"],
        }
        return await client.post("surveys/bulk/reject/", data)

    elif name == "validate_taxon":
        taxon_id = arguments["taxon_id"]
        data = {"comment": arguments.get("comment", "")}
        return await client.post(f"taxa/{taxon_id}/validate/", data)

    elif name == "reject_taxon":
        taxon_id = arguments["taxon_id"]
        data = {"reason": arguments["reason"]}
        return await client.post(f"taxa/{taxon_id}/reject/", data)

    elif name == "get_validation_summary":
        return await client.get("validation/summary/", arguments)

    else:
        raise ValueError(f"Unknown tool: {name}")
