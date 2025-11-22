"""Additional tests for analyze_type_profitability"""

import pytest

from .utils_function import create_item_type, create_order, create_system_details


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
        # Use a real type ID from static data (e.g., from market group 61)
        type_id = 587  # Example: a real type ID from static data

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
            type_id: create_item_type(type_id=type_id, name="Test Item", volume=1.0)
        }
        mock_repository.system_details = {
            30000142: create_system_details(
                system_id=30000142, name="Test System", security_status=0.9
            )
        }

        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=5.0, max_transport_volume=max_transport_volume
        )

        if expected_volume is None:
            assert result is None
        else:
            assert result is not None
            assert result.tradable_volume == expected_volume

    @pytest.mark.parametrize(
        "max_buy_cost,expected_volume",
        [(None, 10), (500.0, 5), (2000.0, 10), (50.0, None)],
    )
    async def test_analyze_type_profitability_with_max_buy_cost(
        self, deals_service, mock_repository, max_buy_cost, expected_volume
    ):
        """Test analyze_type_profitability with max_buy_cost"""
        region_id = 10000002
        # Use a real type ID from static data
        type_id = 587  # Example: a real type ID from static data

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
            type_id: create_item_type(type_id=type_id, name="Test Item", volume=1.0)
        }
        mock_repository.system_details = {
            30000142: create_system_details(
                system_id=30000142, name="Test System", security_status=0.9
            )
        }

        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=5.0, max_buy_cost=max_buy_cost
        )

        if expected_volume is None:
            assert result is None
        else:
            assert result is not None
            assert result.tradable_volume == expected_volume

    async def test_analyze_type_profitability_with_additional_regions(
        self, deals_service, mock_repository
    ):
        """Test analyze_type_profitability with additional_regions"""
        region_id = 10000002
        additional_region_id = 10000003
        # Use a real type ID from static data
        type_id = 587  # Example: a real type ID from static data

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
            type_id: create_item_type(type_id=type_id, name="Test Item", volume=1.0)
        }
        mock_repository.system_details = {
            30000142: create_system_details(
                system_id=30000142, name="Test System 1", security_status=0.9
            ),
            30000143: create_system_details(
                system_id=30000143, name="Test System 2", security_status=0.9
            ),
        }

        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=5.0, additional_regions=[additional_region_id]
        )

        assert result is not None
        assert result.buy_price == 100
        assert result.sell_price == 110
        assert result.buy_region_id == additional_region_id
        assert result.sell_region_id == region_id

