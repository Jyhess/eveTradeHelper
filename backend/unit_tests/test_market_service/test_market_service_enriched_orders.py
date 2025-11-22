"""
Unit tests for MarketService - Enriched Orders
Tests business logic with repository mocks
"""

from typing import Any

import pytest

from unit_tests.test_market_service.test_market_service_fixtures import (
    market_service,
    mock_repository,
)


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

    async def test_get_enriched_market_orders_respects_limit(
        self, market_service, mock_repository
    ):
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

