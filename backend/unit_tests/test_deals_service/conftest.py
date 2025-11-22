import pytest

from ..mock_eve_repository import MockEveRepository
from domain.deals_service import DealsService
from domain.location_validator import LocationValidator
from domain.orders_service import OrdersService
from .utils_function import (
    DESTINATION_CONSTELLATION_ID,
    DESTINATION_REGION_ID,
    DESTINATION_STATION_ID,
    DESTINATION_SYSTEM_ID,
    DETOUR_STATION_ID,
    DETOUR_SYSTEM_ID,
    FROM_CONSTELLATION_ID,
    FROM_REGION_ID,
    FROM_STATION_ID,
    FROM_SYSTEM_ID,
    TO_CONSTELLATION_ID,
    TO_REGION_ID,
    TO_STATION_ID,
    TO_SYSTEM_ID,
    create_constellation_details,
    create_item_type,
    create_order,
    create_station_details,
    create_system_details,
)

# Default type ID for common test data
DEFAULT_TYPE_ID = 587  # A real type ID from static data


@pytest.fixture
def mock_repository():
    """Fixture to create a mock repository with common test data"""
    repo = MockEveRepository()

    # Setup common system details
    repo.system_details = {
        FROM_SYSTEM_ID: create_system_details(
            system_id=FROM_SYSTEM_ID,
            name="From System",
            constellation_id=FROM_CONSTELLATION_ID,
        ),
        TO_SYSTEM_ID: create_system_details(
            system_id=TO_SYSTEM_ID,
            name="To System",
            constellation_id=TO_CONSTELLATION_ID,
        ),
        DETOUR_SYSTEM_ID: create_system_details(
            system_id=DETOUR_SYSTEM_ID,
            name="Detour System",
            constellation_id=FROM_CONSTELLATION_ID,
        ),
    }

    # Setup common constellation details
    repo.constellation_details = {
        FROM_CONSTELLATION_ID: create_constellation_details(
            constellation_id=FROM_CONSTELLATION_ID, region_id=FROM_REGION_ID
        ),
        TO_CONSTELLATION_ID: create_constellation_details(
            constellation_id=TO_CONSTELLATION_ID, region_id=TO_REGION_ID
        ),
        DESTINATION_CONSTELLATION_ID: create_constellation_details(
            constellation_id=DESTINATION_CONSTELLATION_ID, region_id=DESTINATION_REGION_ID
        ),
    }

    # Setup common station details
    repo.station_details = {
        FROM_STATION_ID: create_station_details(
            station_id=FROM_STATION_ID,
            system_id=FROM_SYSTEM_ID,
            name="From Station",
        ),
        TO_STATION_ID: create_station_details(
            station_id=TO_STATION_ID,
            system_id=TO_SYSTEM_ID,
            name="To Station",
        ),
        DETOUR_STATION_ID: create_station_details(
            station_id=DETOUR_STATION_ID,
            system_id=DETOUR_SYSTEM_ID,
            name="Detour Station",
        ),
        DESTINATION_STATION_ID: create_station_details(
            station_id=DESTINATION_STATION_ID,
            system_id=TO_SYSTEM_ID,
            name="Destination Station",
        ),
    }

    # Common route: direct connection between FROM and TO systems
    repo.routes = {(FROM_SYSTEM_ID, TO_SYSTEM_ID): [FROM_SYSTEM_ID, TO_SYSTEM_ID]}

    # Setup common item type
    repo.item_types = {
        DEFAULT_TYPE_ID: create_item_type(
            type_id=DEFAULT_TYPE_ID, name=f"Item {DEFAULT_TYPE_ID}", volume=1.0
        )
    }

    # Setup common market orders: profitable deal in FROM region
    repo.market_orders = {
        (FROM_REGION_ID, DEFAULT_TYPE_ID): [
            create_order(
                order_id=1,
                type_id=DEFAULT_TYPE_ID,
                is_buy_order=False,  # Someone wants to sell, we can buy
                price=100.0,
                volume_remain=10,
                volume_total=10,
                location_id=FROM_STATION_ID,
            ),
            create_order(
                order_id=2,
                type_id=DEFAULT_TYPE_ID,
                is_buy_order=True,  # Someone wants to buy, we can sell
                price=110.0,
                volume_remain=10,
                volume_total=10,
                location_id=FROM_STATION_ID,
            ),
        ],
        (TO_REGION_ID, DEFAULT_TYPE_ID): [
            create_order(
                order_id=3,
                type_id=DEFAULT_TYPE_ID,
                is_buy_order=True,  # Someone wants to buy, we can sell
                price=110.0,
                volume_remain=10,
                volume_total=10,
                location_id=TO_STATION_ID,
            ),
        ],
    }

    return repo


@pytest.fixture
def deals_service(mock_repository, local_data_repository, cache):
    """Fixture to create a DealsService with a mock repository"""
    location_validator = LocationValidator(local_data_repository, mock_repository)
    orders_service = OrdersService(mock_repository, location_validator, cache)
    return DealsService(mock_repository, location_validator, orders_service, local_data_repository)

