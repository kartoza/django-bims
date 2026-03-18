#!/usr/bin/env python3
# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Entry point for running the BIMS MCP server.

Usage:
    python -m mcp_bims

Made with love by Kartoza | https://kartoza.com
"""
import asyncio
from mcp_bims.server import main

if __name__ == "__main__":
    asyncio.run(main())
