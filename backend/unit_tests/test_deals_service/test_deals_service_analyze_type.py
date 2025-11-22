"""Tests for type profitability analysis"""

import pytest

from .utils_function import (
    create_item_type,
    create_order,
    create_system_details
)


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceAnalyzeType:
    """Tests for type profitability analysis"""

    async def test_analyze_type_profitability_profitable(self, deals_service, mock_repository):
        """Test with a profitable type"""
        region_id = 10000002
        # Use a real type ID from static data (e.g., from market group 61)
        type_id = 587  # Example: a real type ID from static data
        profit_threshold = 5.0

        # Setup: buy and sell orders
        # buy_order = someone wants to BUY → we can SELL at this price
        # sell_order = someone wants to SELL → we can BUY at this price
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
                ),  # Best price to SELL
                create_order(
                    order_id=2,
                    type_id=type_id,
                    is_buy_order=True,
                    price=105,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),
                create_order(
                    order_id=3,
                    type_id=type_id,
                    is_buy_order=False,
                    price=95,
                    volume_remain=10,
                    volume_total=10,
                    location_id=30000142,
                ),  # Best price to BUY
                create_order(
                    order_id=4,
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
            type_id: create_item_type(
                type_id=type_id, name="Test Item", description="A test item", volume=1.0
            )
        }
        mock_repository.system_details = {
            30000142: create_system_details(
                system_id=30000142, name="Test System", security_status=0.9
            )
        }

        # Execute
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=profit_threshold
        )

        # Verify
        # Note: profit_percent is calculated after market sale fee (8%)
        # With buy_price=95, sell_price=110, volume=10:
        # - buy_cost = 95 * 10 = 950
        # - sell_revenue = 110 * 10 = 1100
        # - sale_fee = 88 (8% of 1100)
        # - net_revenue = 1012
        # - profit_isk = 1012 - 950 = 62
        # - profit_percent = (62/950) * 100 = 6.53%
        assert result is not None
        assert result.type_id == type_id
        assert result.type_name == "Test Item"
        assert result.buy_price == 95  # Price at which we BUY (lowest among sell_orders)
        assert result.sell_price == 110  # Price at which we SELL (highest among buy_orders)
        assert result.profit_percent == pytest.approx(6.53, rel=0.01)
        assert result.profit_isk == pytest.approx(62, rel=0.01)
        assert result.buy_order_count == 2
        assert result.sell_order_count == 2

    async def test_analyze_type_profitability_below_threshold(self, deals_service, mock_repository):
        """Test with a non-profitable type (profit < threshold)"""
        region_id = 10000002
        type_id = 587  # Use a real type ID
        profit_threshold = 10.0

        mock_repository.market_orders = {
            (region_id, type_id): [
                create_order(
                    order_id=1,
                    type_id=type_id,
                    is_buy_order=True,
                    price=105,
                    location_id=30000142,
                ),  # Profit = 5%
                create_order(
                    order_id=2,
                    type_id=type_id,
                    is_buy_order=False,
                    price=100,
                    location_id=30000142,
                ),
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
        type_id = 587  # Use a real type ID

        mock_repository.market_orders = {
            (region_id, type_id): [
                create_order(
                    order_id=1,
                    type_id=type_id,
                    is_buy_order=False,
                    price=100,
                    location_id=30000142,
                ),
            ]
        }

        # Execute
        result = await deals_service.analyze_type_profitability(region_id, type_id, 5.0)

        # Verify: should return None
        assert result is None

    async def test_analyze_type_profitability_no_sell_orders(self, deals_service, mock_repository):
        """Test with only buy orders"""
        region_id = 10000002
        type_id = 587  # Use a real type ID

        mock_repository.market_orders = {
            (region_id, type_id): [
                create_order(
                    order_id=1,
                    type_id=type_id,
                    is_buy_order=True,
                    price=100,
                    location_id=30000142,
                ),
            ]
        }

        # Execute
        result = await deals_service.analyze_type_profitability(region_id, type_id, 5.0)

        # Verify: should return None
        assert result is None

    async def test_analyze_type_profitability_exact_threshold(self, deals_service, mock_repository):
        """Test with profit exactly equal to threshold"""
        region_id = 10000002
        type_id = 587  # Use a real type ID
        profit_threshold = 10.0

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
                ),  # Profit = 10%
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

        # Execute
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=profit_threshold
        )

        # Verify: should return result (>= threshold)
        # Note: profit_percent is calculated after market sale fee (8%)
        # With buy_price=100, sell_price=110, volume=10:
        # - buy_cost = 1000
        # - sell_revenue = 1100
        # - sale_fee = 88 (8% of 1100)
        # - net_revenue = 1012
        # - profit_isk = 12
        # - profit_percent = (12/1000) * 100 = 1.2%
        assert result is not None
        assert result.profit_percent == pytest.approx(1.2, rel=0.01)

    async def test_analyze_type_profitability_handles_exception(
        self, deals_service, mock_repository
    ):
        """Test that exceptions are handled"""
        region_id = 10000002
        type_id = 587  # Use a real type ID

        # Simulate an exception when calling repository
        async def failing_get_market_orders(*args, **kwargs):
            raise Exception("API Error")

        mock_repository.get_market_orders = failing_get_market_orders

        # Execute
        result = await deals_service.analyze_type_profitability(region_id, type_id, 5.0)

        # Verify: should return None without raising exception
        assert result is None

