import logging

from domain.eve_repository import EveRepository
from domain.exceptions import BadRequestError, NotFoundError
from domain.types import (
    ConstellationDetails,
    ItemType,
    MarketGroupDetails,
    Order,
    RegionDetails,
    RouteDetail,
    StargateDetails,
    StationDetails,
    SystemDetails,
)
from repositories import LocalDataRepository
from utils.cache import cached

from .eve_api_client import EveAPIClient

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
    async def get_region_details(self, region_id: int) -> RegionDetails:
        data = await self.api_client.get(f"/universe/regions/{region_id}/")
        return RegionDetails.from_dict(data)

    @cached()
    async def get_constellation_details(self, constellation_id: int) -> ConstellationDetails:
        data = await self.api_client.get(f"/universe/constellations/{constellation_id}/")
        return ConstellationDetails.from_dict(data)

    @cached()
    async def get_system_details(self, system_id: int) -> SystemDetails:
        data = await self.api_client.get(f"/universe/systems/{system_id}/")
        return SystemDetails.from_dict(data)

    @cached()
    async def get_item_type(self, type_id: int) -> ItemType:
        data = await self.api_client.get(f"/universe/types/{type_id}/")
        return ItemType.from_dict(data)

    @cached()
    async def get_stargate_details(self, stargate_id: int) -> StargateDetails:
        data = await self.api_client.get(f"/universe/stargates/{stargate_id}/")
        return StargateDetails.from_dict(data)

    @cached()
    async def get_station_details(self, station_id: int) -> StationDetails:
        try:
            data = await self.api_client.get(f"/universe/stations/{station_id}/")
            return StationDetails.from_dict(data)
        except (BadRequestError, NotFoundError):
            if self.local_data_repository:
                self.local_data_repository.mark_location_id_as_invalid(station_id)
            raise

    @cached()
    async def get_market_groups_list(self) -> list[int]:
        result = await self.api_client.get("/markets/groups/")
        return result if isinstance(result, list) else []

    @cached()
    async def get_market_group_details(self, group_id: int) -> MarketGroupDetails:
        data = await self.api_client.get(f"/markets/groups/{group_id}/")
        return MarketGroupDetails.from_dict(data)

    async def get_market_orders(self, region_id: int, type_id: int | None = None) -> list[Order]:
        params = {}
        if type_id:
            params["type_id"] = type_id
        result = await self.api_client.get(f"/markets/{region_id}/orders/", params=params)
        if not isinstance(result, list):
            return []
        return [Order.from_dict(order_data) for order_data in result]

    @cached()
    async def get_route(self, origin: int, destination: int) -> list[int]:
        try:
            route = await self.api_client.get(f"/route/{origin}/{destination}/")
            return route if isinstance(route, list) else []
        except Exception as e:
            logger.warning(f"Error calculating route between {origin} and {destination}: {e}")
            return []

    async def get_route_with_details(self, origin: int, destination: int) -> list[RouteDetail]:
        import asyncio

        route_ids = await self.get_route(origin, destination)

        if not route_ids:
            return []

        async def fetch_system_details(system_id: int) -> RouteDetail:
            try:
                system_data = await self.get_system_details(system_id)
                faction_id = None

                # Add factionID if available from static data
                if self.local_data_repository:
                    faction_id = self.local_data_repository.get_system_faction_id(system_id)

                return RouteDetail(
                    system_id=system_id,
                    name=system_data.name,
                    security_status=system_data.security_status,
                    faction_id=faction_id,
                )
            except Exception as e:
                logger.warning(f"Error retrieving system {system_id}: {e}")
                faction_id = None
                # Add factionID even if system details failed
                if self.local_data_repository:
                    faction_id = self.local_data_repository.get_system_faction_id(system_id)

                return RouteDetail(
                    system_id=system_id,
                    name=f"System {system_id}",
                    security_status=0.0,
                    faction_id=faction_id,
                )

        results = await asyncio.gather(*[fetch_system_details(sid) for sid in route_ids])

        return results
