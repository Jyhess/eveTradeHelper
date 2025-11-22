"""
Mock EveRepository for unit tests
"""

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


class MockEveRepository(EveRepository):
    """Mock repository for unit tests"""

    def __init__(self):
        self.market_groups_list = []
        self.market_groups_details = {}
        self.market_orders = {}
        self.item_types = {}
        self.system_details = {}
        self.region_details = {}
        self.constellation_details = {}
        self.station_details = {}
        self.route_with_details = {}
        self.routes = {}
        self.stargate_details = {}
        self.system_connections = {}
        self.regions_list = []
        # IDs that should raise BadRequestError when accessed
        self.invalid_station_ids = set()

    async def get_market_groups_list(self) -> list[int]:
        return self.market_groups_list

    async def get_market_group_details(self, group_id: int) -> MarketGroupDetails:
        if group_id not in self.market_groups_details:
            raise NotFoundError(f"Market group {group_id} not found")
        return self.market_groups_details[group_id]

    async def get_market_orders(self, region_id: int, type_id: int | None = None) -> list[Order]:
        key = (region_id, type_id)
        return self.market_orders.get(key, [])

    async def get_item_type(self, type_id: int) -> ItemType:
        if type_id not in self.item_types:
            raise NotFoundError(f"Item type {type_id} not found")
        return self.item_types[type_id]

    async def get_regions_list(self) -> list[int]:
        return self.regions_list

    async def get_region_details(self, region_id: int) -> RegionDetails:
        if region_id not in self.region_details:
            raise NotFoundError(f"Region {region_id} not found")
        return self.region_details[region_id]

    async def get_constellation_details(self, constellation_id: int) -> ConstellationDetails:
        if constellation_id not in self.constellation_details:
            raise NotFoundError(f"Constellation {constellation_id} not found")
        return self.constellation_details[constellation_id]

    async def get_system_details(self, system_id: int) -> SystemDetails:
        if system_id not in self.system_details:
            raise NotFoundError(f"System {system_id} not found")
        return self.system_details[system_id]

    async def get_stargate_details(self, stargate_id: int) -> StargateDetails:
        if stargate_id not in self.stargate_details:
            raise NotFoundError(f"Stargate {stargate_id} not found")
        return self.stargate_details[stargate_id]

    async def get_station_details(self, station_id: int) -> StationDetails:
        if station_id in self.invalid_station_ids:
            raise BadRequestError(f"Station {station_id} is invalid")
        if station_id not in self.station_details:
            raise NotFoundError(f"Station {station_id} not found")
        return self.station_details[station_id]

    async def get_route(self, origin: int, destination: int) -> list[int]:
        key = (origin, destination)
        return self.routes.get(key, [])

    async def get_route_with_details(self, origin: int, destination: int) -> list[RouteDetail]:
        key = (origin, destination)
        return self.route_with_details.get(key, [])
