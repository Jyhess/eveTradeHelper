"""
Client for Eve Online ESI (Eve Swagger Interface) API
Async version with httpx
"""

import asyncio
import logging
import time
from collections import deque
from typing import Any

import httpx

from domain.constants import DEFAULT_API_MAX_RETRIES, DEFAULT_API_RETRY_DELAY_SECONDS
from utils.cache import cached

logger = logging.getLogger(__name__)


class EveAPIClient:
    """Client to interact with Eve Online ESI API (async)"""

    def __init__(
        self,
        base_url: str = "https://esi.evetech.net/latest",
        timeout: int = 10,
        rate_limit_per_second: int = 60,
    ):
        """
        Initialize the API client

        Args:
            base_url: ESI API base URL
            timeout: Request timeout in seconds
            rate_limit_per_second: Maximum number of requests per second (default: 20)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limit_per_second = rate_limit_per_second
        self._client: httpx.AsyncClient | None = None

        # Rate limiting: keep timestamps of recent requests
        self._request_timestamps: deque = deque()
        self._rate_limit_lock: asyncio.Lock | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Gets or creates an async HTTP client"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Closes the HTTP client"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _wait_for_rate_limit(self):
        """
        Waits if necessary to respect the rate limit
        Uses a 1-second sliding window
        """
        # Initialize lock lazily (necessary because asyncio.Lock() cannot be created outside an event loop)
        if self._rate_limit_lock is None:
            self._rate_limit_lock = asyncio.Lock()

        async with self._rate_limit_lock:
            now = time.time()

            # Remove timestamps older than 1 second
            while self._request_timestamps and self._request_timestamps[0] < now - 1.0:
                self._request_timestamps.popleft()

            # If we've reached the limit, wait until a request exits the window
            if len(self._request_timestamps) >= self.rate_limit_per_second:
                oldest_timestamp = self._request_timestamps[0]
                wait_time = 1.0 - (now - oldest_timestamp)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.time()
                    while self._request_timestamps and self._request_timestamps[0] < now - 1.0:
                        self._request_timestamps.popleft()

            # Add this request's timestamp
            self._request_timestamps.append(time.time())

    def _create_exception_from_httpx_error(self, error: Exception, url: str) -> Exception:
        """
        Creates an appropriate exception from an httpx error

        Args:
            error: httpx exception
            url: Request URL

        Returns:
            Formatted exception
        """
        if isinstance(error, httpx.TimeoutException):
            return Exception(f"Timeout calling API: {url}")
        elif isinstance(error, httpx.HTTPStatusError):
            return Exception(f"HTTP error {error.response.status_code} calling {url}: {error}")
        elif isinstance(error, httpx.RequestError):
            return Exception(f"Connection error to API {url}: {error}")
        else:
            return Exception(f"Unexpected error calling {url}: {error}")

    def _get_error_message(self, error: Exception, url: str) -> str:
        """
        Generates a formatted error message for logging

        Args:
            error: httpx exception
            url: Request URL

        Returns:
            Formatted error message
        """
        if isinstance(error, httpx.TimeoutException):
            return f"Timeout calling {url}"
        elif isinstance(error, httpx.HTTPStatusError):
            return f"HTTP error {error.response.status_code} calling {url}"
        elif isinstance(error, httpx.RequestError):
            return f"Connection error to {url}"
        else:
            return f"Unexpected error calling {url}"

    async def _execute_request_with_retry(
        self, url: str, params: dict | None, max_retries: int
    ) -> dict[str, Any]:
        """
        Executes an HTTP request with automatic retry

        Args:
            url: Complete request URL
            params: Optional request parameters
            max_retries: Maximum number of additional attempts

        Returns:
            API JSON response

        Raises:
            Exception: If the request fails after all attempts
        """
        client = await self._get_client()

        for attempt in range(max_retries + 1):
            try:
                await self._wait_for_rate_limit()
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as e:
                exception = self._create_exception_from_httpx_error(e, url)

                if attempt < max_retries:
                    error_message = self._get_error_message(e, url)
                    logger.warning(
                        f"{error_message} (attempt {attempt + 1}/{max_retries + 1}). Retrying..."
                    )
                    await asyncio.sleep(DEFAULT_API_RETRY_DELAY_SECONDS)
                else:
                    raise exception from None

        raise Exception(f"Unexpected error calling {url}")

    async def _get(
        self,
        endpoint: str,
        params: dict | None = None,
        max_retries: int = DEFAULT_API_MAX_RETRIES,
    ) -> dict[str, Any]:
        """
        Performs a GET request to the API (async)
        Automatically respects the configured rate limit
        Automatically retries on error

        Args:
            endpoint: Endpoint path (e.g., "/universe/regions/")
            params: Optional request parameters
            max_retries: Maximum number of additional attempts on error

        Returns:
            API JSON response

        Raises:
            Exception: If the request fails after all attempts
        """
        url = f"{self.base_url}{endpoint}"
        return await self._execute_request_with_retry(url, params, max_retries)

    @cached()
    async def get_regions_list(self) -> list[int]:
        """
        Retrieves the list of region IDs

        Returns:
            List of region IDs

        Raises:
            Exception: If the API call fails
        """
        result = await self._get("/universe/regions/")
        return result if isinstance(result, list) else []

    @cached()
    async def get_region_details(self, region_id: int) -> dict[str, Any]:
        """
        Retrieves region details

        Args:
            region_id: Region ID

        Returns:
            Dictionary containing region details

        Raises:
            Exception: If the API call fails
        """
        return await self._get(f"/universe/regions/{region_id}/")

    @cached()
    async def get_systems_list(self) -> list[int]:
        """
        Retrieves the list of solar system IDs

        Returns:
            List of system IDs

        Raises:
            Exception: If the API call fails
        """
        result = await self._get("/universe/systems/")
        return result if isinstance(result, list) else []

    @cached()
    async def get_constellation_details(self, constellation_id: int) -> dict[str, Any]:
        """
        Retrieves constellation details

        Args:
            constellation_id: Constellation ID

        Returns:
            Dictionary containing constellation details

        Raises:
            Exception: If the API call fails
        """
        return await self._get(f"/universe/constellations/{constellation_id}/")

    @cached()
    async def get_system_details(self, system_id: int) -> dict[str, Any]:
        """
        Retrieves solar system details

        Args:
            system_id: System ID

        Returns:
            Dictionary containing system details

        Raises:
            Exception: If the API call fails
        """
        return await self._get(f"/universe/systems/{system_id}/")

    @cached()
    async def get_item_type(self, type_id: int) -> dict[str, Any]:
        """
        Retrieves item type information

        Args:
            type_id: Item type ID

        Returns:
            Dictionary containing item information

        Raises:
            Exception: If the API call fails
        """
        return await self._get(f"/universe/types/{type_id}/")

    @cached()
    async def get_stargate_details(self, stargate_id: int) -> dict[str, Any]:
        """
        Retrieves stargate (star gate) details

        Args:
            stargate_id: Stargate ID

        Returns:
            Dictionary containing stargate details

        Raises:
            Exception: If the API call fails
        """
        return await self._get(f"/universe/stargates/{stargate_id}/")

    @cached()
    async def get_station_details(self, station_id: int) -> dict[str, Any]:
        """
        Retrieves station details

        Args:
            station_id: Station ID

        Returns:
            Dictionary containing station details

        Raises:
            Exception: If the API call fails
        """
        return await self._get(f"/universe/stations/{station_id}/")

    @cached()
    async def get_market_groups_list(self) -> list[int]:
        """
        Retrieves the list of market group IDs

        Returns:
            List of market group IDs

        Raises:
            Exception: If the API call fails
        """
        result = await self._get("/markets/groups/")
        return result if isinstance(result, list) else []

    @cached()
    async def get_market_group_details(self, group_id: int) -> dict[str, Any]:
        """
        Retrieves market group details

        Args:
            group_id: Market group ID

        Returns:
            Dictionary containing market group details

        Raises:
            Exception: If the API call fails
        """
        return await self._get(f"/markets/groups/{group_id}/")

    @cached(expiry_hours=1)
    async def get_market_orders(
        self, region_id: int, type_id: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Retrieves market orders for a region, optionally filtered by type

        Args:
            region_id: Region ID
            type_id: Optional, item type ID to filter orders

        Returns:
            List of market orders

        Raises:
            Exception: If the API call fails
        """
        params = {}
        if type_id:
            params["type_id"] = type_id
        result = await self._get(f"/markets/{region_id}/orders/", params=params)
        return result if isinstance(result, list) else []

    @cached()
    async def get_route(
        self,
        origin: int,
        destination: int,
        avoid: list[int] | None = None,
        connections: list[list[int]] | None = None,
    ) -> list[int]:
        """
        Calculates the route between two systems

        Args:
            origin: Origin system ID
            destination: Destination system ID
            avoid: Optional list of system IDs to avoid
            connections: Optional list of connected system pairs

        Returns:
            List of system IDs forming the route (including origin and destination)
            If no route found, returns an empty list

        Raises:
            Exception: If the API call fails
        """
        params = {}
        if avoid:
            # API expects a comma-separated list of IDs for avoid
            params["avoid"] = ",".join(map(str, avoid))
        if connections:
            # For connections, the API expects a special format, but generally not used
            # Could be implemented if necessary
            pass

        try:
            route = await self._get(
                f"/route/{origin}/{destination}/", params=params if params else None
            )
            # API returns a list of system IDs
            return route if isinstance(route, list) else []
        except Exception as e:
            logger.warning(f"Error calculating route between {origin} and {destination}: {e}")
            return []

    @cached()
    async def search(
        self, categories: list[str], search: str, strict: bool = False
    ) -> dict[str, Any]:
        """
        Performs a search in the Eve universe

        Args:
            categories: Search categories (e.g., ["region", "system"])
            search: Search term
            strict: If True, exact search only

        Returns:
            Search results

        Raises:
            Exception: If the API call fails
        """
        params = {
            "categories": ",".join(categories),
            "search": search,
            "strict": str(strict).lower(),
        }
        return await self._get("/search/", params=params)
