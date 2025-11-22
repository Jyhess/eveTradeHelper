from ..mock_eve_repository import MockEveRepository
from domain.types import (
    ConstellationDetails,
    ItemType,
    Order,
    StargateDetails,
    StationDetails,
    SystemDetails,
)

# Common test data constants
FROM_SYSTEM_ID = 30000142
TO_SYSTEM_ID = 30000143
DETOUR_SYSTEM_ID = 30000144
DESTINATION_SYSTEM_ID = 30000144  # Same as DETOUR_SYSTEM_ID for convenience
FROM_REGION_ID = 10000002
TO_REGION_ID = 10000003
DESTINATION_REGION_ID = 10000004
FROM_CONSTELLATION_ID = 20000001
TO_CONSTELLATION_ID = 20000002
DESTINATION_CONSTELLATION_ID = 20000003
FROM_STATION_ID = 60008494
TO_STATION_ID = 60008495
DETOUR_STATION_ID = 60000004
DESTINATION_STATION_ID = 60000005
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


def add_profitable_deal_to_mock_repository(
    mock_repository: MockEveRepository,
    type_id: int,
    region_id: int = FROM_REGION_ID,
    buy_price: float = 100.0,
    sell_price: float = 110.0,
    volume: float = 1.0,
    buy_location_id: int = FROM_STATION_ID,
    sell_location_id: int = TO_STATION_ID,
    volume_remain: int = 10,
) -> None:
    """
    Helper function to add a profitable deal to mock repository
    Creates both market orders and item type for a profitable deal

    Args:
        mock_repository: The mock repository to add data to
        type_id: The item type ID
        region_id: The region ID (default: FROM_REGION_ID)
        buy_price: Price to buy the item (default: 100.0)
        sell_price: Price to sell the item (default: 110.0)
        volume: Item volume in m³ (default: 1.0)
        buy_location_id: Location ID where to buy (default: FROM_STATION_ID)
        sell_location_id: Location ID where to sell (default: TO_STATION_ID)
        volume_remain: Remaining volume in orders (default: 10)
    """
    # Initialize dictionaries if they don't exist
    if not hasattr(mock_repository, "market_orders") or mock_repository.market_orders is None:
        mock_repository.market_orders = {}
    if not hasattr(mock_repository, "item_types") or mock_repository.item_types is None:
        mock_repository.item_types = {}

    # Add market orders: buy order (someone wants to sell, we can buy) and sell order (someone wants to buy, we can sell)
    orders_key = (region_id, type_id)
    if orders_key not in mock_repository.market_orders:
        mock_repository.market_orders[orders_key] = []

    # Add buy order (is_buy_order=False means someone wants to sell, we can buy)
    mock_repository.market_orders[orders_key].append(
        create_order(
            order_id=len(mock_repository.market_orders[orders_key]) + 1,
            type_id=type_id,
            is_buy_order=False,
            price=buy_price,
            volume_remain=volume_remain,
            volume_total=volume_remain,
            location_id=buy_location_id,
        )
    )

    # Add sell order (is_buy_order=True means someone wants to buy, we can sell)
    mock_repository.market_orders[orders_key].append(
        create_order(
            order_id=len(mock_repository.market_orders[orders_key]) + 1,
            type_id=type_id,
            is_buy_order=True,
            price=sell_price,
            volume_remain=volume_remain,
            volume_total=volume_remain,
            location_id=sell_location_id,
        )
    )

    # Add item type
    mock_repository.item_types[type_id] = create_item_type(
        type_id=type_id, name=f"Item {type_id}", volume=volume
    )


def add_item_type_to_mock_repository(
    mock_repository: MockEveRepository,
    type_id: int,
    name: str | None = None,
    volume: float = 1.0,
    description: str | None = None,
) -> None:
    """
    Helper function to add an item type to mock repository

    Args:
        mock_repository: The mock repository to add data to
        type_id: The item type ID
        name: Item name (default: "Item {type_id}")
        volume: Item volume in m³ (default: 1.0)
        description: Item description (default: None)
    """
    if not hasattr(mock_repository, "item_types") or mock_repository.item_types is None:
        mock_repository.item_types = {}

    mock_repository.item_types[type_id] = create_item_type(
        type_id=type_id, name=name or f"Item {type_id}", volume=volume, description=description
    )

