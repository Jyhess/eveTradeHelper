"""
Eve repository implementation using EveAPIClient (async version)
"""

import logging
from typing import Any

from domain.repository import EveRepository

from .eve_api_client import EveAPIClient

logger = logging.getLogger(__name__)


class EveRepositoryImpl(EveRepository):
    """Concrete Eve repository implementation using the API client (async)"""

    def __init__(self, api_client: EveAPIClient):
        """
        Initialize the repository with an API client

        Args:
            api_client: EveAPIClient instance
        """
        self.api_client = api_client

    async def close(self):
        await self.api_client.close()

    async def get_regions_list(self) -> list[int]:
        """Retrieves the list of region IDs"""
        return await self.api_client.get_regions_list()

    async def get_region_details(self, region_id: int) -> dict[str, Any]:
        """Retrieves region details"""
        return await self.api_client.get_region_details(region_id)

    async def get_constellation_details(self, constellation_id: int) -> dict[str, Any]:
        """Retrieves constellation details"""
        return await self.api_client.get_constellation_details(constellation_id)

    async def get_system_details(self, system_id: int) -> dict[str, Any]:
        """Retrieves solar system details"""
        return await self.api_client.get_system_details(system_id)

    async def get_item_type(self, type_id: int) -> dict[str, Any]:
        """Retrieves item type information"""
        return await self.api_client.get_item_type(type_id)

    async def get_stargate_details(self, stargate_id: int) -> dict[str, Any]:
        """Retrieves stargate details"""
        return await self.api_client.get_stargate_details(stargate_id)

    async def get_station_details(self, station_id: int) -> dict[str, Any]:
        """Retrieves station details"""
        return await self.api_client.get_station_details(station_id)

    async def get_market_groups_list(self) -> list[int]:
        """Retrieves the list of market group IDs"""
        return await self.api_client.get_market_groups_list()

    async def get_market_group_details(self, group_id: int) -> dict[str, Any]:
        """Retrieves market group details"""
        return await self.api_client.get_market_group_details(group_id)

    async def get_market_orders(
        self, region_id: int, type_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Retrieves market orders for a region, optionally filtered by type"""
        return await self.api_client.get_market_orders(region_id, type_id)

    async def get_route(self, origin: int, destination: int) -> list[int]:
        """Calculates the route between two systems"""
        return await self.api_client.get_route(origin, destination)

    async def get_route_with_details(self, origin: int, destination: int) -> list[dict[str, Any]]:
        """Calculates the route between two systems with security details"""
        import asyncio

        # Get the list of system IDs for the route
        route_ids = await self.api_client.get_route(origin, destination)

        if not route_ids:
            return []

        # Fetch details of each system in parallel
        async def fetch_system_details(system_id: int) -> dict[str, Any]:
            try:
                system_data = await self.api_client.get_system_details(system_id)
                return {
                    "system_id": system_id,
                    "name": system_data.get("name", f"System {system_id}"),
                    "security_status": system_data.get("security_status", 0.0),
                }
            except Exception as e:
                logger.warning(f"Error retrieving system {system_id}: {e}")
                return {
                    "system_id": system_id,
                    "name": f"System {system_id}",
                    "security_status": 0.0,
                }

        # Fetch all details in parallel
        results = await asyncio.gather(*[fetch_system_details(sid) for sid in route_ids])

        return results
