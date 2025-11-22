"""Tests for complete deal search"""

import pytest

from domain.types import RouteDetail

from .utils_function import create_item_type, create_order, create_system_details


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceFindDeals:
    """Tests for complete deal search"""

    async def test_find_market_deals_empty_group(self, deals_service, mock_repository):
        """Test with an empty group"""
        # Use a non-existent group ID that doesn't exist in static data
        group_id = 99999999

        # Execute
        result = await deals_service.find_market_deals(
            10000002, group_ids=[group_id], min_profit_isk=5.0
        )

        # Verify
        assert result.region_id == 10000002
        assert result.group_id == group_id
        assert result.min_profit_isk == 5.0
        assert result.total_types == 0
        assert result.deals == []

    async def test_find_market_deals_without_group_id(
        self, deals_service, mock_repository, local_data_repository
    ):
        """Test find_market_deals with group_ids=None (all groups) using real static data"""
        region_id = 10000002
        profit_threshold = 5.0

        # Get a real type ID from static data (e.g., from market group 61)
        real_group_id = 61
        real_types = local_data_repository.get_types_for_group(real_group_id, include_children=False)
        assert len(real_types) > 0, "Market group 61 should have types in static data"
        type_id = list(real_types)[0]  # Use first type from real data

        # Setup orders: profitable
        mock_repository.market_orders = {
            (region_id, type_id): [
                create_order(
                    order_id=1,
                    type_id=type_id,
                    is_buy_order=True,
                    price=110,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
                create_order(
                    order_id=2,
                    type_id=type_id,
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
            ],
        }
        mock_repository.item_types = {
            type_id: create_item_type(type_id=type_id, name=f"Item {type_id}", volume=1.0)
        }

        # Execute with group_ids=None (uses all groups from static data)
        result = await deals_service.find_market_deals(
            region_id, group_ids=None, min_profit_isk=profit_threshold
        )

        # Verify
        assert result.region_id == region_id
        assert result.group_id is None  # Should not include group_id when None
        assert result.min_profit_isk == profit_threshold
        assert result.total_types > 0  # Should include types from all groups in static data
        # May or may not find deals depending on orders setup

    async def test_find_market_deals_with_profitable_items(
        self, deals_service, mock_repository, local_data_repository
    ):
        """Test with profitable items using real static data"""
        region_id = 10000002
        profit_threshold = 5.0

        # Use real market group 61 (Caldari Frigates) which has types
        group_id = 61
        real_types = local_data_repository.get_types_for_group(group_id, include_children=False)
        assert len(real_types) >= 2, "Market group 61 should have at least 2 types in static data"
        type_ids = sorted(list(real_types))[:3]  # Use first 3 types

        # Setup orders: type_ids[0] profitable, type_ids[1] non, type_ids[2] profitable
        mock_repository.market_orders = {
            (region_id, type_ids[0]): [
                create_order(
                    order_id=1,
                    type_id=type_ids[0],
                    is_buy_order=True,
                    price=110,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
                create_order(
                    order_id=2,
                    type_id=type_ids[0],
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),  # 10% profit, 100 ISK
            ],
            (region_id, type_ids[1]): [
                create_order(
                    order_id=3,
                    type_id=type_ids[1],
                    is_buy_order=True,
                    price=102,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
                create_order(
                    order_id=4,
                    type_id=type_ids[1],
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),  # 2% profit, 20 ISK
            ],
            (region_id, type_ids[2]): [
                create_order(
                    order_id=5,
                    type_id=type_ids[2],
                    is_buy_order=True,
                    price=120,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
                create_order(
                    order_id=6,
                    type_id=type_ids[2],
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),  # 20% profit, 200 ISK
            ],
        }

        # Setup types
        mock_repository.item_types = {
            type_ids[0]: create_item_type(type_id=type_ids[0], name=f"Item {type_ids[0]}", volume=1.0),
            type_ids[1]: create_item_type(type_id=type_ids[1], name=f"Item {type_ids[1]}", volume=1.0),
            type_ids[2]: create_item_type(type_id=type_ids[2], name=f"Item {type_ids[2]}", volume=1.0),
        }

        # Execute
        result = await deals_service.find_market_deals(
            region_id, group_ids=[group_id], min_profit_isk=profit_threshold
        )

        # Verify
        # Note: find_market_deals analyzes ALL types from market group 61 in static data
        # So total_types will be the total number of types in group 61, not just the 3 we configured
        expected_total_types = len(real_types)
        assert result.total_types == expected_total_types, (
            f"Expected {expected_total_types} types from market group 61, got {result.total_types}"
        )

        # Note: After 8% sale fee, type_ids[1] is not profitable:
        # - buy_cost = 1000, sell_revenue = 1020, fee = 81.6, net = 938.4, profit = -61.6
        # Only type_ids[0] and type_ids[2] are profitable after tax
        # Other types in the group will have no orders, so they won't be profitable
        assert len(result.deals) == 2, (
            f"Expected 2 profitable deals, got {len(result.deals)}. "
            f"Deals found: {[d.type_id for d in result.deals]}"
        )
        assert result.deals[0].type_id == type_ids[2]  # Sorted by profit ISK descending
        assert result.deals[0].profit_percent == pytest.approx(10.4, rel=0.01)  # After 8% tax
        assert result.deals[1].type_id == type_ids[0]  # 12 ISK after tax
        assert result.deals[1].profit_percent == pytest.approx(1.2, rel=0.01)  # After 8% tax

    async def test_find_market_deals_sorted_by_profit(
        self, deals_service, mock_repository, local_data_repository
    ):
        """Test that deals are sorted by profit descending using real static data"""
        region_id = 10000002

        # Use real market group 61 (Caldari Frigates) which has types
        group_id = 61
        real_types = local_data_repository.get_types_for_group(group_id, include_children=False)
        assert len(real_types) >= 3, "Market group 61 should have at least 3 types in static data"
        type_ids = sorted(list(real_types))[:3]  # Use first 3 types

        # Setup: different profits
        mock_repository.market_orders = {
            (region_id, type_ids[0]): [
                create_order(
                    order_id=1,
                    type_id=type_ids[0],
                    is_buy_order=True,
                    price=105,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),  # 5%, 50 ISK
                create_order(
                    order_id=2,
                    type_id=type_ids[0],
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
            ],
            (region_id, type_ids[1]): [
                create_order(
                    order_id=3,
                    type_id=type_ids[1],
                    is_buy_order=True,
                    price=115,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),  # 15%, 150 ISK
                create_order(
                    order_id=4,
                    type_id=type_ids[1],
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
            ],
            (region_id, type_ids[2]): [
                create_order(
                    order_id=5,
                    type_id=type_ids[2],
                    is_buy_order=True,
                    price=110,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),  # 10%, 100 ISK
                create_order(
                    order_id=6,
                    type_id=type_ids[2],
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
            ],
        }

        mock_repository.item_types = {
            type_ids[0]: create_item_type(type_id=type_ids[0], name=f"Item {type_ids[0]}", volume=1.0),
            type_ids[1]: create_item_type(type_id=type_ids[1], name=f"Item {type_ids[1]}", volume=1.0),
            type_ids[2]: create_item_type(type_id=type_ids[2], name=f"Item {type_ids[2]}", volume=1.0),
        }

        # Execute
        result = await deals_service.find_market_deals(
            region_id, group_ids=[group_id], min_profit_isk=5.0
        )

        # Verify: descending sort (after 8% sale fee)
        # type_ids[0]: buy=100, sell=105 → profit=-34 ISK (not profitable, filtered out)
        # type_ids[1]: buy=100, sell=115 → profit=58 ISK, percent=5.8%
        # type_ids[2]: buy=100, sell=110 → profit=12 ISK, percent=1.2%
        assert len(result.deals) == 2  # Only type_ids[1] and type_ids[2] are profitable (>= 5.0 ISK)
        assert result.deals[0].profit_percent == pytest.approx(5.8, rel=0.01)  # type_ids[1]
        assert result.deals[1].profit_percent == pytest.approx(1.2, rel=0.01)  # type_ids[2]

    @pytest.mark.parametrize(
        "max_transport_volume,expected_volume",
        [(None, 10), (5.0, 5), (20.0, 10), (0.5, 0)],
    )
    async def test_find_market_deals_with_max_transport_volume(
        self,
        deals_service,
        mock_repository,
        local_data_repository,
        max_transport_volume,
        expected_volume,
    ):
        """Test find_market_deals with max_transport_volume limit using real static data"""
        region_id = 10000002

        # Use real market group 61 (Caldari Frigates) which has types
        group_id = 61
        real_types = local_data_repository.get_types_for_group(group_id, include_children=False)
        assert len(real_types) > 0, "Market group 61 should have types in static data"
        type_id = list(real_types)[0]  # Use first type from real data

        mock_repository.market_orders = {
            (region_id, type_id): [
                create_order(
                    order_id=1,
                    type_id=type_id,
                    is_buy_order=True,
                    price=110,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
                create_order(
                    order_id=2,
                    type_id=type_id,
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
            ]
        }

        mock_repository.item_types = {
            type_id: create_item_type(type_id=type_id, name=f"Item {type_id}", volume=1.0)
        }
        mock_repository.system_details = {
            30000142: create_system_details(
                system_id=30000142, name="Test System", security_status=0.9
            )
        }

        result = await deals_service.find_market_deals(
            region_id,
            group_ids=[group_id],
            min_profit_isk=5.0,
            max_transport_volume=max_transport_volume,
        )

        if expected_volume == 0:
            assert len(result.deals) == 0
        else:
            assert len(result.deals) == 1
            assert result.deals[0].tradable_volume == expected_volume

    @pytest.mark.parametrize(
        "max_buy_cost,expected_volume",
        [(None, 10), (500.0, 5), (2000.0, 10), (50.0, 0)],
    )
    async def test_find_market_deals_with_max_buy_cost(
        self,
        deals_service,
        mock_repository,
        local_data_repository,
        max_buy_cost,
        expected_volume,
    ):
        """Test find_market_deals with max_buy_cost limit using real static data"""
        region_id = 10000002

        # Use real market group 61 (Caldari Frigates) which has types
        group_id = 61
        real_types = local_data_repository.get_types_for_group(group_id, include_children=False)
        assert len(real_types) > 0, "Market group 61 should have types in static data"
        type_id = list(real_types)[0]  # Use first type from real data

        mock_repository.market_orders = {
            (region_id, type_id): [
                create_order(
                    order_id=1,
                    type_id=type_id,
                    is_buy_order=True,
                    price=110,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
                create_order(
                    order_id=2,
                    type_id=type_id,
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
            ]
        }

        mock_repository.item_types = {
            type_id: create_item_type(type_id=type_id, name=f"Item {type_id}", volume=1.0)
        }
        mock_repository.system_details = {
            30000142: create_system_details(
                system_id=30000142, name="Test System", security_status=0.9
            )
        }

        result = await deals_service.find_market_deals(
            region_id, group_ids=[group_id], min_profit_isk=5.0, max_buy_cost=max_buy_cost
        )

        if expected_volume == 0:
            assert len(result.deals) == 0
        else:
            assert len(result.deals) == 1
            assert result.deals[0].tradable_volume == expected_volume

    async def test_find_market_deals_with_additional_regions(
        self, deals_service, mock_repository, local_data_repository
    ):
        """Test find_market_deals with additional_regions using real static data"""
        region_id = 10000002
        additional_region_id = 10000003

        # Use real market group 61 (Caldari Frigates) which has types
        group_id = 61
        real_types = local_data_repository.get_types_for_group(group_id, include_children=False)
        assert len(real_types) > 0, "Market group 61 should have types in static data"
        type_id = list(real_types)[0]  # Use first type from real data

        # Best buy order in additional region, best sell order in main region
        mock_repository.market_orders = {
            (region_id, type_id): [
                create_order(
                    order_id=1,
                    type_id=type_id,
                    is_buy_order=True,
                    price=110,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
            ],
            (additional_region_id, type_id): [
                create_order(
                    order_id=2,
                    type_id=type_id,
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000143,
                ),
            ],
        }

        mock_repository.item_types = {
            type_id: create_item_type(type_id=type_id, name=f"Item {type_id}", volume=1.0)
        }
        mock_repository.system_details = {
            30000142: create_system_details(
                system_id=30000142, name="Test System 1", security_status=0.9
            ),
            30000143: create_system_details(
                system_id=30000143, name="Test System 2", security_status=0.9
            ),
        }

        result = await deals_service.find_market_deals(
            region_id,
            group_ids=[group_id],
            min_profit_isk=5.0,
            additional_regions=[additional_region_id],
        )

        assert len(result.deals) == 1
        assert result.deals[0].type_id == type_id
        assert result.deals[0].buy_price == 100
        assert result.deals[0].sell_price == 110

