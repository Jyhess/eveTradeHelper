import time
from typing import Any

import pytest

from domain.deals_service import DealsService
from domain.location_validator import LocationValidator
from domain.orders_service import OrdersService
from domain.repository import EveRepository
from repositories.local_data import LocalDataRepository


class MockRepository(EveRepository):
    """Mock repository for unit tests"""

    def __init__(self):
        self.market_groups_list = []
        self.market_groups_details = {}
        self.market_orders = {}
        self.item_types = {}
        self.system_details = {}
        self.constellation_details = {}
        self.station_details = {}
        self.route_with_details = {}
        self.routes = {}

    async def get_market_groups_list(self) -> list[int]:
        return self.market_groups_list

    async def get_market_group_details(self, group_id: int) -> dict[str, Any]:
        return self.market_groups_details.get(group_id, {})

    async def get_market_orders(
        self, region_id: int, type_id: int | None = None
    ) -> list[dict[str, Any]]:
        key = (region_id, type_id)
        return self.market_orders.get(key, [])

    async def get_item_type(self, type_id: int) -> dict[str, Any]:
        return self.item_types.get(type_id, {"name": f"Type {type_id}"})

    async def get_regions_list(self) -> list[int]:
        return []

    async def get_region_details(self, region_id: int) -> dict[str, Any]:
        return {}

    async def get_constellation_details(self, constellation_id: int) -> dict[str, Any]:
        return self.constellation_details.get(constellation_id, {})

    async def get_system_details(self, system_id: int) -> dict[str, Any]:
        return self.system_details.get(system_id, {})

    async def get_stargate_details(self, stargate_id: int) -> dict[str, Any]:
        return {}

    async def get_station_details(self, station_id: int) -> dict[str, Any]:
        return self.station_details.get(station_id, {})

    async def get_route(self, origin: int, destination: int) -> list[int]:
        key = (origin, destination)
        return self.routes.get(key, [])

    async def get_route_with_details(self, origin: int, destination: int) -> list[dict[str, Any]]:
        key = (origin, destination)
        return self.route_with_details.get(key, [])


@pytest.fixture
def mock_repository():
    """Fixture to create a mock repository"""
    return MockRepository()


@pytest.fixture
def deals_service(mock_repository, local_data_repository):
    """Fixture to create a DealsService with a mock repository"""
    location_validator = LocationValidator(local_data_repository, mock_repository)
    orders_service = OrdersService(mock_repository, location_validator)
    return DealsService(mock_repository, location_validator, orders_service)


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceCollectTypes:
    """Tests for collecting types from a group"""

    async def test_collect_all_types_from_simple_group(self, deals_service, mock_repository):
        """Test with a simple group without subgroups"""
        # Setup - use unique IDs to avoid cache conflicts
        group_id = int(time.time() * 1000000) % 1000000 + 1000000
        mock_repository.market_groups_list = [group_id]
        mock_repository.market_groups_details = {
            group_id: {"types": [101, 102, 103], "parent_group_id": None}
        }

        # Execute
        result = await deals_service.collect_all_types_from_group(group_id)

        # Verify
        # The @cached decorator returns a list, convert it to Set for comparison
        if isinstance(result, list):
            result = set(result)
        assert isinstance(result, set)
        assert result == {101, 102, 103}

    async def test_collect_all_types_from_group_with_children(self, deals_service, mock_repository):
        """Test with a group having subgroups"""
        # Setup: parent group with 2 subgroups - use unique IDs
        base_id = int(time.time() * 1000000) % 1000000 + 2000000
        group_id_1 = base_id
        group_id_2 = base_id + 1
        group_id_3 = base_id + 2
        mock_repository.market_groups_list = [group_id_1, group_id_2, group_id_3]
        mock_repository.market_groups_details = {
            group_id_1: {"types": [101, 102], "parent_group_id": None},  # Parent
            group_id_2: {
                "types": [201, 202],
                "parent_group_id": group_id_1,
            },  # Child 1
            group_id_3: {"types": [301], "parent_group_id": group_id_1},  # Child 2
        }

        # Execute
        result = await deals_service.collect_all_types_from_group(group_id_1)

        # Verify: should include types from parent and children
        # The @cached decorator returns a list, convert it to Set for comparison
        if isinstance(result, list):
            result = set(result)
        assert isinstance(result, set)
        assert result == {101, 102, 201, 202, 301}

    async def test_collect_all_types_from_nested_groups(self, deals_service, mock_repository):
        """Test with nested groups on multiple levels"""
        # Use unique IDs to avoid cache conflicts
        base_id = int(time.time() * 1000000) % 1000000 + 3000000
        group_id_1 = base_id
        group_id_2 = base_id + 1
        group_id_3 = base_id + 2
        group_id_4 = base_id + 3
        mock_repository.market_groups_list = [
            group_id_1,
            group_id_2,
            group_id_3,
            group_id_4,
        ]
        mock_repository.market_groups_details = {
            group_id_1: {"types": [101], "parent_group_id": None},  # Level 1
            group_id_2: {"types": [201], "parent_group_id": group_id_1},  # Level 2
            group_id_3: {"types": [301], "parent_group_id": group_id_2},  # Level 3
            group_id_4: {
                "types": [401],
                "parent_group_id": group_id_2,
            },  # Level 3 (other child)
        }

        # Execute
        result = await deals_service.collect_all_types_from_group(group_id_1)

        # Verify: should include all types from all levels
        # The @cached decorator returns a list, convert it to Set for comparison
        if isinstance(result, list):
            result = set(result)
        assert result == {101, 201, 301, 401}

    async def test_collect_all_types_from_unknown_group(self, deals_service, mock_repository):
        """Test with a non-existent group"""
        # Use unique ID to avoid cache conflicts
        unknown_group_id = int(time.time() * 1000000) % 1000000 + 9999999
        mock_repository.market_groups_list = []
        mock_repository.market_groups_details = {}

        # Execute
        result = await deals_service.collect_all_types_from_group(unknown_group_id)

        # Verify: should return an empty set
        # The @cached decorator returns a list, convert it to Set for comparison
        if isinstance(result, list):
            result = set(result)
        assert isinstance(result, set)
        assert len(result) == 0

    async def test_collect_all_types_from_group_without_types(self, deals_service, mock_repository):
        """Test with a group without types (only subgroups)"""
        # Use unique IDs to avoid cache conflicts
        base_id = int(time.time() * 1000000) % 1000000 + 4000000
        group_id_1 = base_id
        group_id_2 = base_id + 1
        mock_repository.market_groups_list = [group_id_1, group_id_2]
        mock_repository.market_groups_details = {
            group_id_1: {"types": [], "parent_group_id": None},
            group_id_2: {"types": [201, 202], "parent_group_id": group_id_1},
        }

        # Execute
        result = await deals_service.collect_all_types_from_group(group_id_1)

        # Verify: should include only types from children
        # The @cached decorator returns a list, convert it to Set for comparison
        if isinstance(result, list):
            result = set(result)
        assert result == {201, 202}


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceAnalyzeType:
    """Tests for type profitability analysis"""

    async def test_analyze_type_profitability_profitable(self, deals_service, mock_repository):
        """Test with a profitable type"""
        region_id = 10000002
        type_id = 123
        profit_threshold = 5.0

        # Setup: buy and sell orders
        # buy_order = someone wants to BUY → we can SELL at this price
        # sell_order = someone wants to SELL → we can BUY at this price
        mock_repository.market_orders = {
            (region_id, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # Best price to SELL
                {
                    "is_buy_order": True,
                    "price": 105,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 95,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # Best price to BUY
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ]
        }
        mock_repository.item_types = {
            type_id: {"name": "Test Item", "description": "A test item", "volume": 1.0}
        }
        mock_repository.system_details = {
            30000142: {
                "system_id": 30000142,
                "name": "Test System",
                "security_status": 0.9,
            }
        }

        # Execute
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=profit_threshold
        )

        # Verify
        assert result is not None
        assert result["type_id"] == type_id
        assert result["type_name"] == "Test Item"
        assert (
            result["buy_price"] == 95
        )  # Price at which we BUY (lowest among sell_orders)
        assert (
            result["sell_price"] == 110
        )  # Price at which we SELL (highest among buy_orders)
        # Profit = (110 - 95) * 10 = 150 ISK
        # Profit % = (110 - 95) / 95 * 100 = 15.79%
        assert result["profit_percent"] == pytest.approx(15.79, rel=0.01)
        assert result["profit_isk"] == pytest.approx(150, rel=0.01)
        assert result["buy_order_count"] == 2
        assert result["sell_order_count"] == 2

    async def test_analyze_type_profitability_below_threshold(self, deals_service, mock_repository):
        """Test with a non-profitable type (profit < threshold)"""
        region_id = 10000002
        type_id = 123
        profit_threshold = 10.0

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 105, "location_id": 30000142},  # Profit = 5%
                {"is_buy_order": False, "price": 100, "location_id": 30000142},
            ]
        }

        # Execute
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=profit_threshold
        )

        # Verify: should return None because profit < threshold
        assert result is None

    async def test_analyze_type_profitability_no_buy_orders(self, deals_service, mock_repository):
        """Test with only sell orders"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": False, "price": 100, "location_id": 30000142},
            ]
        }

        # Execute
        result = await deals_service.analyze_type_profitability(region_id, type_id, 5.0)

        # Verify: should return None
        assert result is None

    async def test_analyze_type_profitability_no_sell_orders(self, deals_service, mock_repository):
        """Test with only buy orders"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 100, "location_id": 30000142},
            ]
        }

        # Execute
        result = await deals_service.analyze_type_profitability(region_id, type_id, 5.0)

        # Verify: should return None
        assert result is None

    async def test_analyze_type_profitability_exact_threshold(self, deals_service, mock_repository):
        """Test with profit exactly equal to threshold"""
        region_id = 10000002
        type_id = 123
        profit_threshold = 10.0

        mock_repository.market_orders = {
            (region_id, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # Profit = 10%
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ]
        }
        mock_repository.item_types = {type_id: {"name": "Test Item", "volume": 1.0}}

        # Execute
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=profit_threshold
        )

        # Verify: should return result (>= threshold)
        assert result is not None
        assert result["profit_percent"] == 10.0

    async def test_analyze_type_profitability_handles_exception(
        self, deals_service, mock_repository
    ):
        """Test that exceptions are handled"""
        region_id = 10000002
        type_id = 123

        # Simulate an exception when calling repository
        async def failing_get_market_orders(*args, **kwargs):
            raise Exception("API Error")

        mock_repository.get_market_orders = failing_get_market_orders

        # Execute
        result = await deals_service.analyze_type_profitability(region_id, type_id, 5.0)

        # Verify: should return None without raising exception
        assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceFindDeals:
    """Tests for complete deal search"""

    async def test_find_market_deals_empty_group(self, deals_service, mock_repository):
        """Test with an empty group"""
        # Use unique ID to avoid cache conflicts
        group_id = int(time.time() * 1000000) % 1000000 + 5000000
        mock_repository.market_groups_list = []
        mock_repository.market_groups_details = {}

        # Execute
        result = await deals_service.find_market_deals(10000002, group_id, min_profit_isk=5.0)

        # Verify
        assert result["region_id"] == 10000002
        assert result["group_id"] == group_id
        assert result["min_profit_isk"] == 5.0
        assert result["total_types"] == 0
        assert result["deals"] == []

    async def test_find_market_deals_without_group_id(self, deals_service, mock_repository):
        """Test find_market_deals with group_id=None (all groups)"""
        region_id = 10000002
        profit_threshold = 5.0

        # Setup top-level groups
        top_level_group_1 = 1
        top_level_group_2 = 2
        child_group = 3

        mock_repository.market_groups_list = [top_level_group_1, top_level_group_2, child_group]
        mock_repository.market_groups_details = {
            top_level_group_1: {"types": [101], "parent_group_id": None},
            top_level_group_2: {"types": [201], "parent_group_id": None},
            child_group: {"types": [301], "parent_group_id": top_level_group_1},
        }

        # Setup orders: 101 profitable
        mock_repository.market_orders = {
            (region_id, 101): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ],
            (region_id, 201): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ],
        }

        # Execute with group_id=None
        result = await deals_service.find_market_deals(
            region_id, group_id=None, min_profit_isk=profit_threshold
        )

        # Verify
        assert result["region_id"] == region_id
        assert "group_id" not in result  # Should not include group_id when None
        assert result["min_profit_isk"] == profit_threshold
        assert result["total_types"] >= 2  # Should include types from top-level groups
        assert len(result["deals"]) >= 1  # Should find at least one deal

    async def test_find_market_deals_with_profitable_items(self, deals_service, mock_repository):
        """Test with profitable items"""
        # Use unique IDs to avoid cache conflicts
        base_id = int(time.time() * 1000000) % 1000000 + 6000000
        region_id = 10000002
        profit_threshold = 5.0

        # Setup groups
        group_id_1 = base_id
        group_id_2 = base_id + 1
        mock_repository.market_groups_list = [group_id_1, group_id_2]
        mock_repository.market_groups_details = {
            group_id_1: {"types": [101, 102], "parent_group_id": None},
            group_id_2: {"types": [201], "parent_group_id": group_id_1},
        }

        # Setup orders: 101 profitable, 102 non, 201 profitable
        # min_profit_isk = 5.0 ISK, so with volume=10: profit_isk = (sell_price - buy_price) * 10
        # For 101: (110-100)*10 = 100 ISK > 5.0 ✓
        # For 102: (102-100)*10 = 20 ISK > 5.0 ✓ (but profit% = 2% < 5%)
        # For 201: (120-100)*10 = 200 ISK > 5.0 ✓
        mock_repository.market_orders = {
            (region_id, 101): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # 10% profit, 100 ISK
            ],
            (region_id, 102): [
                {
                    "is_buy_order": True,
                    "price": 102,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # 2% profit, 20 ISK
            ],
            (region_id, 201): [
                {
                    "is_buy_order": True,
                    "price": 120,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # 20% profit, 200 ISK
            ],
        }

        # Setup types
        mock_repository.item_types = {
            101: {"name": "Item 101", "volume": 1.0},
            102: {"name": "Item 102", "volume": 1.0},
            201: {"name": "Item 201", "volume": 1.0},
        }

        # Execute
        result = await deals_service.find_market_deals(
            region_id, group_id_1, min_profit_isk=profit_threshold
        )

        # Verify
        assert result["total_types"] == 3  # 101, 102, 201
        # All 3 types have profit_isk >= 5.0, so 3 deals
        assert len(result["deals"]) == 3  # 101, 102, and 201 (all > 5.0 ISK)
        assert result["deals"][0]["type_id"] == 201  # Sorted by profit ISK descending
        assert result["deals"][0]["profit_percent"] == 20.0
        assert result["deals"][1]["type_id"] == 101  # 100 ISK
        assert result["deals"][1]["profit_percent"] == 10.0
        assert result["deals"][2]["type_id"] == 102  # 20 ISK (lowest but > 5.0)
        assert result["deals"][2]["profit_percent"] == 2.0

    async def test_find_market_deals_sorted_by_profit(self, deals_service, mock_repository):
        """Test that deals are sorted by profit descending"""
        region_id = 10000002
        group_id = 1

        mock_repository.market_groups_list = [1]
        mock_repository.market_groups_details = {
            1: {"types": [101, 102, 103], "parent_group_id": None}
        }

        # Setup: different profits
        # min_profit_isk = 5.0 ISK, so with volume=10: profit_isk = (sell_price - buy_price) * 10
        mock_repository.market_orders = {
            (region_id, 101): [
                {
                    "is_buy_order": True,
                    "price": 105,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # 5%, 50 ISK
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ],
            (region_id, 102): [
                {
                    "is_buy_order": True,
                    "price": 115,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # 15%, 150 ISK
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ],
            (region_id, 103): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # 10%, 100 ISK
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ],
        }

        mock_repository.item_types = {
            101: {"name": "Item 101", "volume": 1.0},
            102: {"name": "Item 102", "volume": 1.0},
            103: {"name": "Item 103", "volume": 1.0},
        }

        # Execute
        result = await deals_service.find_market_deals(region_id, group_id, min_profit_isk=5.0)

        # Verify: descending sort
        assert len(result["deals"]) == 3
        assert result["deals"][0]["profit_percent"] == 15.0  # 102
        assert result["deals"][1]["profit_percent"] == 10.0  # 103
        assert result["deals"][2]["profit_percent"] == 5.0  # 101

    @pytest.mark.parametrize(
        "max_transport_volume,expected_volume",
        [(None, 10), (5.0, 5), (20.0, 10), (0.5, 0)],
    )
    async def test_find_market_deals_with_max_transport_volume(
        self, deals_service, mock_repository, max_transport_volume, expected_volume
    ):
        """Test find_market_deals with max_transport_volume limit"""
        region_id = 10000002
        group_id = 1
        type_id = 101

        mock_repository.market_groups_list = [1]
        mock_repository.market_groups_details = {
            1: {"types": [type_id], "parent_group_id": None}
        }

        mock_repository.market_orders = {
            (region_id, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ]
        }

        mock_repository.item_types = {type_id: {"name": "Item 101", "volume": 1.0}}
        mock_repository.system_details = {
            30000142: {"system_id": 30000142, "name": "Test System", "security_status": 0.9}
        }

        result = await deals_service.find_market_deals(
            region_id, group_id, min_profit_isk=5.0, max_transport_volume=max_transport_volume
        )

        if expected_volume == 0:
            assert len(result["deals"]) == 0
        else:
            assert len(result["deals"]) == 1
            assert result["deals"][0]["tradable_volume"] == expected_volume

    @pytest.mark.parametrize(
        "max_buy_cost,expected_volume",
        [(None, 10), (500.0, 5), (2000.0, 10), (50.0, 0)],
    )
    async def test_find_market_deals_with_max_buy_cost(
        self, deals_service, mock_repository, max_buy_cost, expected_volume
    ):
        """Test find_market_deals with max_buy_cost limit"""
        region_id = 10000002
        group_id = 1
        type_id = 101

        mock_repository.market_groups_list = [1]
        mock_repository.market_groups_details = {
            1: {"types": [type_id], "parent_group_id": None}
        }

        mock_repository.market_orders = {
            (region_id, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ]
        }

        mock_repository.item_types = {type_id: {"name": "Item 101", "volume": 1.0}}
        mock_repository.system_details = {
            30000142: {"system_id": 30000142, "name": "Test System", "security_status": 0.9}
        }

        result = await deals_service.find_market_deals(
            region_id, group_id, min_profit_isk=5.0, max_buy_cost=max_buy_cost
        )

        if expected_volume == 0:
            assert len(result["deals"]) == 0
        else:
            assert len(result["deals"]) == 1
            assert result["deals"][0]["tradable_volume"] == expected_volume

    async def test_find_market_deals_with_additional_regions(
        self, deals_service, mock_repository
    ):
        """Test find_market_deals with additional_regions"""
        region_id = 10000002
        additional_region_id = 10000003
        group_id = 1
        type_id = 101

        mock_repository.market_groups_list = [1]
        mock_repository.market_groups_details = {
            1: {"types": [type_id], "parent_group_id": None}
        }

        # Best buy order in additional region, best sell order in main region
        mock_repository.market_orders = {
            (region_id, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ],
            (additional_region_id, type_id): [
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000143,
                },
            ],
        }

        mock_repository.item_types = {type_id: {"name": "Item 101", "volume": 1.0}}
        mock_repository.system_details = {
            30000142: {"system_id": 30000142, "name": "Test System 1", "security_status": 0.9},
            30000143: {"system_id": 30000143, "name": "Test System 2", "security_status": 0.9},
        }

        result = await deals_service.find_market_deals(
            region_id,
            group_id,
            min_profit_isk=5.0,
            additional_regions=[additional_region_id],
        )

        assert len(result["deals"]) == 1
        assert result["deals"][0]["type_id"] == type_id
        assert result["deals"][0]["buy_price"] == 100
        assert result["deals"][0]["sell_price"] == 110


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceSystemToSystem:
    """Tests for system-to-system deals"""

    async def test_find_system_to_system_deals_profitable(
        self, deals_service, mock_repository
    ):
        """Test find_system_to_system_deals with profitable deal"""
        from_system_id = 30000142
        to_system_id = 30000143
        from_region_id = 10000002
        to_region_id = 10000003
        type_id = 101

        # Setup system and constellation data
        mock_repository.system_details = {
            from_system_id: {
                "system_id": from_system_id,
                "name": "From System",
                "constellation_id": 20000001,
            },
            to_system_id: {
                "system_id": to_system_id,
                "name": "To System",
                "constellation_id": 20000002,
            },
        }

        mock_repository.constellation_details = {
            20000001: {"constellation_id": 20000001, "region_id": from_region_id},
            20000002: {"constellation_id": 20000002, "region_id": to_region_id},
        }

        # Setup station details for location validation
        # Use station IDs that are >= STATION_ID_THRESHOLD (60000000)
        # Use known valid station IDs from static data
        from_station_id = 60008494  # Known valid station ID in static data
        to_station_id = 60000004  # Another known valid station ID in static data
        mock_repository.station_details = {
            from_station_id: {"station_id": from_station_id, "system_id": from_system_id, "name": "From Station"},
            to_station_id: {"station_id": to_station_id, "system_id": to_system_id, "name": "To Station"},
        }

        # Setup market orders
        mock_repository.market_orders = {
            (from_region_id, type_id): [
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": from_station_id,
                },
            ],
            (to_region_id, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": to_station_id,
                },
            ],
        }

        mock_repository.item_types = {type_id: {"name": "Item 101", "volume": 1.0}}
        # Setup route (direct connection)
        mock_repository.routes = {
            (from_system_id, to_system_id): [from_system_id, to_system_id]
        }
        mock_repository.route_with_details = {
            (from_system_id, to_system_id): [
                {
                    "system_id": from_system_id,
                    "name": "From System",
                    "security_status": 0.9,
                },
                {
                    "system_id": to_system_id,
                    "name": "To System",
                    "security_status": 0.9,
                },
            ]
        }

        # Setup market groups to collect all types (group_id=None means all groups)
        mock_repository.market_groups_list = [1]
        mock_repository.market_groups_details = {
            1: {"types": [type_id], "parent_group_id": None}
        }

        result = await deals_service.find_system_to_system_deals(
            from_system_id, to_system_id, min_profit_isk=5.0
        )

        assert result["from_system_id"] == from_system_id
        assert result["to_system_id"] == to_system_id
        assert result["route"] == [from_system_id, to_system_id]
        assert result["route_segments"] == [(from_system_id, to_system_id)]
        assert len(result["deals"]) == 1
        assert result["deals"][0]["type_id"] == type_id
        assert result["deals"][0]["buy_price"] == 100
        assert result["deals"][0]["sell_price"] == 110
        assert result["deals"][0]["jumps"] == 1

    async def test_find_system_to_system_deals_with_group_filter(
        self, deals_service, mock_repository
    ):
        """Test find_system_to_system_deals with group_id filter"""
        from_system_id = 30000142
        to_system_id = 30000143
        from_region_id = 10000002
        to_region_id = 10000003
        group_id = 1
        type_id_in_group = 101
        type_id_not_in_group = 102

        # Setup system and constellation data
        mock_repository.system_details = {
            from_system_id: {
                "system_id": from_system_id,
                "name": "From System",
                "constellation_id": 20000001,
            },
            to_system_id: {
                "system_id": to_system_id,
                "name": "To System",
                "constellation_id": 20000002,
            },
        }

        mock_repository.constellation_details = {
            20000001: {"constellation_id": 20000001, "region_id": from_region_id},
            20000002: {"constellation_id": 20000002, "region_id": to_region_id},
        }

        # Setup station details
        # Use station IDs that are >= STATION_ID_THRESHOLD (60000000)
        from_station_id = 60008494  # Known valid station ID
        to_station_id = 60000004  # Another known valid station ID
        mock_repository.station_details = {
            from_station_id: {"station_id": from_station_id, "system_id": from_system_id},
            to_station_id: {"station_id": to_station_id, "system_id": to_system_id},
        }

        # Setup market groups
        mock_repository.market_groups_list = [group_id]
        mock_repository.market_groups_details = {
            group_id: {"types": [type_id_in_group], "parent_group_id": None}
        }

        # Setup market orders for both types
        mock_repository.market_orders = {
            (from_region_id, type_id_in_group): [
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": from_station_id,
                },
            ],
            (to_region_id, type_id_in_group): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": to_station_id,
                },
            ],
            (from_region_id, type_id_not_in_group): [
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": from_station_id,
                },
            ],
            (to_region_id, type_id_not_in_group): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": to_station_id,
                },
            ],
        }

        mock_repository.item_types = {
            type_id_in_group: {"name": "Item 101", "volume": 1.0},
            type_id_not_in_group: {"name": "Item 102", "volume": 1.0},
        }
        # Setup route (direct connection)
        mock_repository.routes = {
            (from_system_id, to_system_id): [from_system_id, to_system_id]
        }

        result = await deals_service.find_system_to_system_deals(
            from_system_id, to_system_id, min_profit_isk=5.0, group_id=group_id
        )

        # Should only find deals for type_id_in_group
        assert len(result["deals"]) == 1
        assert result["deals"][0]["type_id"] == type_id_in_group

    async def test_find_system_to_system_deals_no_constellation(
        self, deals_service, mock_repository
    ):
        """Test find_system_to_system_deals when constellation is missing"""
        from_system_id = 30000142
        to_system_id = 30000143

        mock_repository.system_details = {
            from_system_id: {"system_id": from_system_id, "name": "From System"},
            to_system_id: {"system_id": to_system_id, "name": "To System"},
        }

        result = await deals_service.find_system_to_system_deals(
            from_system_id, to_system_id, min_profit_isk=5.0
        )

        assert result["from_system_id"] == from_system_id
        assert result["to_system_id"] == to_system_id
        assert result["total_types"] == 0
        assert result["deals"] == []

    async def test_find_system_to_system_deals_with_volume_limit(
        self, deals_service, mock_repository
    ):
        """Test find_system_to_system_deals with max_transport_volume"""
        from_system_id = 30000142
        to_system_id = 30000143
        from_region_id = 10000002
        to_region_id = 10000003
        type_id = 101

        mock_repository.system_details = {
            from_system_id: {
                "system_id": from_system_id,
                "name": "From System",
                "constellation_id": 20000001,
            },
            to_system_id: {
                "system_id": to_system_id,
                "name": "To System",
                "constellation_id": 20000002,
            },
        }

        mock_repository.constellation_details = {
            20000001: {"constellation_id": 20000001, "region_id": from_region_id},
            20000002: {"constellation_id": 20000002, "region_id": to_region_id},
        }

        # Use station IDs that are >= STATION_ID_THRESHOLD (60000000)
        from_station_id = 60008494  # Known valid station ID
        to_station_id = 60000004  # Another known valid station ID
        mock_repository.station_details = {
            from_station_id: {"station_id": from_station_id, "system_id": from_system_id},
            to_station_id: {"station_id": to_station_id, "system_id": to_system_id},
        }

        mock_repository.market_orders = {
            (from_region_id, type_id): [
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": from_station_id,
                },
            ],
            (to_region_id, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": to_station_id,
                },
            ],
        }

        # Item volume is 2.0, max_transport_volume is 5.0, so max tradable is 2
        mock_repository.item_types = {type_id: {"name": "Item 101", "volume": 2.0}}
        # Setup route (direct connection)
        mock_repository.routes = {
            (from_system_id, to_system_id): [from_system_id, to_system_id]
        }

        # Setup market groups to collect all types (group_id=None means all groups)
        mock_repository.market_groups_list = [1]
        mock_repository.market_groups_details = {
            1: {"types": [type_id], "parent_group_id": None}
        }

        result = await deals_service.find_system_to_system_deals(
            from_system_id, to_system_id, min_profit_isk=5.0, max_transport_volume=5.0
        )

        assert len(result["deals"]) == 1
        assert result["deals"][0]["tradable_volume"] == 2

    async def test_find_system_to_system_deals_with_multiple_segments(
        self, deals_service, mock_repository
    ):
        """Test find_system_to_system_deals with a route containing multiple systems"""
        source_system = 30000142
        intermediate_system = 30000143
        destination_system = 30000144
        source_region = 10000002
        intermediate_region = 10000003
        destination_region = 10000004
        type_id = 101

        # Setup route: source -> intermediate -> destination
        route = [source_system, intermediate_system, destination_system]
        mock_repository.routes = {
            (source_system, destination_system): route
        }

        # Setup system and constellation data
        mock_repository.system_details = {
            source_system: {
                "system_id": source_system,
                "name": "Source System",
                "constellation_id": 20000001,
            },
            intermediate_system: {
                "system_id": intermediate_system,
                "name": "Intermediate System",
                "constellation_id": 20000002,
            },
            destination_system: {
                "system_id": destination_system,
                "name": "Destination System",
                "constellation_id": 20000003,
            },
        }

        mock_repository.constellation_details = {
            20000001: {"constellation_id": 20000001, "region_id": source_region},
            20000002: {"constellation_id": 20000002, "region_id": intermediate_region},
            20000003: {"constellation_id": 20000003, "region_id": destination_region},
        }

        # Setup stations
        source_station = 60008494
        intermediate_station = 60000004
        destination_station = 60000005
        mock_repository.station_details = {
            source_station: {"station_id": source_station, "system_id": source_system, "name": "Source Station"},
            intermediate_station: {"station_id": intermediate_station, "system_id": intermediate_system, "name": "Intermediate Station"},
            destination_station: {"station_id": destination_station, "system_id": destination_system, "name": "Destination Station"},
        }

        # Setup market orders: profitable deal from source to intermediate
        mock_repository.market_orders = {
            (source_region, type_id): [
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": source_station,
                },
            ],
            (intermediate_region, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": intermediate_station,
                },
            ],
        }

        mock_repository.item_types = {type_id: {"name": "Item 101", "volume": 1.0}}

        # Setup market groups
        mock_repository.market_groups_list = [1]
        mock_repository.market_groups_details = {
            1: {"types": [type_id], "parent_group_id": None}
        }

        result = await deals_service.find_system_to_system_deals(
            source_system, destination_system, min_profit_isk=5.0
        )

        # Should find deals for all route segments
        # Route segments: (source, intermediate), (source, destination), (intermediate, destination)
        assert result["from_system_id"] == source_system
        assert result["to_system_id"] == destination_system
        assert result["route"] == route
        assert len(result["route_segments"]) == 3
        assert (source_system, intermediate_system) in result["route_segments"]
        assert (source_system, destination_system) in result["route_segments"]
        assert (intermediate_system, destination_system) in result["route_segments"]
        # Should find at least one deal (source -> intermediate)
        assert len(result["deals"]) >= 1

    async def test_collect_types_for_deals_with_top_level_groups(
        self, deals_service, mock_repository
    ):
        """Test _collect_types_for_deals uses top-level groups when group_id is None"""
        # Setup market groups with hierarchy
        top_level_group_1 = 1
        top_level_group_2 = 2
        child_group_1 = 3  # child of group 1
        child_group_2 = 4  # child of group 2

        mock_repository.market_groups_list = [
            top_level_group_1,
            top_level_group_2,
            child_group_1,
            child_group_2,
        ]
        mock_repository.market_groups_details = {
            top_level_group_1: {
                "types": [101, 102],
                "parent_group_id": None,
            },
            top_level_group_2: {
                "types": [201, 202],
                "parent_group_id": None,
            },
            child_group_1: {
                "types": [103, 104],
                "parent_group_id": top_level_group_1,
            },
            child_group_2: {
                "types": [203, 204],
                "parent_group_id": top_level_group_2,
            },
        }

        # When group_id is None, should collect from all top-level groups
        all_types = await deals_service._collect_types_for_deals(group_id=None)

        # Should include types from top-level groups and their children
        # Top-level group 1: 101, 102, 103, 104 (via collect_all_types_from_group)
        # Top-level group 2: 201, 202, 203, 204 (via collect_all_types_from_group)
        assert len(all_types) == 8
        assert 101 in all_types
        assert 102 in all_types
        assert 103 in all_types
        assert 104 in all_types
        assert 201 in all_types
        assert 202 in all_types
        assert 203 in all_types
        assert 204 in all_types

    async def test_collect_types_for_deals_with_specific_group(
        self, deals_service, mock_repository
    ):
        """Test _collect_types_for_deals with a specific group_id"""
        group_id = 1
        child_group = 2

        mock_repository.market_groups_list = [group_id, child_group]
        mock_repository.market_groups_details = {
            group_id: {
                "types": [101, 102],
                "parent_group_id": None,
            },
            child_group: {
                "types": [103, 104],
                "parent_group_id": group_id,
            },
        }

        # When group_id is specified, should collect from that group and its children
        all_types = await deals_service._collect_types_for_deals(group_id=group_id)

        # Should include types from group and its children (via collect_all_types_from_group)
        assert len(all_types) == 4
        assert 101 in all_types
        assert 102 in all_types
        assert 103 in all_types
        assert 104 in all_types


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceAnalyzeTypeProfitability:
    """Additional tests for analyze_type_profitability"""

    @pytest.mark.parametrize(
        "max_transport_volume,expected_volume",
        [(None, 10), (5.0, 5), (20.0, 10), (0.5, None)],
    )
    async def test_analyze_type_profitability_with_max_transport_volume(
        self, deals_service, mock_repository, max_transport_volume, expected_volume
    ):
        """Test analyze_type_profitability with max_transport_volume"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ]
        }

        mock_repository.item_types = {type_id: {"name": "Test Item", "volume": 1.0}}
        mock_repository.system_details = {
            30000142: {"system_id": 30000142, "name": "Test System", "security_status": 0.9}
        }

        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=5.0, max_transport_volume=max_transport_volume
        )

        if expected_volume is None:
            assert result is None
        else:
            assert result is not None
            assert result["tradable_volume"] == expected_volume

    @pytest.mark.parametrize(
        "max_buy_cost,expected_volume",
        [(None, 10), (500.0, 5), (2000.0, 10), (50.0, None)],
    )
    async def test_analyze_type_profitability_with_max_buy_cost(
        self, deals_service, mock_repository, max_buy_cost, expected_volume
    ):
        """Test analyze_type_profitability with max_buy_cost"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ]
        }

        mock_repository.item_types = {type_id: {"name": "Test Item", "volume": 1.0}}
        mock_repository.system_details = {
            30000142: {"system_id": 30000142, "name": "Test System", "security_status": 0.9}
        }

        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=5.0, max_buy_cost=max_buy_cost
        )

        if expected_volume is None:
            assert result is None
        else:
            assert result is not None
            assert result["tradable_volume"] == expected_volume

    async def test_analyze_type_profitability_with_additional_regions(
        self, deals_service, mock_repository
    ):
        """Test analyze_type_profitability with additional_regions"""
        region_id = 10000002
        additional_region_id = 10000003
        type_id = 123

        # Best buy order in additional region, best sell order in main region
        mock_repository.market_orders = {
            (region_id, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ],
            (additional_region_id, type_id): [
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000143,
                },
            ],
        }

        mock_repository.item_types = {type_id: {"name": "Test Item", "volume": 1.0}}
        mock_repository.system_details = {
            30000142: {"system_id": 30000142, "name": "Test System 1", "security_status": 0.9},
            30000143: {"system_id": 30000143, "name": "Test System 2", "security_status": 0.9},
        }

        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=5.0, additional_regions=[additional_region_id]
        )

        assert result is not None
        assert result["buy_price"] == 100
        assert result["sell_price"] == 110
        assert result["buy_region_id"] == additional_region_id
        assert result["sell_region_id"] == region_id
