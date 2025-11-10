"""
Eve repository implementation using EveAPIClient (async version)
"""

import logging
from typing import Any

from domain.repository import EveRepository
from utils.cache import cached

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

    @cached()
    async def get_regions_list(self) -> list[int]:
        """Retrieves the list of region IDs"""
        result = await self.api_client.get("/universe/regions/")
        return result if isinstance(result, list) else []

    @cached()
    async def get_region_details(self, region_id: int) -> dict[str, Any]:
        """Retrieves region details"""
        return await self.api_client.get(f"/universe/regions/{region_id}/")

    @cached()
    async def get_constellation_details(self, constellation_id: int) -> dict[str, Any]:
        """Retrieves constellation details"""
        return await self.api_client.get(f"/universe/constellations/{constellation_id}/")

    @cached()
    async def get_system_details(self, system_id: int) -> dict[str, Any]:
        """Retrieves solar system details"""
        return await self.api_client.get(f"/universe/systems/{system_id}/")

    @cached()
    async def get_item_type(self, type_id: int) -> dict[str, Any]:
        """Retrieves item type information"""
        return await self.api_client.get(f"/universe/types/{type_id}/")

    @cached()
    async def get_stargate_details(self, stargate_id: int) -> dict[str, Any]:
        """Retrieves stargate details"""
        return await self.api_client.get(f"/universe/stargates/{stargate_id}/")

    @cached()
    async def get_station_details(self, station_id: int) -> dict[str, Any]:
        """Retrieves station details"""
        return await self.api_client.get(f"/universe/stations/{station_id}/")

    @cached()
    async def get_market_groups_list(self) -> list[int]:
        """Retrieves the list of market group IDs"""
        result = await self.api_client.get("/markets/groups/")
        return result if isinstance(result, list) else []

    @cached()
    async def get_market_group_details(self, group_id: int) -> dict[str, Any]:
        """Retrieves market group details"""
        return await self.api_client.get(f"/markets/groups/{group_id}/")

    @cached(expiry_hours=1)
    async def get_market_orders(
        self, region_id: int, type_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Retrieves market orders for a region, optionally filtered by type"""
        params = {}
        if type_id:
            params["type_id"] = type_id
        result = await self.api_client.get(f"/markets/{region_id}/orders/", params=params)
        return result if isinstance(result, list) else []

    @cached()
    async def get_route(self, origin: int, destination: int) -> list[int]:
        """Calculates the route between two systems"""
        try:
            route = await self.api_client.get(f"/route/{origin}/{destination}/")
            return route if isinstance(route, list) else []
        except Exception as e:
            logger.warning(f"Error calculating route between {origin} and {destination}: {e}")
            return []

    async def get_route_with_details(self, origin: int, destination: int) -> list[dict[str, Any]]:
        """Calculates the route between two systems with security details"""
        import asyncio

        # Get the list of system IDs for the route
        route_ids = await self.get_route(origin, destination)

        if not route_ids:
            return []

        # Fetch details of each system in parallel
        async def fetch_system_details(system_id: int) -> dict[str, Any]:
            try:
                system_data = await self.get_system_details(system_id)
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
