"""
Unit tests for OrdersService
"""

import pytest

from domain.location_validator import LocationValidator
from domain.orders_service import OrdersService
from domain.repository import EveRepository


class MockRepository(EveRepository):
    """Mock repository for unit tests"""

    def __init__(self):
        self.market_orders = {}

    async def get_market_orders(
        self, region_id: int, type_id: int | None = None
    ) -> list[dict]:
        key = (region_id, type_id)
        return self.market_orders.get(key, [])

    async def get_regions_list(self) -> list[int]:
        return []

    async def get_region_details(self, region_id: int) -> dict:
        return {}

    async def get_constellation_details(self, constellation_id: int) -> dict:
        return {}

    async def get_system_details(self, system_id: int) -> dict:
        return {}

    async def get_stargate_details(self, stargate_id: int) -> dict:
        return {}

    async def get_station_details(self, station_id: int) -> dict:
        return {}

    async def get_market_groups_list(self) -> list[int]:
        return []

    async def get_market_group_details(self, group_id: int) -> dict:
        return {}

    async def get_item_type(self, type_id: int) -> dict:
        return {}

    async def get_route(self, origin: int, destination: int) -> list[int]:
        return []

    async def get_route_with_details(self, origin: int, destination: int) -> list[dict]:
        return []


@pytest.fixture
def mock_repository():
    """Fixture to create a mock repository"""
    return MockRepository()


@pytest.fixture
def orders_service(mock_repository, local_data_repository):
    """Fixture to create an OrdersService with a mock repository"""
    location_validator = LocationValidator(local_data_repository, mock_repository)
    return OrdersService(mock_repository, location_validator)


@pytest.mark.asyncio
@pytest.mark.unit
class TestOrdersService:
    """Tests for OrdersService"""

    async def test_get_orders_for_region_and_type(self, orders_service, mock_repository):
        """Test retrieving orders for a specific region and type"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 100, "location_id": 30000142},
                {"is_buy_order": False, "price": 90, "location_id": 30000142},
            ]
        }

        orders = await orders_service.get_orders(region_id, type_id)

        assert len(orders) == 2
        assert orders[0]["is_buy_order"] is True
        assert orders[1]["is_buy_order"] is False

    async def test_get_orders_caches_results(self, orders_service, mock_repository):
        """Test that orders are cached in memory"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 100, "location_id": 30000142},
            ]
        }

        # First call
        orders1 = await orders_service.get_orders(region_id, type_id)
        assert len(orders1) == 1

        # Clear repository to verify cache is used
        mock_repository.market_orders = {}

        # Second call should use cache
        orders2 = await orders_service.get_orders(region_id, type_id)
        assert len(orders2) == 1
        assert orders2 == orders1

    async def test_get_orders_for_multiple_regions(self, orders_service, mock_repository):
        """Test retrieving orders for multiple regions"""
        region_id_1 = 10000002
        region_id_2 = 10000003
        type_id = 123

        mock_repository.market_orders = {
            (region_id_1, type_id): [
                {"is_buy_order": True, "price": 100, "location_id": 30000142},
            ],
            (region_id_2, type_id): [
                {"is_buy_order": False, "price": 90, "location_id": 30000143},
            ],
        }

        orders1 = await orders_service.get_orders(region_id_1, type_id)
        orders2 = await orders_service.get_orders(region_id_2, type_id)

        assert len(orders1) == 1
        assert len(orders2) == 1
        assert orders1[0]["is_buy_order"] is True
        assert orders2[0]["is_buy_order"] is False

    async def test_get_orders_separated_by_type(self, orders_service, mock_repository):
        """Test that orders are separated correctly by buy/sell type"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 100, "location_id": 30000142},
                {"is_buy_order": True, "price": 105, "location_id": 30000142},
                {"is_buy_order": False, "price": 90, "location_id": 30000142},
                {"is_buy_order": False, "price": 95, "location_id": 30000142},
            ]
        }

        buy_orders, sell_orders = await orders_service.get_orders_separated(region_id, type_id)

        assert len(buy_orders) == 2
        assert len(sell_orders) == 2
        assert all(order["is_buy_order"] for order in buy_orders)
        assert all(not order["is_buy_order"] for order in sell_orders)

    async def test_get_orders_separated_with_region_id(self, orders_service, mock_repository):
        """Test get_orders_separated_with_region returns orders with region_id"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 100, "location_id": 30000142},
                {"is_buy_order": False, "price": 90, "location_id": 30000142},
            ]
        }

        buy_orders, sell_orders = await orders_service.get_orders_separated_with_region(
            region_id, type_id
        )

        assert len(buy_orders) == 1
        assert len(sell_orders) == 1
        assert buy_orders[0][1] == region_id  # (order, region_id) tuple
        assert sell_orders[0][1] == region_id

    async def test_get_orders_for_multiple_regions_with_region_id(
        self, orders_service, mock_repository
    ):
        """Test retrieving orders for multiple regions with region_id in result"""
        region_id_1 = 10000002
        region_id_2 = 10000003
        type_id = 123

        mock_repository.market_orders = {
            (region_id_1, type_id): [
                {"is_buy_order": True, "price": 100, "location_id": 30000142},
            ],
            (region_id_2, type_id): [
                {"is_buy_order": False, "price": 90, "location_id": 30000143},
            ],
        }

        buy_orders, sell_orders = await orders_service.get_orders_for_regions(
            [region_id_1, region_id_2], type_id
        )

        assert len(buy_orders) == 1
        assert len(sell_orders) == 1
        assert buy_orders[0][1] == region_id_1
        assert sell_orders[0][1] == region_id_2

    async def test_clear_cache(self, orders_service, mock_repository):
        """Test that cache can be cleared"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 100, "location_id": 30000142},
            ]
        }

        # First call - cache the result
        await orders_service.get_orders(region_id, type_id)

        # Clear cache
        orders_service.clear_cache()

        # Clear repository
        mock_repository.market_orders = {}

        # Should fail now since cache is cleared and repository is empty
        orders = await orders_service.get_orders(region_id, type_id)
        assert len(orders) == 0

    async def test_get_orders_handles_empty_result(self, orders_service, mock_repository):
        """Test that get_orders handles empty results"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {}

        orders = await orders_service.get_orders(region_id, type_id)

        assert orders == []

    async def test_get_orders_separated_handles_empty_result(
        self, orders_service, mock_repository
    ):
        """Test that get_orders_separated handles empty results"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {}

        buy_orders, sell_orders = await orders_service.get_orders_separated(region_id, type_id)

        assert buy_orders == []
        assert sell_orders == []

    async def test_get_orders_filters_invalid_locations(
        self, orders_service, mock_repository, local_data_repository
    ):
        """Test that get_orders filters out orders with invalid location_id"""
        region_id = 10000002
        type_id = 123

        # Mark an invalid location_id
        invalid_location_id = 999999999999
        local_data_repository.mark_location_id_as_invalid(invalid_location_id)

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 100, "location_id": 30000142},  # Valid
                {"is_buy_order": False, "price": 90, "location_id": invalid_location_id},  # Invalid
            ]
        }

        orders = await orders_service.get_orders(region_id, type_id)

        # Only the valid order should be returned
        assert len(orders) == 1
        assert orders[0]["location_id"] == 30000142

