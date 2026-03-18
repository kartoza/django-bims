# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Token management for BIMS API authentication.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional

import httpx

from mcp_bims.config import BimsConfig

logger = logging.getLogger(__name__)


class TokenManager:
    """
    Manages API tokens for BIMS authentication.

    Supports both pre-configured API tokens and session-based authentication.
    """

    def __init__(self, config: BimsConfig):
        self.config = config
        self._token: Optional[str] = config.api_token
        self._csrf_token: Optional[str] = None
        self._session_id: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._lock = asyncio.Lock()

    @property
    def is_authenticated(self) -> bool:
        """Check if we have valid authentication."""
        if self._token:
            return True
        if self._session_id:
            return self._token_expiry is None or datetime.now() < self._token_expiry
        return False

    async def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests."""
        async with self._lock:
            if not self.is_authenticated:
                await self._authenticate()

            headers = {}

            if self._token:
                headers["Authorization"] = f"Token {self._token}"

            if self._csrf_token:
                headers["X-CSRFToken"] = self._csrf_token

            return headers

    async def _authenticate(self) -> None:
        """Authenticate with the BIMS API."""
        if self._token:
            # Already have a static token
            return

        if not self.config.username or not self.config.password:
            raise ValueError(
                "No API token provided and username/password not configured. "
                "Set BIMS_API_TOKEN or BIMS_USERNAME and BIMS_PASSWORD environment variables."
            )

        logger.info("Authenticating with BIMS API...")

        async with httpx.AsyncClient(timeout=self.config.timeout) as client:
            # Get CSRF token first
            login_page_url = f"{self.config.base_url}/accounts/login/"
            response = await client.get(login_page_url)

            if "csrftoken" in response.cookies:
                self._csrf_token = response.cookies["csrftoken"]

            # Perform login
            login_data = {
                "login": self.config.username,
                "password": self.config.password,
            }

            headers = {}
            if self._csrf_token:
                headers["X-CSRFToken"] = self._csrf_token

            response = await client.post(
                login_page_url,
                data=login_data,
                headers=headers,
                follow_redirects=True,
            )

            if response.status_code != 200:
                raise ValueError(f"Authentication failed: {response.status_code}")

            # Extract session ID
            if "sessionid" in response.cookies:
                self._session_id = response.cookies["sessionid"]
                self._token_expiry = datetime.now() + timedelta(hours=12)
                logger.info("Successfully authenticated with BIMS API")
            else:
                raise ValueError("Authentication failed: No session cookie received")

    async def get_cookies(self) -> dict[str, str]:
        """Get cookies for API requests."""
        cookies = {}

        if self._session_id:
            cookies["sessionid"] = self._session_id

        if self._csrf_token:
            cookies["csrftoken"] = self._csrf_token

        return cookies

    async def refresh(self) -> None:
        """Force refresh authentication."""
        async with self._lock:
            self._session_id = None
            self._token_expiry = None
            await self._authenticate()

    def clear(self) -> None:
        """Clear all authentication state."""
        self._token = None
        self._csrf_token = None
        self._session_id = None
        self._token_expiry = None
