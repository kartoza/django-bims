#!/usr/bin/env python3
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
BIMS MCP Server - Model Context Protocol server for BIMS.

This server exposes BIMS functionality to AI assistants through MCP.

Made with love by Kartoza | https://kartoza.com
GitHub: https://github.com/kartoza/django-bims
"""
import asyncio
import logging
from typing import Any, Sequence

from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    ResourceTemplate,
    Tool,
    TextContent,
    EmbeddedResource,
    ServerCapabilities,
    ToolsCapability,
    ResourcesCapability,
)

from mcp_bims.config import BimsConfig, MCPConfig
from mcp_bims.clients import BimsClient
from mcp_bims.tools import (
    location_sites,
    biological_records,
    taxonomy,
    analytics,
    validation,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server
server = Server("bims-mcp-server")

# Global client instance
_client: BimsClient | None = None


async def get_client() -> BimsClient:
    """Get or create the BIMS API client."""
    global _client
    if _client is None:
        config = BimsConfig()
        _client = BimsClient(config)
    return _client


# ============================================================================
# Resource Handlers
# ============================================================================

@server.list_resources()
async def list_resources() -> list[Resource]:
    """List available static resources."""
    return [
        Resource(
            uri="bims://modules",
            name="BIMS Modules",
            description="Available taxon modules/groups in BIMS",
            mimeType="application/json",
        ),
        Resource(
            uri="bims://conservation-statuses",
            name="Conservation Statuses",
            description="IUCN conservation status categories",
            mimeType="application/json",
        ),
        Resource(
            uri="bims://ecosystem-types",
            name="Ecosystem Types",
            description="Available ecosystem types",
            mimeType="application/json",
        ),
    ]


@server.list_resource_templates()
async def list_resource_templates() -> list[ResourceTemplate]:
    """List dynamic resource templates."""
    return [
        ResourceTemplate(
            uriTemplate="bims://site/{site_id}",
            name="Location Site",
            description="Get details for a specific location site",
            mimeType="application/json",
        ),
        ResourceTemplate(
            uriTemplate="bims://taxon/{taxon_id}",
            name="Taxon",
            description="Get details for a specific taxon",
            mimeType="application/json",
        ),
        ResourceTemplate(
            uriTemplate="bims://record/{record_id}",
            name="Biological Record",
            description="Get details for a specific biological collection record",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """Read a resource by URI."""
    import json

    client = await get_client()

    # Static resources
    if uri == "bims://modules":
        result = await client.list_taxon_groups()
        return json.dumps(result.get("data", []), indent=2)

    elif uri == "bims://conservation-statuses":
        # Return standard IUCN categories
        statuses = [
            {"code": "LC", "name": "Least Concern", "order": 1},
            {"code": "NT", "name": "Near Threatened", "order": 2},
            {"code": "VU", "name": "Vulnerable", "order": 3},
            {"code": "EN", "name": "Endangered", "order": 4},
            {"code": "CR", "name": "Critically Endangered", "order": 5},
            {"code": "EW", "name": "Extinct in the Wild", "order": 6},
            {"code": "EX", "name": "Extinct", "order": 7},
            {"code": "DD", "name": "Data Deficient", "order": 8},
            {"code": "NE", "name": "Not Evaluated", "order": 9},
        ]
        return json.dumps(statuses, indent=2)

    elif uri == "bims://ecosystem-types":
        ecosystems = [
            "river",
            "wetland",
            "estuary",
            "dam",
            "lake",
            "coastal",
            "marine",
        ]
        return json.dumps(ecosystems, indent=2)

    # Dynamic resources
    elif uri.startswith("bims://site/"):
        site_id = int(uri.split("/")[-1])
        result = await client.get_site(site_id)
        return json.dumps(result.get("data", {}), indent=2)

    elif uri.startswith("bims://taxon/"):
        taxon_id = int(uri.split("/")[-1])
        result = await client.get_taxon(taxon_id)
        return json.dumps(result.get("data", {}), indent=2)

    elif uri.startswith("bims://record/"):
        record_id = int(uri.split("/")[-1])
        result = await client.get_record(record_id)
        return json.dumps(result.get("data", {}), indent=2)

    else:
        raise ValueError(f"Unknown resource URI: {uri}")


# ============================================================================
# Tool Handlers
# ============================================================================

@server.list_tools()
async def list_tools() -> list[Tool]:
    """List all available tools."""
    tools = []

    # Location Sites tools
    tools.extend(location_sites.get_tools())

    # Biological Records tools
    tools.extend(biological_records.get_tools())

    # Taxonomy tools
    tools.extend(taxonomy.get_tools())

    # Analytics tools
    tools.extend(analytics.get_tools())

    # Validation tools
    tools.extend(validation.get_tools())

    return tools


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> Sequence[TextContent | EmbeddedResource]:
    """Execute a tool by name."""
    import json

    client = await get_client()

    try:
        # Route to appropriate handler
        if name.startswith("list_") or name.startswith("get_") or name.startswith("search_") or name.startswith("find_"):
            # Read operations
            if name in location_sites.TOOLS:
                result = await location_sites.handle_tool(client, name, arguments)
            elif name in biological_records.TOOLS:
                result = await biological_records.handle_tool(client, name, arguments)
            elif name in taxonomy.TOOLS:
                result = await taxonomy.handle_tool(client, name, arguments)
            elif name in analytics.TOOLS:
                result = await analytics.handle_tool(client, name, arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

        elif name.startswith("validate_") or name.startswith("reject_") or name.startswith("bulk_"):
            # Validation operations
            result = await validation.handle_tool(client, name, arguments)

        elif name.startswith("create_") or name.startswith("merge_"):
            # Write operations
            if name in location_sites.TOOLS:
                result = await location_sites.handle_tool(client, name, arguments)
            else:
                raise ValueError(f"Unknown tool: {name}")

        elif name.startswith("request_") or name.startswith("download_"):
            # Export operations
            result = await analytics.handle_tool(client, name, arguments)

        else:
            raise ValueError(f"Unknown tool: {name}")

        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    except Exception as e:
        logger.error(f"Tool {name} failed: {e}")
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


# ============================================================================
# Server Entry Point
# ============================================================================

async def main():
    """Run the MCP server."""
    logger.info("Starting BIMS MCP Server...")

    mcp_config = MCPConfig()

    # Define server capabilities
    capabilities = ServerCapabilities(
        tools=ToolsCapability(),
        resources=ResourcesCapability(subscribe=False, listChanged=False),
    )

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name=mcp_config.name,
                server_version=mcp_config.version,
                capabilities=capabilities,
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
