import logging
from typing import Any

from domain.repository import EveRepository
from repositories.local_data import LocalDataRepository
from utils.cache import cached

from .eve_api_client import EveAPIClient
from .exceptions import BadRequestError, NotFoundError

logger = logging.getLogger(__name__)


class EveRepositoryImpl(EveRepository):
    def __init__(
        self, api_client: EveAPIClient, local_data_repository: LocalDataRepository | None = None
    ):
        self.api_client = api_client
        self.local_data_repository = local_data_repository

    async def close(self):
        await self.api_client.close()

    @cached()
    async def get_regions_list(self) -> list[int]:
        result = await self.api_client.get("/universe/regions/")
        return result if isinstance(result, list) else []

    @cached()
    async def get_region_details(self, region_id: int) -> dict[str, Any]:
        return await self.api_client.get(f"/universe/regions/{region_id}/")

    @cached()
    async def get_constellation_details(self, constellation_id: int) -> dict[str, Any]:
        return await self.api_client.get(f"/universe/constellations/{constellation_id}/")

    @cached()
    async def get_system_details(self, system_id: int) -> dict[str, Any]:
        return await self.api_client.get(f"/universe/systems/{system_id}/")

    @cached()
    async def get_item_type(self, type_id: int) -> dict[str, Any]:
        return await self.api_client.get(f"/universe/types/{type_id}/")

    @cached()
    async def get_stargate_details(self, stargate_id: int) -> dict[str, Any]:
        return await self.api_client.get(f"/universe/stargates/{stargate_id}/")

    @cached()
    async def get_station_details(self, station_id: int) -> dict[str, Any]:
        try:
            return await self.api_client.get(f"/universe/stations/{station_id}/")
        except (BadRequestError, NotFoundError):
            if self.local_data_repository:
                self.local_data_repository.mark_location_id_as_invalid(station_id)
            raise

    @cached()
    async def get_market_groups_list(self) -> list[int]:
        result = await self.api_client.get("/markets/groups/")
        return result if isinstance(result, list) else []

    @cached()
    async def get_market_group_details(self, group_id: int) -> dict[str, Any]:
        return await self.api_client.get(f"/markets/groups/{group_id}/")

    async def get_market_orders(
        self, region_id: int, type_id: int | None = None
    ) -> list[dict[str, Any]]:
        params = {}
        if type_id:
            params["type_id"] = type_id
        result = await self.api_client.get(f"/markets/{region_id}/orders/", params=params)
        return result if isinstance(result, list) else []

    @cached()
    async def get_route(self, origin: int, destination: int) -> list[int]:
        try:
            route = await self.api_client.get(f"/route/{origin}/{destination}/")
            return route if isinstance(route, list) else []
        except Exception as e:
            logger.warning(f"Error calculating route between {origin} and {destination}: {e}")
            return []

    async def get_route_with_details(self, origin: int, destination: int) -> list[dict[str, Any]]:
        import asyncio

        route_ids = await self.get_route(origin, destination)

        if not route_ids:
            return []

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

        results = await asyncio.gather(*[fetch_system_details(sid) for sid in route_ids])

        return results
