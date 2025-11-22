from domain.eve_repository import EveRepository
from domain.types import (
    ConstellationDetails,
    ItemType,
    MarketGroupDetails,
    Order,
    RegionDetails,
    RouteDetail,
    StationDetails,
    SystemDetails,
    StargateDetails,
)


class MockRepository(EveRepository):
    """Mock repository for unit tests"""

    def __init__(self):
        self.market_groups_list = []
        self.market_groups_details = {}
        self.market_orders = {}
        self.station_details = {}
        self.system_details = {}
        self.item_types = {}
        self._regions_list = []
        self._region_details = {}

    async def get_market_groups_list(self) -> list[int]:
        return self.market_groups_list

    async def get_market_group_details(self, group_id: int) -> MarketGroupDetails:
        group_data = self.market_groups_details.get(group_id, {})
        if isinstance(group_data, dict):
            return MarketGroupDetails.from_dict(group_data)
        return group_data

    async def get_market_orders(self, region_id: int, type_id: int | None = None) -> list[Order]:
        key = (region_id, type_id)
        orders_data = self.market_orders.get(key, [])
        # Convert dictionaries to Order objects
        return [
            Order.from_dict(order_data) if isinstance(order_data, dict) else order_data
            for order_data in orders_data
        ]

    async def get_station_details(self, station_id: int) -> StationDetails:
        station_data = self.station_details.get(station_id, {})
        if isinstance(station_data, dict):
            return StationDetails.from_dict(station_data)
        return station_data

    async def get_system_details(self, system_id: int) -> SystemDetails:
        system_data = self.system_details.get(system_id, {})
        if isinstance(system_data, dict):
            return SystemDetails.from_dict(system_data)
        return system_data

    # Other methods required by interface but not used in these tests
    async def get_regions_list(self) -> list[int]:
        return getattr(self, "_regions_list", [])

    async def get_region_details(self, region_id: int) -> RegionDetails:
        region_data = self._region_details.get(region_id, {})
        if isinstance(region_data, dict):
            return RegionDetails.from_dict(region_data)
        return region_data

    async def get_constellation_details(self, constellation_id: int) -> ConstellationDetails:
        raise NotImplementedError

    async def get_stargate_details(self, stargate_id: int) -> StargateDetails:
        raise NotImplementedError

    async def get_item_type(self, type_id: int) -> ItemType:
        item_data = self.item_types.get(type_id, {})
        if isinstance(item_data, dict):
            return ItemType.from_dict(item_data)
        return item_data

    async def get_route(self, origin: int, destination: int) -> list[int]:
        return []

    async def get_route_with_details(self, origin: int, destination: int) -> list[RouteDetail]:
        return []


class FakeLocalDataRepository:
    """Fake local data repository for type search tests"""

    def __init__(self):
        self.types = [
            {"type_id": 34, "name": "Tritanium"},
            {"type_id": 35, "name": "Pyerite"},
            {"type_id": 1234, "name": "Advanced Tritanium"},
        ]

    def search_types(self, query: str | None, limit: int = 20):
        if query is None or not query.strip():
            return self.types[:limit]
        query_lower = query.lower()
        matches = [t for t in self.types if query_lower in t["name"].lower()]
        return matches[:limit]

