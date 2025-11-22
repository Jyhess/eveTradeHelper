from domain.deals_service import DealsService
from domain.location_validator import LocationValidator
from domain.orders_service import OrdersService
from domain.repository import EveRepository
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

class MockRepository(EveRepository):
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

    async def get_market_groups_list(self) -> list[int]:
        return self.market_groups_list

    async def get_market_group_details(self, group_id: int) -> MarketGroupDetails:
        group_data = self.market_groups_details.get(group_id)
        if group_data is None:
            return MarketGroupDetails(
                market_group_id=group_id,
                name=f"Group {group_id}",
                description="",
                parent_group_id=None,
                types=[],
                icon_id=None,
            )
        if isinstance(group_data, MarketGroupDetails):
            return group_data
        if isinstance(group_data, dict):
            complete_data = {
                "market_group_id": group_id,
                "name": group_data.get("name", f"Group {group_id}"),
                "description": group_data.get("description", ""),
                "parent_group_id": group_data.get("parent_group_id"),
                "types": group_data.get("types", []),
                "icon_id": group_data.get("icon_id"),
            }
            return MarketGroupDetails.from_dict(complete_data)
        return group_data

    async def get_market_orders(self, region_id: int, type_id: int | None = None) -> list[Order]:
        key = (region_id, type_id)
        orders_data = self.market_orders.get(key, [])
        return [
            Order.from_dict(order_data) if isinstance(order_data, dict) else order_data
            for order_data in orders_data
        ]

    async def get_item_type(self, type_id: int) -> ItemType:
        item_data = self.item_types.get(type_id)
        if item_data is None:
            return create_item_type(type_id=type_id, name=f"Type {type_id}")
        if isinstance(item_data, ItemType):
            return item_data
        if isinstance(item_data, dict):
            complete_data = {
                "type_id": type_id,
                "name": item_data.get("name", f"Type {type_id}"),
                "volume": item_data.get("volume", 0.0),
                "description": item_data.get("description"),
                "group_id": item_data.get("group_id"),
                "category_id": item_data.get("category_id"),
                "market_group_id": item_data.get("market_group_id"),
            }
            return ItemType.from_dict(complete_data)
        return item_data

    async def get_regions_list(self) -> list[int]:
        return []

    async def get_region_details(self, region_id: int) -> RegionDetails:
        region_data = self.region_details.get(region_id)
        if region_data is None:
            return RegionDetails(
                region_id=region_id,
                name=f"Region {region_id}",
                description="",
                constellations=[],
            )
        if isinstance(region_data, RegionDetails):
            return region_data
        if isinstance(region_data, dict):
            complete_data = {
                "region_id": region_id,
                "name": region_data.get("name", f"Region {region_id}"),
                "description": region_data.get("description", ""),
                "constellations": region_data.get("constellations", []),
            }
            return RegionDetails.from_dict(complete_data)
        return region_data

    async def get_constellation_details(self, constellation_id: int) -> ConstellationDetails:
        constellation_data = self.constellation_details.get(constellation_id)
        if constellation_data is None:
            return create_constellation_details(constellation_id=constellation_id)
        if isinstance(constellation_data, ConstellationDetails):
            return constellation_data
        if isinstance(constellation_data, dict):
            complete_data = {
                "constellation_id": constellation_id,
                "name": constellation_data.get("name", f"Constellation {constellation_id}"),
                "systems": constellation_data.get("systems", []),
                "position": constellation_data.get("position", {}),
                "region_id": constellation_data.get("region_id"),
            }
            return ConstellationDetails.from_dict(complete_data)
        return constellation_data

    async def get_system_details(self, system_id: int) -> SystemDetails:
        system_data = self.system_details.get(system_id)
        if system_data is None:
            return create_system_details(system_id=system_id)
        if isinstance(system_data, SystemDetails):
            if system_id in self.system_connections:
                return SystemDetails(
                    system_id=system_data.system_id,
                    name=system_data.name,
                    security_status=system_data.security_status,
                    security_class=system_data.security_class,
                    position=system_data.position,
                    constellation_id=system_data.constellation_id,
                    planets=system_data.planets,
                    star_id=system_data.star_id,
                    stargates=self.system_connections[system_id],
                )
            return system_data
        if isinstance(system_data, dict):
            system_data = system_data.copy()
            if system_id in self.system_connections:
                system_data["stargates"] = self.system_connections[system_id]
            complete_data = {
                "system_id": system_id,
                "name": system_data.get("name", f"System {system_id}"),
                "security_status": system_data.get("security_status", 0.0),
                "security_class": system_data.get("security_class", ""),
                "position": system_data.get("position", {}),
                "constellation_id": system_data.get("constellation_id"),
                "planets": system_data.get("planets", []),
                "star_id": system_data.get("star_id"),
                "stargates": system_data.get("stargates"),
            }
            return SystemDetails.from_dict(complete_data)
        return system_data

    async def get_stargate_details(self, stargate_id: int) -> StargateDetails:
        stargate_data = self.stargate_details.get(stargate_id)
        if stargate_data is None:
            return create_stargate_details(stargate_id=stargate_id)
        if isinstance(stargate_data, StargateDetails):
            return stargate_data
        if isinstance(stargate_data, dict):
            complete_data = {
                "stargate_id": stargate_id,
                "system_id": stargate_data.get("system_id", 0),
                "destination": stargate_data.get("destination", {"system_id": 0}),
                "position": stargate_data.get("position", {}),
                "type_id": stargate_data.get("type_id", 0),
                "name": stargate_data.get("name", f"Stargate {stargate_id}"),
            }
            return StargateDetails.from_dict(complete_data)
        return stargate_data

    async def get_station_details(self, station_id: int) -> StationDetails:
        station_data = self.station_details.get(station_id)
        if station_data is None:
            return create_station_details(station_id=station_id)
        if isinstance(station_data, StationDetails):
            return station_data
        if isinstance(station_data, dict):
            if "station_id" not in station_data:
                station_data = station_data.copy()
                station_data["station_id"] = station_id
            return StationDetails.from_dict(station_data)
        return station_data

    async def get_route(self, origin: int, destination: int) -> list[int]:
        key = (origin, destination)
        return self.routes.get(key, [])

    async def get_route_with_details(self, origin: int, destination: int) -> list[RouteDetail]:
        key = (origin, destination)
        route_data = self.route_with_details.get(key, [])
        return [
            RouteDetail(
                system_id=route_item.get("system_id", 0),
                name=route_item.get("name", "Unknown"),
                security_status=route_item.get("security_status", 0.0),
                faction_id=route_item.get("faction_id"),
            )
            if isinstance(route_item, dict)
            else route_item
            for route_item in route_data
        ]


def create_order(
    order_id: int = 1,
    type_id: int = 123,
    is_buy_order: bool = True,
    price: float = 100.0,
    location_id: int = 30000142,
    volume_remain: int = 1000,
    volume_total: int = 1000,
) -> Order:
    """Helper function to create a complete Order object"""
    return Order(
        order_id=order_id,
        type_id=type_id,
        is_buy_order=is_buy_order,
        price=price,
        location_id=location_id,
        volume_total=volume_total,
        volume_remain=volume_remain,
        min_volume=1,
        duration=90,
        issued="2024-01-01T00:00:00Z",
        range="region",
    )


def create_item_type(
    type_id: int = 123,
    name: str = "Test Item",
    volume: float = 1.0,
    description: str | None = None,
) -> ItemType:
    """Helper function to create an ItemType object"""
    return ItemType(
        type_id=type_id,
        name=name,
        volume=volume,
        description=description,
        group_id=None,
        category_id=None,
        market_group_id=None,
    )


def create_system_details(
    system_id: int = 30000142,
    name: str = "Test System",
    security_status: float = 0.9,
    security_class: str = "B",
    constellation_id: int | None = None,
    stargates: list[int] | None = None,
) -> SystemDetails:
    """Helper function to create a SystemDetails object"""
    return SystemDetails(
        system_id=system_id,
        name=name,
        security_status=security_status,
        security_class=security_class,
        position={},
        constellation_id=constellation_id,
        planets=[],
        star_id=None,
        stargates=stargates,
    )


def create_station_details(
    station_id: int = 60008494,
    name: str = "Test Station",
    system_id: int = 30000142,
) -> StationDetails:
    """Helper function to create a StationDetails object"""
    return StationDetails(
        station_id=station_id,
        name=name,
        system_id=system_id,
        type_id=None,
        position=None,
        owner=None,
        race_id=None,
        reprocessing_efficiency=None,
        reprocessing_stations_take=None,
        max_dockable_ship_volume=None,
        office_rental_cost=None,
        services=None,
    )


def create_constellation_details(
    constellation_id: int = 20000001,
    name: str = "Test Constellation",
    region_id: int | None = None,
    systems: list[int] | None = None,
) -> ConstellationDetails:
    """Helper function to create a ConstellationDetails object"""
    return ConstellationDetails(
        constellation_id=constellation_id,
        name=name,
        systems=systems or [],
        position={},
        region_id=region_id,
    )


def create_stargate_details(
    stargate_id: int = 50000001,
    system_id: int = 30000142,
    destination_system_id: int = 30000143,
    name: str = "Test Stargate",
) -> StargateDetails:
    """Helper function to create a StargateDetails object"""
    return StargateDetails(
        stargate_id=stargate_id,
        system_id=system_id,
        destination_system_id=destination_system_id,
        position={},
        type_id=0,
        name=name,
    )

