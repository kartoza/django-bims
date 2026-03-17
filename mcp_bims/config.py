# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Configuration for the BIMS MCP Server.
"""
import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class BimsConfig:
    """Configuration for connecting to a BIMS instance."""

    # API Configuration
    base_url: str = field(default_factory=lambda: os.getenv("BIMS_BASE_URL", "http://localhost:8000"))
    api_version: str = "v1"
    api_prefix: str = field(init=False)

    # Authentication
    api_token: Optional[str] = field(default_factory=lambda: os.getenv("BIMS_API_TOKEN"))
    username: Optional[str] = field(default_factory=lambda: os.getenv("BIMS_USERNAME"))
    password: Optional[str] = field(default_factory=lambda: os.getenv("BIMS_PASSWORD"))

    # Request settings
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    # Pagination defaults
    default_page_size: int = 20
    max_page_size: int = 100

    def __post_init__(self):
        self.api_prefix = f"/api/{self.api_version}"

    @property
    def api_base_url(self) -> str:
        """Return the full API base URL."""
        return f"{self.base_url.rstrip('/')}{self.api_prefix}"

    def get_endpoint(self, path: str) -> str:
        """Get full URL for an API endpoint."""
        return f"{self.api_base_url}/{path.lstrip('/')}"


@dataclass
class MCPConfig:
    """Configuration for the MCP server."""

    # Server settings
    name: str = "bims-mcp-server"
    version: str = "0.1.0"
    description: str = "MCP server for BIMS - Biodiversity Information Management System"

    # Logging
    log_level: str = field(default_factory=lambda: os.getenv("MCP_LOG_LEVEL", "INFO"))

    # Rate limiting
    rate_limit_requests: int = 100
    rate_limit_window: int = 60  # seconds


# Default configurations
DEFAULT_BIMS_CONFIG = BimsConfig()
DEFAULT_MCP_CONFIG = MCPConfig()
