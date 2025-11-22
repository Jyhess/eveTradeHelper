"""Tests for system-to-system deals"""

import pytest

from domain.types import RouteDetail

from .utils_function import (
    create_constellation_details,
    create_item_type,
    create_order,
    create_stargate_details,
    create_station_details,
    create_system_details,
)


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceSystemToSystem:
    """Tests for system-to-system deals"""

    async def test_find_system_to_system_deals_profitable(
        self, deals_service, mock_repository, local_data_repository
    ):
        """Test find_system_to_system_deals with profitable deal using real static data"""
        from_system_id = 30000142
        to_system_id = 30000143
        from_region_id = 10000002
        to_region_id = 10000003

        # Get a real type ID from static data (e.g., from market group 61)
        real_group_id = 61
        real_types = local_data_repository.get_types_for_group(real_group_id, include_children=False)
        assert len(real_types) > 0, "Market group 61 should have types in static data"
        type_id = list(real_types)[0]  # Use first type from real data

        # Setup system and constellation data
        mock_repository.system_details = {
            from_system_id: create_system_details(
                system_id=from_system_id,
                name="From System",
                constellation_id=20000001,
            ),
            to_system_id: create_system_details(
                system_id=to_system_id,
                name="To System",
                constellation_id=20000002,
            ),
        }

        mock_repository.constellation_details = {
            20000001: create_constellation_details(
                constellation_id=20000001, region_id=from_region_id
            ),
            20000002: create_constellation_details(
                constellation_id=20000002, region_id=to_region_id
            ),
        }

        # Setup station details for location validation
        # Use station IDs that are >= STATION_ID_THRESHOLD (60000000)
        from_station_id = 60008494  # Known valid station ID in static data
        to_station_id = 60008495  # Another known valid station ID (>= 60000000) in static data
        mock_repository.station_details = {
            from_station_id: create_station_details(
                station_id=from_station_id,
                system_id=from_system_id,
                name="From Station",
            ),
            to_station_id: create_station_details(
                station_id=to_station_id,
                system_id=to_system_id,
                name="To Station",
            ),
        }

        # Setup market orders
        mock_repository.market_orders = {
            (from_region_id, type_id): [
                create_order(
                    order_id=1,
                    type_id=type_id,
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=from_station_id,
                ),
            ],
            (to_region_id, type_id): [
                create_order(
                    order_id=2,
                    type_id=type_id,
                    is_buy_order=True,
                    price=110,
                    volume_remain=10,
                    volume_total=10,
                    location_id=to_station_id,
                ),
            ],
        }

        mock_repository.item_types = {
            type_id: create_item_type(type_id=type_id, name=f"Item {type_id}", volume=1.0)
        }
        # Setup route (direct connection)
        mock_repository.routes = {(from_system_id, to_system_id): [from_system_id, to_system_id]}
        mock_repository.route_with_details = {
            (from_system_id, to_system_id): [
                RouteDetail(
                    system_id=from_system_id,
                    name="From System",
                    security_status=0.9,
                    faction_id=None,
                ),
                RouteDetail(
                    system_id=to_system_id,
                    name="To System",
                    security_status=0.9,
                    faction_id=None,
                ),
            ]
        }

        # Execute with group_ids=None (uses all groups from static data)
        result = await deals_service.find_system_to_system_deals(
            from_system_id, to_system_id, min_profit_isk=5.0
        )

        assert result.from_system_id == from_system_id
        assert result.to_system_id == to_system_id
        assert result.route == [from_system_id, to_system_id]
        assert result.route_segments == [(from_system_id, to_system_id)]
        assert len(result.deals) == 1
        assert result.deals[0].type_id == type_id
        assert result.deals[0].buy_price == 100
        assert result.deals[0].sell_price == 110
        assert result.deals[0].jumps == 1

    async def test_find_system_to_system_deals_with_group_filter(
        self, deals_service, mock_repository, local_data_repository
    ):
        """Test find_system_to_system_deals with group_ids filter using real static data"""
        from_system_id = 30000142
        to_system_id = 30000143
        from_region_id = 10000002
        to_region_id = 10000003

        # Use real market group 61 (Caldari Frigates) which has types
        group_id = 61
        real_types = local_data_repository.get_types_for_group(group_id, include_children=False)
        assert len(real_types) >= 1, "Market group 61 should have at least 1 type in static data"
        type_id_in_group = list(real_types)[0]  # Use first type from real data

        # Get a type from a different group (e.g., group 5 - Standard Frigates) to test filtering
        other_group_id = 5
        other_group_types = local_data_repository.get_types_for_group(
            other_group_id, include_children=False
        )
        assert len(other_group_types) >= 1, "Market group 5 should have at least 1 type in static data"
        type_id_not_in_group = list(other_group_types)[0]  # Use first type from other group
        # Verify this type is not in group 61
        assert (
            type_id_not_in_group not in real_types
        ), f"Type {type_id_not_in_group} should not be in group {group_id}"

        # Setup system and constellation data
        mock_repository.system_details = {
            from_system_id: create_system_details(
                system_id=from_system_id,
                name="From System",
                constellation_id=20000001,
            ),
            to_system_id: create_system_details(
                system_id=to_system_id,
                name="To System",
                constellation_id=20000002,
            ),
        }

        mock_repository.constellation_details = {
            20000001: create_constellation_details(
                constellation_id=20000001, region_id=from_region_id
            ),
            20000002: create_constellation_details(
                constellation_id=20000002, region_id=to_region_id
            ),
        }

        # Setup station details
        from_station_id = 60008494  # Known valid station ID
        to_station_id = 60008495  # Another known valid station ID (>= 60000000)
        mock_repository.station_details = {
            from_station_id: create_station_details(
                station_id=from_station_id, system_id=from_system_id
            ),
            to_station_id: create_station_details(station_id=to_station_id, system_id=to_system_id),
        }

        # Setup market orders for both types
        mock_repository.market_orders = {
            (from_region_id, type_id_in_group): [
                create_order(
                    order_id=1,
                    type_id=type_id_in_group,
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=from_station_id,
                ),
            ],
            (to_region_id, type_id_in_group): [
                create_order(
                    order_id=2,
                    type_id=type_id_in_group,
                    is_buy_order=True,
                    price=110,
                    volume_remain=10,
                    volume_total=10,
                    location_id=to_station_id,
                ),
            ],
            (from_region_id, type_id_not_in_group): [
                create_order(
                    order_id=3,
                    type_id=type_id_not_in_group,
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=from_station_id,
                ),
            ],
            (to_region_id, type_id_not_in_group): [
                create_order(
                    order_id=4,
                    type_id=type_id_not_in_group,
                    is_buy_order=True,
                    price=110,
                    volume_remain=10,
                    volume_total=10,
                    location_id=to_station_id,
                ),
            ],
        }

        mock_repository.item_types = {
            type_id_in_group: create_item_type(
                type_id=type_id_in_group, name=f"Item {type_id_in_group}", volume=1.0
            ),
            type_id_not_in_group: create_item_type(
                type_id=type_id_not_in_group, name=f"Item {type_id_not_in_group}", volume=1.0
            ),
        }
        # Setup route (direct connection)
        mock_repository.routes = {(from_system_id, to_system_id): [from_system_id, to_system_id]}

        result = await deals_service.find_system_to_system_deals(
            from_system_id, to_system_id, min_profit_isk=5.0, group_ids=[group_id]
        )

        # Verify total_types is the number of types in group 61 (with children)
        expected_total_types = len(
            local_data_repository.get_types_for_group(group_id, include_children=True)
        )
        assert result.total_types == expected_total_types, (
            f"Expected {expected_total_types} types from market group {group_id} "
            f"(with children), got {result.total_types}"
        )

        # Should only find deals for type_id_in_group (filtered by group_id)
        # type_id_not_in_group should be filtered out because it's not in group 61
        assert len(result.deals) == 1, (
            f"Expected 1 deal, got {len(result.deals)}. "
            f"Deals found: {[d.type_id for d in result.deals]}"
        )
        assert result.deals[0].type_id == type_id_in_group

    async def test_find_system_to_system_deals_with_max_detour_jumps_zero(
        self, deals_service, mock_repository, local_data_repository
    ):
        """Test find_system_to_system_deals with max_detour_jumps=0 using real static data"""
        from_system_id = 30000142
        to_system_id = 30000143
        detour_system_id = 30000144
        from_region_id = 10000002
        to_region_id = 10000003

        # Get a real type ID from static data
        real_group_id = 61
        real_types = local_data_repository.get_types_for_group(real_group_id, include_children=False)
        assert len(real_types) > 0, "Market group 61 should have types in static data"
        type_id = list(real_types)[0]  # Use first type from real data

        mock_repository.system_details = {
            from_system_id: create_system_details(
                system_id=from_system_id,
                name="From System",
                constellation_id=20000001,
            ),
            to_system_id: create_system_details(
                system_id=to_system_id,
                name="To System",
                constellation_id=20000002,
            ),
            detour_system_id: create_system_details(
                system_id=detour_system_id,
                name="Detour System",
                constellation_id=20000001,
            ),
        }

        mock_repository.constellation_details = {
            20000001: create_constellation_details(
                constellation_id=20000001, region_id=from_region_id
            ),
            20000002: create_constellation_details(
                constellation_id=20000002, region_id=to_region_id
            ),
        }

        from_station_id = 60008494
        to_station_id = 60000004
        detour_station_id = 60000005
        mock_repository.station_details = {
            from_station_id: create_station_details(
                station_id=from_station_id, system_id=from_system_id
            ),
            to_station_id: create_station_details(station_id=to_station_id, system_id=to_system_id),
            detour_station_id: create_station_details(
                station_id=detour_station_id, system_id=detour_system_id
            ),
        }

        mock_repository.market_orders = {
            (from_region_id, type_id): [
                create_order(
                    order_id=1,
                    type_id=type_id,
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=from_station_id,
                ),
            ],
            (to_region_id, type_id): [
                create_order(
                    order_id=2,
                    type_id=type_id,
                    is_buy_order=True,
                    price=110,
                    volume_remain=10,
                    volume_total=10,
                    location_id=to_station_id,
                ),
            ],
        }

        mock_repository.item_types = {
            type_id: create_item_type(type_id=type_id, name=f"Item {type_id}", volume=1.0)
        }
        mock_repository.routes = {(from_system_id, to_system_id): [from_system_id, to_system_id]}

        stargate_id = 50000001
        mock_repository.system_connections = {
            from_system_id: [stargate_id],
        }
        mock_repository.stargate_details = {
            stargate_id: create_stargate_details(
                stargate_id=stargate_id,
                system_id=from_system_id,
                destination_system_id=detour_system_id,
            ),
        }

        result = await deals_service.find_system_to_system_deals(
            from_system_id, to_system_id, min_profit_isk=5.0, max_detour_jumps=0
        )

        assert result.from_system_id == from_system_id
        assert result.to_system_id == to_system_id
        assert result.route == [from_system_id, to_system_id]
        assert len(result.deals) == 1
        assert result.deals[0].buy_system_id == from_system_id
        assert result.deals[0].sell_system_id == to_system_id

    async def test_find_system_to_system_deals_with_max_detour_jumps_one(
        self, deals_service, mock_repository, local_data_repository
    ):
        """Test find_system_to_system_deals with max_detour_jumps=1 using real static data"""
        from_system_id = 30000142
        to_system_id = 30000143
        detour_system_id = 30000144
        from_region_id = 10000002
        to_region_id = 10000003

        # Get a real type ID from static data
        real_group_id = 61
        real_types = local_data_repository.get_types_for_group(real_group_id, include_children=False)
        assert len(real_types) > 0, "Market group 61 should have types in static data"
        type_id = list(real_types)[0]  # Use first type from real data

        mock_repository.system_details = {
            from_system_id: create_system_details(
                system_id=from_system_id,
                name="From System",
                constellation_id=20000001,
            ),
            to_system_id: create_system_details(
                system_id=to_system_id,
                name="To System",
                constellation_id=20000002,
            ),
            detour_system_id: create_system_details(
                system_id=detour_system_id,
                name="Detour System",
                constellation_id=20000001,
            ),
        }

        mock_repository.constellation_details = {
            20000001: create_constellation_details(
                constellation_id=20000001, region_id=from_region_id
            ),
            20000002: create_constellation_details(
                constellation_id=20000002, region_id=to_region_id
            ),
        }

        from_station_id = 60008494
        detour_station_id = 60000005
        mock_repository.station_details = {
            from_station_id: create_station_details(
                station_id=from_station_id, system_id=from_system_id
            ),
            detour_station_id: create_station_details(
                station_id=detour_station_id, system_id=detour_system_id
            ),
        }

        mock_repository.market_orders = {
            (from_region_id, type_id): [
                create_order(
                    order_id=1,
                    type_id=type_id,
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=from_station_id,
                ),
            ],
            (to_region_id, type_id): [
                create_order(
                    order_id=2,
                    type_id=type_id,
                    is_buy_order=True,
                    price=110,
                    volume_remain=10,
                    volume_total=10,
                    location_id=detour_station_id,
                ),
            ],
        }

        mock_repository.item_types = {
            type_id: create_item_type(type_id=type_id, name=f"Item {type_id}", volume=1.0)
        }
        mock_repository.routes = {(from_system_id, to_system_id): [from_system_id, to_system_id]}

        stargate_id = 50000001
        mock_repository.system_connections = {
            from_system_id: [stargate_id],
        }
        mock_repository.stargate_details = {
            stargate_id: create_stargate_details(
                stargate_id=stargate_id,
                system_id=from_system_id,
                destination_system_id=detour_system_id,
            ),
        }

        result = await deals_service.find_system_to_system_deals(
            from_system_id, to_system_id, min_profit_isk=5.0, max_detour_jumps=1
        )

        assert result.from_system_id == from_system_id
        assert result.to_system_id == to_system_id
        assert result.route == [from_system_id, to_system_id]
        assert (
            detour_system_id == result.deals[0].buy_system_id
            or detour_system_id == result.deals[0].sell_system_id
            or any(
                deal.buy_system_id == detour_system_id or deal.sell_system_id == detour_system_id
                for deal in result.deals
            )
        )

    async def test_find_system_to_system_deals_no_constellation(
        self, deals_service, mock_repository
    ):
        """Test find_system_to_system_deals when constellation is missing"""
        from_system_id = 30000142
        to_system_id = 30000143

        mock_repository.system_details = {
            from_system_id: create_system_details(system_id=from_system_id, name="From System"),
            to_system_id: create_system_details(system_id=to_system_id, name="To System"),
        }

        result = await deals_service.find_system_to_system_deals(
            from_system_id, to_system_id, min_profit_isk=5.0
        )

        assert result.from_system_id == from_system_id
        assert result.to_system_id == to_system_id
        assert result.total_types == 0
        assert result.deals == []

    async def test_find_system_to_system_deals_with_volume_limit(
        self, deals_service, mock_repository, local_data_repository
    ):
        """Test find_system_to_system_deals with max_transport_volume using real static data"""
        from_system_id = 30000142
        to_system_id = 30000143
        from_region_id = 10000002
        to_region_id = 10000003

        # Get a real type ID from static data
        real_group_id = 61
        real_types = local_data_repository.get_types_for_group(real_group_id, include_children=False)
        assert len(real_types) > 0, "Market group 61 should have types in static data"
        type_id = list(real_types)[0]  # Use first type from real data

        mock_repository.system_details = {
            from_system_id: create_system_details(
                system_id=from_system_id,
                name="From System",
                constellation_id=20000001,
            ),
            to_system_id: create_system_details(
                system_id=to_system_id,
                name="To System",
                constellation_id=20000002,
            ),
        }

        mock_repository.constellation_details = {
            20000001: create_constellation_details(
                constellation_id=20000001, region_id=from_region_id
            ),
            20000002: create_constellation_details(
                constellation_id=20000002, region_id=to_region_id
            ),
        }

        # Use station IDs that are >= STATION_ID_THRESHOLD (60000000)
        from_station_id = 60008494  # Known valid station ID
        to_station_id = 60008495  # Another known valid station ID (>= 60000000)
        mock_repository.station_details = {
            from_station_id: create_station_details(
                station_id=from_station_id, system_id=from_system_id
            ),
            to_station_id: create_station_details(station_id=to_station_id, system_id=to_system_id),
        }

        # Price calculation: with volume 2.0, max_transport_volume 5.0, we can transport 2 units
        # To have profit >= 5.0 ISK after 8% sale fee:
        # Profit = (sell_price - buy_price) * volume - sell_price * volume * 0.08
        # 5.0 <= (sell_price - buy_price) * 2 - sell_price * 2 * 0.08
        # 5.0 <= 2 * sell_price - 2 * buy_price - 0.16 * sell_price
        # 5.0 <= 1.84 * sell_price - 2 * buy_price
        # With buy_price = 100: 5.0 <= 1.84 * sell_price - 200
        # sell_price >= (5.0 + 200) / 1.84 = 111.41
        # Let's use sell_price = 115 to have a clear margin
        # Profit = (115 - 100) * 2 - 115 * 2 * 0.08 = 30 - 18.4 = 11.6 ISK
        mock_repository.market_orders = {
            (from_region_id, type_id): [
                create_order(
                    order_id=1,
                    type_id=type_id,
                    is_buy_order=False,
                    price=100,
                    location_id=from_station_id,
                    volume_remain=10,
                    volume_total=10,
                ),
            ],
            (to_region_id, type_id): [
                create_order(
                    order_id=2,
                    type_id=type_id,
                    is_buy_order=True,
                    price=115,
                    location_id=to_station_id,
                    volume_remain=10,
                    volume_total=10,
                ),
            ],
        }

        # Item volume is 2.0, max_transport_volume is 5.0, so max tradable is 2
        mock_repository.item_types = {
            type_id: create_item_type(type_id=type_id, name=f"Item {type_id}", volume=2.0)
        }
        # Setup route (direct connection)
        mock_repository.routes = {(from_system_id, to_system_id): [from_system_id, to_system_id]}

        result = await deals_service.find_system_to_system_deals(
            from_system_id, to_system_id, min_profit_isk=5.0, max_transport_volume=5.0
        )

        assert len(result.deals) == 1
        assert result.deals[0].tradable_volume == 2

    async def test_find_system_to_system_deals_with_multiple_segments(
        self, deals_service, mock_repository, local_data_repository
    ):
        """Test find_system_to_system_deals with a route containing multiple systems using real static data"""
        source_system = 30000142
        intermediate_system = 30000143
        destination_system = 30000144
        source_region = 10000002
        intermediate_region = 10000003
        destination_region = 10000004

        # Get a real type ID from static data
        real_group_id = 61
        real_types = local_data_repository.get_types_for_group(real_group_id, include_children=False)
        assert len(real_types) > 0, "Market group 61 should have types in static data"
        type_id = list(real_types)[0]  # Use first type from real data

        # Setup route: source -> intermediate -> destination
        route = [source_system, intermediate_system, destination_system]
        mock_repository.routes = {(source_system, destination_system): route}

        # Setup system and constellation data
        mock_repository.system_details = {
            source_system: create_system_details(
                system_id=source_system,
                name="Source System",
                constellation_id=20000001,
            ),
            intermediate_system: create_system_details(
                system_id=intermediate_system,
                name="Intermediate System",
                constellation_id=20000002,
            ),
            destination_system: create_system_details(
                system_id=destination_system,
                name="Destination System",
                constellation_id=20000003,
            ),
        }

        mock_repository.constellation_details = {
            20000001: create_constellation_details(
                constellation_id=20000001, region_id=source_region
            ),
            20000002: create_constellation_details(
                constellation_id=20000002, region_id=intermediate_region
            ),
            20000003: create_constellation_details(
                constellation_id=20000003, region_id=destination_region
            ),
        }

        # Setup stations
        source_station = 60008494
        intermediate_station = 60000004
        destination_station = 60000005
        mock_repository.station_details = {
            source_station: create_station_details(
                station_id=source_station,
                system_id=source_system,
                name="Source Station",
            ),
            intermediate_station: create_station_details(
                station_id=intermediate_station,
                system_id=intermediate_system,
                name="Intermediate Station",
            ),
            destination_station: create_station_details(
                station_id=destination_station,
                system_id=destination_system,
                name="Destination Station",
            ),
        }

        # Setup market orders: profitable deal from source to intermediate
        mock_repository.market_orders = {
            (source_region, type_id): [
                create_order(
                    order_id=1,
                    type_id=type_id,
                    is_buy_order=False,
                    price=100,
                    volume_remain=10,
                    volume_total=10,
                    location_id=source_station,
                ),
            ],
            (intermediate_region, type_id): [
                create_order(
                    order_id=2,
                    type_id=type_id,
                    is_buy_order=True,
                    price=110,
                    volume_remain=10,
                    volume_total=10,
                    location_id=intermediate_station,
                ),
            ],
        }

        mock_repository.item_types = {
            type_id: create_item_type(type_id=type_id, name=f"Item {type_id}", volume=1.0)
        }

        result = await deals_service.find_system_to_system_deals(
            source_system, destination_system, min_profit_isk=5.0
        )

        # Should find deals for all route segments
        # Route segments: (source, intermediate), (source, destination), (intermediate, destination)
        assert result.from_system_id == source_system
        assert result.to_system_id == destination_system
        assert result.route == route
        assert len(result.route_segments) == 3
        assert (source_system, intermediate_system) in result.route_segments
        assert (source_system, destination_system) in result.route_segments
        assert (intermediate_system, destination_system) in result.route_segments
        # Should find at least one deal (source -> intermediate)
        assert len(result.deals) >= 1

