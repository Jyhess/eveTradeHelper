import pytest


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

