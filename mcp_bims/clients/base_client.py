# SPDX-FileCopyrightText: Kartoza
# SPDX-License-Identifier: AGPL-3.0
"""
Base HTTP client for communicating with the BIMS API.
"""
import asyncio
import logging
from typing import Any, Optional

import httpx

from mcp_bims.auth import TokenManager
from mcp_bims.config import BimsConfig

logger = logging.getLogger(__name__)


class BimsClient:
    """
    Async HTTP client for the BIMS API.

    Handles authentication, retries, and response parsing.
    """

    def __init__(self, config: Optional[BimsConfig] = None):
        self.config = config or BimsConfig()
        self.token_manager = TokenManager(self.config)
        self._client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self) -> "BimsClient":
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def _ensure_client(self) -> None:
        """Ensure the HTTP client is initialized."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.config.timeout,
                follow_redirects=True,
            )

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
        retry_count: int = 0,
    ) -> dict[str, Any]:
        """
        Make an authenticated request to the BIMS API.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint path (without base URL)
            params: Query parameters
            json_data: JSON request body
            retry_count: Current retry attempt

        Returns:
            Parsed JSON response
        """
        await self._ensure_client()

        url = self.config.get_endpoint(endpoint)
        headers = await self.token_manager.get_auth_headers()
        cookies = await self.token_manager.get_cookies()

        headers["Accept"] = "application/json"
        headers["Content-Type"] = "application/json"

        try:
            response = await self._client.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                headers=headers,
                cookies=cookies,
            )

            # Handle authentication errors
            if response.status_code == 401:
                if retry_count < self.config.max_retries:
                    logger.info("Authentication expired, refreshing...")
                    await self.token_manager.refresh()
                    return await self._request(
                        method, endpoint, params, json_data, retry_count + 1
                    )
                raise ValueError("Authentication failed after refresh")

            # Handle rate limiting
            if response.status_code == 429:
                if retry_count < self.config.max_retries:
                    retry_after = int(response.headers.get("Retry-After", self.config.retry_delay))
                    logger.warning(f"Rate limited, waiting {retry_after}s...")
                    await asyncio.sleep(retry_after)
                    return await self._request(
                        method, endpoint, params, json_data, retry_count + 1
                    )
                raise ValueError("Rate limited, max retries exceeded")

            # Handle server errors with retry
            if response.status_code >= 500:
                if retry_count < self.config.max_retries:
                    await asyncio.sleep(self.config.retry_delay * (retry_count + 1))
                    return await self._request(
                        method, endpoint, params, json_data, retry_count + 1
                    )
                raise ValueError(f"Server error: {response.status_code}")

            response.raise_for_status()
            return response.json()

        except httpx.RequestError as e:
            if retry_count < self.config.max_retries:
                logger.warning(f"Request failed: {e}, retrying...")
                await asyncio.sleep(self.config.retry_delay)
                return await self._request(
                    method, endpoint, params, json_data, retry_count + 1
                )
            raise

    # Convenience methods for HTTP verbs

    async def get(
        self,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make a GET request."""
        return await self._request("GET", endpoint, params=params)

    async def post(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make a POST request."""
        return await self._request("POST", endpoint, json_data=data)

    async def put(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make a PUT request."""
        return await self._request("PUT", endpoint, json_data=data)

    async def patch(
        self,
        endpoint: str,
        data: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Make a PATCH request."""
        return await self._request("PATCH", endpoint, json_data=data)

    async def delete(self, endpoint: str) -> dict[str, Any]:
        """Make a DELETE request."""
        return await self._request("DELETE", endpoint)

    # Resource-specific methods

    async def list_sites(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        **filters: Any,
    ) -> dict[str, Any]:
        """List location sites with optional filters."""
        params = {
            "page": page,
            "page_size": page_size or self.config.default_page_size,
            **filters,
        }
        return await self.get("sites/", params)

    async def get_site(self, site_id: int) -> dict[str, Any]:
        """Get a single location site."""
        return await self.get(f"sites/{site_id}/")

    async def list_records(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        **filters: Any,
    ) -> dict[str, Any]:
        """List biological collection records with optional filters."""
        params = {
            "page": page,
            "page_size": page_size or self.config.default_page_size,
            **filters,
        }
        return await self.get("records/", params)

    async def get_record(self, record_id: int) -> dict[str, Any]:
        """Get a single biological collection record."""
        return await self.get(f"records/{record_id}/")

    async def search_records(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        **filters: Any,
    ) -> dict[str, Any]:
        """Search biological collection records."""
        params = {
            "page": page,
            "page_size": page_size or self.config.default_page_size,
            **filters,
        }
        return await self.get("records/search/", params)

    async def list_taxa(
        self,
        page: int = 1,
        page_size: Optional[int] = None,
        **filters: Any,
    ) -> dict[str, Any]:
        """List taxonomy records with optional filters."""
        params = {
            "page": page,
            "page_size": page_size or self.config.default_page_size,
            **filters,
        }
        return await self.get("taxa/", params)

    async def get_taxon(self, taxon_id: int) -> dict[str, Any]:
        """Get a single taxonomy record."""
        return await self.get(f"taxa/{taxon_id}/")

    async def find_taxon(self, query: str, rank: Optional[str] = None) -> dict[str, Any]:
        """Find taxon by name."""
        params = {"q": query}
        if rank:
            params["rank"] = rank
        return await self.get("taxa/find/", params)

    async def get_taxon_tree(
        self,
        taxon_id: int,
        direction: str = "down",
        depth: int = 10,
    ) -> dict[str, Any]:
        """Get taxonomy tree for a taxon."""
        params = {"direction": direction, "depth": depth}
        return await self.get(f"taxa/{taxon_id}/tree/", params)

    async def list_taxon_groups(self) -> dict[str, Any]:
        """List all taxon groups."""
        return await self.get("taxon-groups/")

    async def get_module_summary(self) -> dict[str, Any]:
        """Get summary statistics for all modules."""
        return await self.get("sites/summary/")

    async def validate_site(self, site_id: int) -> dict[str, Any]:
        """Validate a location site."""
        return await self.post(f"sites/{site_id}/validate/")

    async def validate_survey(self, survey_id: int) -> dict[str, Any]:
        """Validate a survey and its records."""
        return await self.post(f"surveys/{survey_id}/validate/")

    async def bulk_validate_surveys(self, survey_ids: list[int]) -> dict[str, Any]:
        """Bulk validate multiple surveys."""
        return await self.post("surveys/bulk_validate/", {"survey_ids": survey_ids})

    async def request_download(
        self,
        download_type: str = "csv",
        filters: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Request an async download."""
        if download_type == "csv":
            return await self.post("downloads/csv/", {"filters": filters or {}})
        elif download_type == "checklist":
            return await self.post("downloads/checklist/", filters or {})
        else:
            raise ValueError(f"Unknown download type: {download_type}")

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """Get the status of an async task."""
        return await self.get(f"tasks/{task_id}/")
