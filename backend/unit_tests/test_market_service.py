"""
Unit tests for MarketService
Tests business logic with repository mocks
"""

from typing import Any

import pytest

from domain.location_validator import LocationValidator
from domain.market_service import MarketService
from domain.orders_service import OrdersService
from domain.repository import EveRepository
from domain.types import (
    ItemType,
    MarketGroupDetails,
    Order,
    RegionDetails,
    StationDetails,
    SystemDetails,
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

    async def get_constellation_details(self, constellation_id: int) -> dict[str, Any]:
        return {}

    async def get_stargate_details(self, stargate_id: int) -> dict[str, Any]:
        return {}

    async def get_item_type(self, type_id: int) -> ItemType:
        item_data = self.item_types.get(type_id, {})
        if isinstance(item_data, dict):
            return ItemType.from_dict(item_data)
        return item_data

    async def get_route(self, origin: int, destination: int) -> list[int]:
        return []

    async def get_route_with_details(self, origin: int, destination: int) -> list[dict[str, Any]]:
        return []


@pytest.fixture
def mock_repository():
    """Fixture to create a mock repository"""
    return MockRepository()


@pytest.fixture
def market_service(mock_repository, local_data_repository):
    """Fixture to create a MarketService with a mock repository"""
    location_validator = LocationValidator(local_data_repository, mock_repository)
    orders_service = OrdersService(mock_repository, location_validator)
    return MarketService(
        mock_repository,
        location_validator,
        orders_service,
        local_data_repository,
    )


@pytest.fixture
def fake_local_data_repository():
    class FakeLocalDataRepository:
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

    return FakeLocalDataRepository()


@pytest.fixture
def market_service_with_type_search(
    mock_repository, local_data_repository, fake_local_data_repository
):
    """Fixture to create a MarketService with fake type search data"""
    location_validator = LocationValidator(local_data_repository, mock_repository)
    orders_service = OrdersService(mock_repository, location_validator)
    return MarketService(
        mock_repository,
        location_validator,
        orders_service,
        fake_local_data_repository,
    )


@pytest.mark.asyncio
@pytest.mark.unit
class TestMarketServiceCategories:
    """Tests for market category retrieval"""

    async def test_get_market_categories_empty(self, market_service, mock_repository):
        """Test with empty group list"""
        mock_repository.market_groups_list = []

        result = await market_service.get_market_categories()

        assert isinstance(result, list)
        assert len(result) == 0

    async def test_get_market_categories_single_group(self, market_service, mock_repository):
        """Test with a single group"""
        mock_repository.market_groups_list = [1]
        mock_repository.market_groups_details = {
            1: {
                "market_group_id": 1,
                "name": "Test Group",
                "description": "A test group",
                "parent_group_id": None,
                "types": [101, 102, 103],
            }
        }

        result = await market_service.get_market_categories()

        assert len(result) == 1
        assert result[0].group_id == 1
        assert result[0].name == "Test Group"
        assert result[0].description == "A test group"
        assert result[0].parent_group_id is None
        assert result[0].types == [101, 102, 103]

    async def test_get_market_categories_multiple_groups(self, market_service, mock_repository):
        """Test with multiple groups, sorted by name"""
        mock_repository.market_groups_list = [1, 2, 3]
        mock_repository.market_groups_details = {
            1: {
                "market_group_id": 1,
                "name": "Zebra Group",
                "description": "",
                "parent_group_id": None,
                "types": [],
            },
            2: {
                "market_group_id": 2,
                "name": "Alpha Group",
                "description": "",
                "parent_group_id": None,
                "types": [],
            },
            3: {
                "market_group_id": 3,
                "name": "Beta Group",
                "description": "",
                "parent_group_id": None,
                "types": [],
            },
        }

        result = await market_service.get_market_categories()

        assert len(result) == 3
        # Verify results are sorted by name
        assert result[0].name == "Alpha Group"
        assert result[1].name == "Beta Group"
        assert result[2].name == "Zebra Group"

    async def test_get_market_categories_filters_errors(self, market_service, mock_repository):
        """Test that errors when retrieving a group are filtered"""
        mock_repository.market_groups_list = [1, 2, 3]

        # Simulate an exception for group 2
        async def failing_get_market_group_details(group_id: int) -> MarketGroupDetails:
            if group_id == 2:
                raise Exception("API Error")
            group_data = mock_repository.market_groups_details.get(group_id, {})
            if isinstance(group_data, dict):
                return MarketGroupDetails.from_dict(group_data)
            return group_data

        mock_repository.market_groups_details = {
            1: {
                "market_group_id": 1,
                "name": "Valid Group",
                "description": "",
                "parent_group_id": None,
                "types": [],
            },
            3: {
                "market_group_id": 3,
                "name": "Another Valid Group",
                "description": "",
                "parent_group_id": None,
                "types": [],
            },
        }
        mock_repository.get_market_group_details = failing_get_market_group_details

        result = await market_service.get_market_categories()

        # Should filter group 2 (error) and return only 1 and 3
        assert len(result) == 2
        # Verify returned groups are valid (sorted by name)
        group_names = [r.name for r in result]
        assert "Valid Group" in group_names
        assert "Another Valid Group" in group_names

    async def test_get_market_categories_with_parent(self, market_service, mock_repository):
        """Test with groups having a parent"""
        mock_repository.market_groups_list = [1, 2]
        mock_repository.market_groups_details = {
            1: {
                "market_group_id": 1,
                "name": "Parent Group",
                "description": "Parent",
                "parent_group_id": None,
                "types": [101],
            },
            2: {
                "market_group_id": 2,
                "name": "Child Group",
                "description": "Child",
                "parent_group_id": 1,
                "types": [201],
            },
        }

        result = await market_service.get_market_categories()

        assert len(result) == 2
        # Verify groups are sorted by name
        assert result[0].name == "Child Group"
        assert result[0].parent_group_id == 1
        assert result[1].name == "Parent Group"
        assert result[1].parent_group_id is None


@pytest.mark.asyncio
@pytest.mark.unit
class TestMarketServiceEnrichedOrders:
    """Tests for enriched order retrieval"""

    async def test_get_enriched_market_orders_empty(self, market_service, mock_repository):
        """Test with empty order list"""
        region_id = 10000002
        mock_repository.market_orders = {(region_id, None): []}

        result = await market_service.get_enriched_market_orders(region_id)

        assert result.total == 0
        assert result.buy_orders == []
        assert result.sell_orders == []

    async def test_get_enriched_market_orders_separates_buy_sell(
        self, market_service, mock_repository
    ):
        """Test that buy and sell orders are separated"""
        region_id = 10000002
        valid_location_id = 30000142
        mock_repository.market_orders = {
            (region_id, None): [
                {
                    "order_id": 1,
                    "type_id": 34,
                    "is_buy_order": True,
                    "price": 100,
                    "location_id": valid_location_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                },
                {
                    "order_id": 2,
                    "type_id": 34,
                    "is_buy_order": False,
                    "price": 90,
                    "location_id": valid_location_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                },
                {
                    "order_id": 3,
                    "type_id": 34,
                    "is_buy_order": True,
                    "price": 110,
                    "location_id": valid_location_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                },
            ]
        }

        result = await market_service.get_enriched_market_orders(region_id)

        assert result.total == 3
        assert len(result.buy_orders) == 2
        assert len(result.sell_orders) == 1


@pytest.mark.asyncio
@pytest.mark.unit
class TestMarketServiceTypeSearch:
    async def test_search_item_types_by_name(self, market_service_with_type_search):
        results = await market_service_with_type_search.search_item_types("tri")

        assert len(results) == 2
        assert results[0].type_id == 34
        assert results[0].name == "Tritanium"

    async def test_search_item_types_by_id(self, market_service_with_type_search, mock_repository):
        type_id = 987654

        async def fake_get_item_type(requested_id: int) -> ItemType:
            if requested_id == type_id:
                return ItemType.from_dict(
                    {"type_id": type_id, "name": "Custom Item", "volume": 0.0}
                )
            return ItemType.from_dict({"type_id": requested_id, "name": "Unknown", "volume": 0.0})

        mock_repository.get_item_type = fake_get_item_type

        results = await market_service_with_type_search.search_item_types(str(type_id))

        assert len(results) == 1
        assert results[0].type_id == type_id
        assert results[0].name == "Custom Item"

    async def test_search_item_types_empty_query(self, market_service_with_type_search):
        results = await market_service_with_type_search.search_item_types("  ")

        # Empty query should return all types (limited by default limit)
        assert isinstance(results, list)
        assert len(results) > 0

    async def test_search_item_types_no_query(self, market_service_with_type_search):
        results = await market_service_with_type_search.search_item_types(None)

        # No query should return all types (limited by default limit)
        assert isinstance(results, list)
        assert len(results) > 0

    async def test_get_enriched_market_orders_sorted_by_price(
        self, market_service, mock_repository
    ):
        """Test that orders are sorted by price"""
        region_id = 10000002
        valid_location_id = 30000142

        def create_order_dict(order_id: int, is_buy: bool, price: float) -> dict[str, Any]:
            return {
                "order_id": order_id,
                "type_id": 34,
                "is_buy_order": is_buy,
                "price": price,
                "location_id": valid_location_id,
                "volume_total": 1000,
                "volume_remain": 1000,
                "min_volume": 1,
                "duration": 90,
                "issued": "2024-01-01T00:00:00Z",
                "range": "region",
            }

        mock_repository.market_orders = {
            (region_id, None): [
                create_order_dict(1, True, 100),
                create_order_dict(2, True, 110),
                create_order_dict(3, True, 105),
                create_order_dict(4, False, 90),
                create_order_dict(5, False, 95),
                create_order_dict(6, False, 85),
            ]
        }

        result = await market_service.get_enriched_market_orders(region_id)

        # Buy orders sorted by descending price (best price first)
        buy_prices = [o.price for o in result.buy_orders]
        assert buy_prices == [110, 105, 100]

        # Sell orders sorted by ascending price (best price first)
        sell_prices = [o.price for o in result.sell_orders]
        assert sell_prices == [85, 90, 95]

    async def test_get_enriched_market_orders_respects_limit(self, market_service, mock_repository):
        """Test that limit is respected"""
        region_id = 10000002
        valid_location_id = 30000142

        # Create 100 buy orders and 100 sell orders
        def create_order_dict(order_id: int, is_buy: bool, price: float) -> dict[str, Any]:
            return {
                "order_id": order_id,
                "type_id": 34,
                "is_buy_order": is_buy,
                "price": price,
                "location_id": valid_location_id,
                "volume_total": 1000,
                "volume_remain": 1000,
                "min_volume": 1,
                "duration": 90,
                "issued": "2024-01-01T00:00:00Z",
                "range": "region",
            }

        buy_orders = [create_order_dict(i, True, 100 + i) for i in range(100)]
        sell_orders = [create_order_dict(100 + i, False, 50 + i) for i in range(100)]
        mock_repository.market_orders = {(region_id, None): buy_orders + sell_orders}

        result = await market_service.get_enriched_market_orders(region_id, limit=10)

        assert result.total == 200
        assert len(result.buy_orders) == 10  # Limited to 10
        assert len(result.sell_orders) == 10  # Limited to 10

    async def test_get_enriched_market_orders_enriches_system(
        self, market_service, mock_repository
    ):
        """Test that orders with a system are enriched"""
        region_id = 10000002
        system_id = 30000142
        mock_repository.market_orders = {
            (region_id, None): [
                {
                    "order_id": 1,
                    "type_id": 34,
                    "is_buy_order": True,
                    "price": 100,
                    "location_id": system_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                }
            ]
        }
        mock_repository.system_details = {
            system_id: {
                "system_id": system_id,
                "name": "Jita",
                "security_status": 0.9,
                "security_class": "B",
                "position": {},
                "constellation_id": 20000001,
                "planets": [],
                "star_id": None,
            }
        }

        result = await market_service.get_enriched_market_orders(region_id)

        assert len(result.buy_orders) == 1
        enriched_order = result.buy_orders[0]
        assert enriched_order.system_id == system_id
        assert enriched_order.system_name == "Jita"

    async def test_get_enriched_market_orders_enriches_station(
        self, market_service, mock_repository
    ):
        """Test that orders with a station are enriched"""
        region_id = 10000002
        station_id = 60008494
        system_id = 30000142
        mock_repository.market_orders = {
            (region_id, None): [
                {
                    "order_id": 1,
                    "type_id": 34,
                    "is_buy_order": True,
                    "price": 100,
                    "location_id": station_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                }
            ]
        }
        mock_repository.station_details = {
            station_id: {
                "station_id": station_id,
                "name": "Jita IV - Moon 4 - Caldari Navy Assembly Plant",
                "system_id": system_id,
            }
        }
        mock_repository.system_details = {
            system_id: {
                "system_id": system_id,
                "name": "Jita",
                "security_status": 0.9,
                "security_class": "B",
                "position": {},
                "constellation_id": 20000001,
                "planets": [],
                "star_id": None,
            }
        }

        result = await market_service.get_enriched_market_orders(region_id)

        assert len(result.buy_orders) == 1
        enriched_order = result.buy_orders[0]
        assert enriched_order.station_id == station_id
        assert enriched_order.station_name == "Jita IV - Moon 4 - Caldari Navy Assembly Plant"
        assert enriched_order.system_id == system_id
        assert enriched_order.system_name == "Jita"

    async def test_get_enriched_market_orders_handles_missing_location(
        self, market_service, mock_repository, local_data_repository
    ):
        """Test that orders with invalid location_id are filtered out by OrdersService"""
        region_id = 10000002
        invalid_location_id = 999999999  # Invalid location ID
        # Mark as invalid so LocationValidator will filter it
        local_data_repository.mark_location_id_as_invalid(invalid_location_id)
        mock_repository.market_orders = {
            (region_id, None): [
                {
                    "order_id": 1,
                    "type_id": 34,
                    "is_buy_order": True,
                    "price": 100,
                    "location_id": invalid_location_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                }
            ]
        }

        result = await market_service.get_enriched_market_orders(region_id)

        # Orders with invalid location_id are filtered out by OrdersService
        assert len(result.buy_orders) == 0
        assert result.total == 0

    async def test_get_enriched_market_orders_handles_enrichment_error(
        self, market_service, mock_repository
    ):
        """Test that enrichment errors are handled gracefully"""
        region_id = 10000002
        system_id = 99999999  # Non-existent system
        original_order = {
            "order_id": 1,
            "type_id": 34,
            "is_buy_order": True,
            "price": 100,
            "location_id": system_id,
            "volume_total": 1000,
            "volume_remain": 1000,
            "min_volume": 1,
            "duration": 90,
            "issued": "2024-01-01T00:00:00Z",
            "range": "region",
        }
        mock_repository.market_orders = {(region_id, None): [original_order]}

        # Simulate an exception when retrieving the system
        async def failing_get_system_details(system_id_param: int):
            if system_id_param == system_id:
                raise Exception("System not found")
            return {}

        mock_repository.get_system_details = failing_get_system_details

        result = await market_service.get_enriched_market_orders(region_id)

        assert len(result.buy_orders) == 1
        # On error, original order is returned (without enrichment)
        # because asyncio.gather with return_exceptions=True returns the exception
        # and the code filters by returning the original order
        enriched_order = result.buy_orders[0]
        # Order should have its original fields
        assert enriched_order.price == 100
        assert enriched_order.location_id == system_id

    async def test_get_enriched_market_orders_with_type_filter(
        self, market_service, mock_repository
    ):
        """Test with type_id filter"""
        region_id = 10000002
        type_id = 123

        def create_order_dict(order_id: int, price: float) -> dict[str, Any]:
            return {
                "order_id": order_id,
                "type_id": type_id,
                "is_buy_order": True,
                "price": price,
                "location_id": 30000142,
                "volume_total": 1000,
                "volume_remain": 1000,
                "min_volume": 1,
                "duration": 90,
                "issued": "2024-01-01T00:00:00Z",
                "range": "region",
            }

        mock_repository.market_orders = {
            (region_id, None): [create_order_dict(1, 100)],
            (region_id, type_id): [create_order_dict(2, 200)],
        }

        result = await market_service.get_enriched_market_orders(region_id, type_id=type_id)

        # Should return only orders filtered by type_id
        assert result.total == 1
        assert len(result.buy_orders) == 1
        assert result.buy_orders[0].price == 200


@pytest.mark.asyncio
@pytest.mark.unit
class TestMarketServiceTypePricesByRegion:
    """Tests for get_type_prices_by_region method"""

    async def test_get_type_prices_by_region_filters_regions_without_prices(
        self, market_service, mock_repository
    ):
        """Test that regions without any prices are filtered out"""
        type_id = 34
        region_id_1 = 10000002
        region_id_2 = 10000003
        region_id_3 = 10000004
        valid_location_id = 30000142

        # Setup: region 1 has both buy and sell orders, region 2 has only buy, region 3 has no orders
        mock_repository.market_orders = {
            (region_id_1, type_id): [
                {
                    "order_id": 1,
                    "type_id": type_id,
                    "is_buy_order": True,
                    "price": 100.0,
                    "location_id": valid_location_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                },
                {
                    "order_id": 2,
                    "type_id": type_id,
                    "is_buy_order": False,
                    "price": 110.0,
                    "location_id": valid_location_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                },
            ],
            (region_id_2, type_id): [
                {
                    "order_id": 3,
                    "type_id": type_id,
                    "is_buy_order": True,
                    "price": 95.0,
                    "location_id": valid_location_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                },
            ],
            (region_id_3, type_id): [],  # No orders
        }

        # Setup region details
        mock_repository._regions_list = [region_id_1, region_id_2, region_id_3]
        mock_repository._region_details = {
            region_id_1: {
                "region_id": region_id_1,
                "name": "Region 1",
                "description": "",
                "constellations": [],
            },
            region_id_2: {
                "region_id": region_id_2,
                "name": "Region 2",
                "description": "",
                "constellations": [],
            },
            region_id_3: {
                "region_id": region_id_3,
                "name": "Region 3",
                "description": "",
                "constellations": [],
            },
        }

        result = await market_service.get_type_prices_by_region(type_id)

        # Should only return regions 1 and 2 (region 3 has no prices)
        assert len(result) == 2
        region_ids = [r.region_id for r in result]
        assert region_id_1 in region_ids
        assert region_id_2 in region_ids
        assert region_id_3 not in region_ids

    async def test_get_type_prices_by_region_price_fields_always_present(
        self, market_service, mock_repository
    ):
        """Test that max_buy_price and min_sell_price are always present (even if null)"""
        type_id = 34
        region_id = 10000002
        valid_location_id = 30000142

        mock_repository.market_orders = {
            (region_id, type_id): [
                {
                    "order_id": 1,
                    "type_id": type_id,
                    "is_buy_order": True,
                    "price": 100.0,
                    "location_id": valid_location_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                },
            ],
        }

        mock_repository._regions_list = [region_id]
        mock_repository._region_details = {
            region_id: {
                "region_id": region_id,
                "name": "Test Region",
                "description": "",
                "constellations": [],
            }
        }

        result = await market_service.get_type_prices_by_region(type_id)

        assert len(result) == 1
        price_info = result[0]
        # Fields must always be present (can be None)
        assert hasattr(price_info, "max_buy_price")
        assert hasattr(price_info, "min_sell_price")
        assert price_info.max_buy_price == 100.0
        assert price_info.min_sell_price is None

    async def test_get_type_prices_by_region_calculates_max_buy_min_sell(
        self, market_service, mock_repository
    ):
        """Test that max buy price and min sell price are calculated correctly"""
        type_id = 34
        region_id = 10000002
        valid_location_id = 30000142

        mock_repository.market_orders = {
            (region_id, type_id): [
                {
                    "order_id": 1,
                    "type_id": type_id,
                    "is_buy_order": True,
                    "price": 100.0,
                    "location_id": valid_location_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                },
                {
                    "order_id": 2,
                    "type_id": type_id,
                    "is_buy_order": True,
                    "price": 110.0,  # Higher buy price
                    "location_id": valid_location_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                },
                {
                    "order_id": 3,
                    "type_id": type_id,
                    "is_buy_order": False,
                    "price": 120.0,
                    "location_id": valid_location_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                },
                {
                    "order_id": 4,
                    "type_id": type_id,
                    "is_buy_order": False,
                    "price": 115.0,  # Lower sell price
                    "location_id": valid_location_id,
                    "volume_total": 1000,
                    "volume_remain": 1000,
                    "min_volume": 1,
                    "duration": 90,
                    "issued": "2024-01-01T00:00:00Z",
                    "range": "region",
                },
            ],
        }

        mock_repository._regions_list = [region_id]
        mock_repository._region_details = {
            region_id: {
                "region_id": region_id,
                "name": "Test Region",
                "description": "",
                "constellations": [],
            }
        }

        result = await market_service.get_type_prices_by_region(type_id)

        assert len(result) == 1
        price_info = result[0]
        # Max buy price should be 110.0 (highest)
        assert price_info.max_buy_price == 110.0
        # Min sell price should be 115.0 (lowest)
        assert price_info.min_sell_price == 115.0
