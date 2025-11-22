"""
Domain service for finding deals
Contains pure business logic, independent of infrastructure (async version)
"""

import asyncio
import logging
from typing import Any

from repositories.local_data import LocalDataRepository
from utils.cache import cached

from .constants import (
    DEFAULT_MAX_CONCURRENT_ANALYSES,
    DEFAULT_MIN_PROFIT_ISK,
    MARKET_SALE_FEE_PERCENT,
)
from .helpers import (
    apply_buy_cost_limit,
    calculate_tradable_volume,
    get_system_id_from_location,
)
from .location_validator import LocationValidator
from .orders_service import OrdersService
from .repository import EveRepository
from .types import (
    ContrabandSystem,
    Deal,
    MarketDealsResult,
    Order,
    RouteDetail,
    SystemToSystemDealsResult,
)

logger = logging.getLogger(__name__)


class DealsService:
    """Domain service for finding deals (async)"""

    def __init__(
        self,
        repository: EveRepository,
        location_validator: LocationValidator,
        orders_service: OrdersService,
        local_data_repository: LocalDataRepository | None = None,
    ):
        self.repository = repository
        self.location_validator = location_validator
        self.orders_service = orders_service
        self.local_data_repository = local_data_repository

    async def _collect_orders_from_regions(
        self, region_ids: list[int], type_id: int
    ) -> tuple[list[tuple[Order, int]], list[tuple[Order, int]]]:
        all_buy_orders, all_sell_orders = await self.orders_service.get_orders_for_regions(
            region_ids, type_id
        )

        return all_buy_orders, all_sell_orders

    async def _calculate_route_details(
        self, buy_location_id: int, sell_location_id: int, type_id: int
    ) -> tuple[int | None, int | None, int | None, list[RouteDetail]]:
        if not buy_location_id or not sell_location_id:
            return None, None, None, []

        try:
            buy_system_id = await get_system_id_from_location(
                buy_location_id, self.location_validator
            )
            sell_system_id = await get_system_id_from_location(
                sell_location_id, self.location_validator
            )

            if not buy_system_id or not sell_system_id:
                return buy_system_id, sell_system_id, None, []

            # Same system
            if buy_system_id == sell_system_id:
                system_data = await self.repository.get_system_details(buy_system_id)
                route_details = [
                    RouteDetail(
                        system_id=buy_system_id,
                        name=system_data.name,
                        security_status=system_data.security_status,
                        faction_id=None,
                    )
                ]
                return buy_system_id, sell_system_id, 0, route_details

            # Different systems, calculate route
            route_with_details = await self.repository.get_route_with_details(
                buy_system_id, sell_system_id
            )
            jumps = len(route_with_details) - 1 if route_with_details else None
            route_details = list(route_with_details) if route_with_details else []
            return buy_system_id, sell_system_id, jumps, route_details

        except Exception as e:
            logger.warning(f"Error calculating route for {type_id}: {e}")
            return None, None, None, []

    async def _check_contraband_in_route(
        self, type_id: int, route_details: list[RouteDetail]
    ) -> list[ContrabandSystem]:
        """Check which systems in the route consider this item as contraband"""
        if not self.local_data_repository:
            return []

        contraband_systems = []
        for system in route_details:
            if (
                system.faction_id is not None
                and self.local_data_repository.is_contraband_for_faction(type_id, system.faction_id)
            ):
                contraband_systems.append(
                    ContrabandSystem(
                        system_id=system.system_id,
                        system_name=system.name,
                        faction_id=system.faction_id,
                    )
                )

        return contraband_systems

    def _filter_valid_deals(self, results: list[Deal | None]) -> list[Deal]:
        return [r for r in results if r is not None]

    def _sort_deals_by_profit(self, deals: list[Deal]) -> list[Deal]:
        deals.sort(
            key=lambda x: (x.profit_isk, x.profit_percent),
            reverse=True,
        )
        return deals

    def _calculate_total_profit(self, deals: list[Deal]) -> float:
        return sum(deal.profit_isk for deal in deals)

    async def _filter_orders_by_system(
        self,
        all_buy_orders: list[tuple[Order, int]],
        all_sell_orders: list[tuple[Order, int]],
        from_system_id: int | None,
        to_system_id: int | None,
    ) -> tuple[list[tuple[dict[str, Any], int]], list[tuple[dict[str, Any], int]]]:
        """
        Filter orders by system ID if system filters are provided

        Args:
            all_buy_orders: List of buy orders (is_buy_order=True) with region_id
            all_sell_orders: List of sell orders (is_buy_order=False) with region_id
            from_system_id: System ID to filter buy orders (sell_orders) - None means no filter
            to_system_id: System ID to filter sell orders (buy_orders) - None means no filter

        Returns:
            Tuple of (filtered_buy_orders, filtered_sell_orders)
        """
        filtered_buy_orders = []
        filtered_sell_orders = []

        for order, region_id in all_sell_orders:
            if from_system_id is not None:
                location_id = order.location_id
                if location_id:
                    try:
                        order_system_id = await get_system_id_from_location(
                            location_id, self.location_validator
                        )
                        if order_system_id == from_system_id:
                            filtered_sell_orders.append((order, region_id))
                    except (ValueError, Exception):
                        continue
                else:
                    continue
            else:
                filtered_sell_orders.append((order, region_id))

        for order, region_id in all_buy_orders:
            if to_system_id is not None:
                location_id = order.location_id
                if location_id:
                    try:
                        order_system_id = await get_system_id_from_location(
                            location_id, self.location_validator
                        )
                        if order_system_id == to_system_id:
                            filtered_buy_orders.append((order, region_id))
                    except (ValueError, Exception):
                        continue
                else:
                    continue
            else:
                filtered_buy_orders.append((order, region_id))

        return filtered_buy_orders, filtered_sell_orders

    def _calculate_financial_values(
        self, buy_price: float, sell_price: float, tradable_volume: int, item_volume: float
    ) -> tuple[float, float, float, float, float]:
        """
        Calculate financial values for a deal
        Applies market sale fee (8%) on each sale

        Returns:
            Tuple of (profit_isk, total_buy_cost, total_sell_revenue, total_transport_volume, profit_percent)
        """
        total_buy_cost = buy_price * tradable_volume
        total_sell_revenue = sell_price * tradable_volume
        sale_fee = total_sell_revenue * MARKET_SALE_FEE_PERCENT
        net_sell_revenue = total_sell_revenue - sale_fee
        profit_isk = net_sell_revenue - total_buy_cost
        total_transport_volume = item_volume * tradable_volume
        profit_percent = (
            ((net_sell_revenue - total_buy_cost) / total_buy_cost) * 100
            if total_buy_cost > 0
            else 0.0
        )
        return (
            profit_isk,
            total_buy_cost,
            total_sell_revenue,
            total_transport_volume,
            profit_percent,
        )

    def _build_deal(
        self,
        type_id: int,
        type_name: str,
        buy_price: float,
        sell_price: float,
        tradable_volume: int,
        item_volume: float,
        profit_isk: float,
        total_buy_cost: float,
        total_sell_revenue: float,
        total_transport_volume: float,
        profit_percent: float,
        buy_order_count: int,
        sell_order_count: int,
        buy_system_id: int | None,
        sell_system_id: int | None,
        jumps: int | None,
        route_details: list[RouteDetail],
        buy_region_id: int | None = None,
        sell_region_id: int | None = None,
        contraband_systems: list[ContrabandSystem] | None = None,
    ) -> Deal:
        """
        Build a Deal object with all required fields

        Returns:
            Deal object containing deal information
        """
        return Deal(
            type_id=type_id,
            type_name=type_name,
            buy_price=buy_price,
            sell_price=sell_price,
            profit_percent=profit_percent,
            profit_isk=profit_isk,
            tradable_volume=tradable_volume,
            item_volume=item_volume,
            total_buy_cost=total_buy_cost,
            total_sell_revenue=total_sell_revenue,
            total_transport_volume=total_transport_volume,
            buy_order_count=buy_order_count,
            sell_order_count=sell_order_count,
            jumps=jumps,
            estimated_time_minutes=jumps if jumps is not None else None,
            route_details=route_details,
            buy_system_id=buy_system_id,
            sell_system_id=sell_system_id,
            contraband_systems=contraband_systems or [],
            is_contraband=len(contraband_systems or []) > 0,
            buy_region_id=buy_region_id,
            sell_region_id=sell_region_id,
        )

    @cached(cache_key_prefix="collect_all_types_from_group2")
    async def collect_all_types_from_group(self, group_id: int) -> set[int]:
        all_group_ids = await self.repository.get_market_groups_list()
        all_groups_data = await asyncio.gather(
            *[self.repository.get_market_group_details(gid) for gid in all_group_ids],
            return_exceptions=True,
        )

        groups_map = {}
        for i, group_data in enumerate(all_groups_data):
            gid = all_group_ids[i]
            if isinstance(group_data, Exception):
                continue
            groups_map[gid] = {
                "data": group_data,
                "types": group_data.types,
                "parent_id": group_data.parent_group_id,
                "children": [],
            }

        for gid, group_info in groups_map.items():
            parent_id = group_info["parent_id"]
            if parent_id and parent_id in groups_map:
                groups_map[parent_id]["children"].append(gid)

        def collect_all_types_recursive(gid: int, collected_types: set[int]) -> set[int]:
            """Recursively collects all types from a market group"""
            if gid not in groups_map:
                return collected_types

            group_info = groups_map[gid]
            collected_types.update(group_info["types"])

            for child_id in group_info["children"]:
                collect_all_types_recursive(child_id, collected_types)

            return collected_types

        result_set = collect_all_types_recursive(group_id, set())
        return result_set

    async def analyze_type_profitability(
        self,
        region_id: int,
        type_id: int,
        min_profit_isk: float,
        max_transport_volume: float | None = None,
        max_buy_cost: float | None = None,
        additional_regions: list[int] | None = None,
        from_system_id: int | None = None,
        to_system_id: int | None = None,
    ) -> Deal | None:
        try:
            # Build the complete list of regions to search
            all_regions = [region_id]
            if additional_regions:
                all_regions.extend(additional_regions)

            all_buy_orders, all_sell_orders = await self._collect_orders_from_regions(
                all_regions, type_id
            )

            if from_system_id is not None or to_system_id is not None:
                all_buy_orders, all_sell_orders = await self._filter_orders_by_system(
                    all_buy_orders, all_sell_orders, from_system_id, to_system_id
                )

            if not all_buy_orders or not all_sell_orders:
                return None

            best_sell_order_tuple = max(all_buy_orders, key=lambda x: x[0].price)
            best_sell_order, sell_region_id = best_sell_order_tuple
            sell_price = best_sell_order.price
            sell_location_id: int | None = best_sell_order.location_id
            sell_volume = min(
                best_sell_order.volume_remain,
                best_sell_order.volume_total,
            )

            best_buy_order_tuple = min(all_sell_orders, key=lambda x: x[0].price)
            best_buy_order, buy_region_id = best_buy_order_tuple
            buy_price = best_buy_order.price
            buy_location_id: int | None = best_buy_order.location_id
            buy_volume = min(
                best_buy_order.volume_remain,
                best_buy_order.volume_total,
            )

            if sell_price <= 0 or buy_price <= 0:
                return None

            type_details = await self.repository.get_item_type(type_id)
            item_volume = type_details.volume

            tradable_volume = calculate_tradable_volume(
                buy_volume, sell_volume, item_volume, max_transport_volume
            )
            if tradable_volume is None:
                return None

            tradable_volume = apply_buy_cost_limit(tradable_volume, buy_price, max_buy_cost)
            if tradable_volume is None:
                return None

            # Calculate financial values
            (
                profit_isk,
                total_buy_cost,
                total_sell_revenue,
                total_transport_volume,
                profit_percent,
            ) = self._calculate_financial_values(
                buy_price, sell_price, tradable_volume, item_volume
            )

            # Filter according to minimum profit threshold
            if profit_isk < min_profit_isk:
                return None

            # Calculate route details
            if buy_location_id is None or sell_location_id is None:
                buy_system_id = None
                sell_system_id = None
                jumps = None
                route_details: list[RouteDetail] = []
                contraband_systems: list[ContrabandSystem] = []
            else:
                (
                    buy_system_id,
                    sell_system_id,
                    jumps,
                    route_details,
                ) = await self._calculate_route_details(buy_location_id, sell_location_id, type_id)
                contraband_systems = await self._check_contraband_in_route(type_id, route_details)

            total_buy_order_count = len(all_buy_orders)
            total_sell_order_count = len(all_sell_orders)

            type_name = type_details.name
            if isinstance(type_name, dict):
                type_name = type_name.get("en") or type_name.get("fr") or f"Type {type_id}"
            if not isinstance(type_name, str) or not type_name:
                type_name = f"Type {type_id}"

            return self._build_deal(
                type_id=type_id,
                type_name=type_name if isinstance(type_name, str) else f"Type {type_id}",
                buy_price=buy_price,
                sell_price=sell_price,
                tradable_volume=tradable_volume,
                item_volume=item_volume,
                profit_isk=profit_isk,
                total_buy_cost=total_buy_cost,
                total_sell_revenue=total_sell_revenue,
                total_transport_volume=total_transport_volume,
                profit_percent=profit_percent,
                buy_order_count=total_buy_order_count,
                sell_order_count=total_sell_order_count,
                buy_system_id=buy_system_id if buy_location_id else None,
                sell_system_id=sell_system_id if sell_location_id else None,
                jumps=jumps,
                route_details=route_details,
                buy_region_id=buy_region_id,
                sell_region_id=sell_region_id,
                contraband_systems=contraband_systems,
            )
        except Exception as e:
            logger.warning(f"Error analyzing type {type_id}: {e}")
            return None

    async def find_market_deals(
        self,
        region_id: int,
        group_id: int | None = None,
        min_profit_isk: float = DEFAULT_MIN_PROFIT_ISK,
        max_transport_volume: float | None = None,
        max_buy_cost: float | None = None,
        additional_regions: list[int] | None = None,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT_ANALYSES,
    ) -> MarketDealsResult:
        regions_str = str(region_id)
        if additional_regions:
            regions_str += f" + {len(additional_regions)} other(s)"

        group_str = f"group {group_id}" if group_id is not None else "all groups"
        logger.info(
            f"Searching for deals in {group_str} "
            f"in regions: {regions_str} (threshold: {min_profit_isk} ISK"
            f"{f', max volume: {max_transport_volume} m³' if max_transport_volume else ''}"
            f"{f', max buy amount: {max_buy_cost} ISK' if max_buy_cost else ''})"
        )

        # Collect all types from the group (and subgroups)
        all_types = await self._collect_types_for_deals(group_id)

        if not all_types:
            return MarketDealsResult(
                region_id=region_id,
                min_profit_isk=min_profit_isk,
                max_transport_volume=max_transport_volume,
                max_buy_cost=max_buy_cost,
                total_types=0,
                total_profit_isk=0.0,
                deals=[],
                group_id=group_id,
            )

        group_str = f"group {group_id}" if group_id is not None else "all groups"
        logger.info(f"Found {len(all_types)} item types in {group_str}")

        # Analyze all types in parallel (limited to avoid overload)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_limit(type_id: int):
            async with semaphore:
                return await self.analyze_type_profitability(
                    region_id,
                    type_id,
                    min_profit_isk,
                    max_transport_volume,
                    max_buy_cost,
                    additional_regions,
                )

        results = await asyncio.gather(
            *[analyze_with_limit(type_id) for type_id in all_types],
            return_exceptions=True,
        )

        valid_results: list[Deal | None] = [r if isinstance(r, Deal) else None for r in results]
        deals = self._filter_valid_deals(valid_results)
        deals = self._sort_deals_by_profit(deals)
        total_profit_isk = self._calculate_total_profit(deals)

        logger.info(
            f"Found {len(deals)} deals with profit >= {min_profit_isk} ISK"
            f"{f', volume <= {max_transport_volume} m³' if max_transport_volume else ''}"
            f"{f', buy amount <= {max_buy_cost} ISK' if max_buy_cost else ''}"
        )

        return MarketDealsResult(
            region_id=region_id,
            min_profit_isk=min_profit_isk,
            max_transport_volume=max_transport_volume,
            max_buy_cost=max_buy_cost,
            total_types=len(all_types),
            total_profit_isk=total_profit_isk,
            deals=deals,
            group_id=group_id,
        )

    def _generate_route_segments(self, route: list[int]) -> list[tuple[int, int]]:
        """
        Generate all possible segments from a route

        For a route [A, B, C, D], generates:
        - (A, B), (A, C), (A, D)
        - (B, C), (B, D)
        - (C, D)

        Args:
            route: List of system IDs forming the route

        Returns:
            List of tuples (from_system_id, to_system_id) representing all segments
        """
        segments = []
        for i in range(len(route)):
            for j in range(i + 1, len(route)):
                segments.append((route[i], route[j]))
        return segments

    def _filter_deals_by_route_order(
        self,
        deals: list[Deal],
        expanded_route: list[int],
        original_route: list[int] | None = None,
    ) -> list[Deal]:
        """
        Filter deals to keep only those where buy_system_id and sell_system_id
        are in the expanded route and respect the order of the original route

        Args:
            deals: List of Deal objects
            expanded_route: List of system IDs forming the expanded route (includes detour systems)
            original_route: Optional original route for order checking (if None, uses expanded_route)

        Returns:
            Filtered list of deals
        """
        expanded_route_set = set(expanded_route)
        route_for_order = original_route if original_route is not None else expanded_route
        route_set_for_order = set(route_for_order)

        filtered_deals = []

        for deal in deals:
            buy_system_id = deal.buy_system_id
            sell_system_id = deal.sell_system_id

            if buy_system_id is None or sell_system_id is None:
                continue

            if buy_system_id not in expanded_route_set or sell_system_id not in expanded_route_set:
                continue

            # If both systems are in the original route, check order
            if buy_system_id in route_set_for_order and sell_system_id in route_set_for_order:
                buy_index = route_for_order.index(buy_system_id)
                sell_index = route_for_order.index(sell_system_id)
                if buy_index >= sell_index:
                    continue
            # If at least one system is a detour system, accept the deal
            # (we want to include deals involving detour systems)

            filtered_deals.append(deal)

        return filtered_deals

    @cached(cache_key_prefix="collect_types_for_deals")
    async def _collect_types_for_deals(self, group_id: int | None = None) -> set[int]:
        if group_id is not None:
            return await self.collect_all_types_from_group(group_id)

        all_group_ids = await self.repository.get_market_groups_list()
        all_groups_data = await asyncio.gather(
            *[self.repository.get_market_group_details(gid) for gid in all_group_ids],
            return_exceptions=True,
        )

        top_level_group_ids = []
        for i, group_data in enumerate(all_groups_data):
            if isinstance(group_data, Exception):
                continue
            if group_data.parent_group_id is None:
                top_level_group_ids.append(all_group_ids[i])

        all_types = set()
        for top_level_group_id in top_level_group_ids:
            group_types = await self.collect_all_types_from_group(top_level_group_id)
            all_types.update(group_types)

        return all_types

    async def _get_connected_system_ids(self, system_id: int) -> list[int]:
        """
        Get list of system IDs directly connected to a given system via stargates

        Args:
            system_id: System ID

        Returns:
            List of connected system IDs
        """
        try:
            system_data = await self.repository.get_system_details(system_id)
            stargate_ids = system_data.stargates or []

            if not stargate_ids:
                return []

            async def get_destination_system_id(stargate_id: int) -> int | None:
                try:
                    stargate_data = await self.repository.get_stargate_details(stargate_id)
                    return stargate_data.destination_system_id
                except Exception as e:
                    logger.warning(f"Error retrieving stargate {stargate_id}: {e}")
                    return None

            results = await asyncio.gather(
                *[get_destination_system_id(sid) for sid in stargate_ids],
                return_exceptions=True,
            )

            connected_systems = [
                sid for sid in results if isinstance(sid, int) and sid != system_id
            ]
            return connected_systems
        except Exception as e:
            logger.warning(f"Error getting connected systems for {system_id}: {e}")
            return []

    async def _expand_route_with_detour_systems(
        self, route: list[int], max_jumps: int
    ) -> list[int]:
        """
        Expand route to include systems at N jumps distance from each route system

        Uses BFS (breadth-first search) to find all systems within max_jumps
        from each system in the route.

        Args:
            route: List of system IDs forming the original route
            max_jumps: Maximum number of jumps to consider

        Returns:
            Expanded list of system IDs (route systems + detour systems)
        """
        if max_jumps <= 0:
            return route

        expanded_systems = set(route)

        async def find_systems_at_jumps(system_id: int, max_depth: int) -> set[int]:
            """
            Find all systems within max_depth jumps from system_id using BFS
            """
            found_systems = set()
            visited = set()
            queue = [(system_id, 0)]

            while queue:
                current_system, depth = queue.pop(0)

                if current_system in visited or depth > max_depth:
                    continue

                visited.add(current_system)
                found_systems.add(current_system)

                if depth < max_depth:
                    connected = await self._get_connected_system_ids(current_system)
                    for connected_system in connected:
                        if connected_system not in visited:
                            queue.append((connected_system, depth + 1))

            return found_systems

        for route_system in route:
            detour_systems = await find_systems_at_jumps(route_system, max_jumps)
            expanded_systems.update(detour_systems)

        expanded_list = list(expanded_systems)
        return expanded_list

    async def _calculate_and_expand_route(
        self, from_system_id: int, to_system_id: int, max_detour_jumps: int
    ) -> tuple[list[int], list[int]]:
        """
        Calculate route between systems and expand it with detour systems if needed

        Args:
            from_system_id: System ID where to start
            to_system_id: System ID where to end
            max_detour_jumps: Maximum number of jumps to consider for detour systems

        Returns:
            Tuple of (original_route, expanded_route)
        """
        route = await self.repository.get_route(from_system_id, to_system_id)
        if not route:
            return [], []

        original_route = route.copy()
        expanded_route = route

        if max_detour_jumps > 0:
            expanded_route = await self._expand_route_with_detour_systems(route, max_detour_jumps)
            logger.info(
                f"Route expanded from {len(route)} to {len(expanded_route)} systems "
                f"(max_detour_jumps={max_detour_jumps})"
            )

        return original_route, expanded_route

    async def _get_route_regions(
        self, expanded_route: list[int]
    ) -> tuple[dict[int, int], int | None, list[int]]:
        """
        Get region mapping and region IDs for systems in the expanded route

        Args:
            expanded_route: List of system IDs in the expanded route

        Returns:
            Tuple of (system_to_region mapping, from_region_id, additional_region_ids)
        """
        route_systems_data = await asyncio.gather(
            *[self.repository.get_system_details(system_id) for system_id in expanded_route],
            return_exceptions=True,
        )

        system_to_region: dict[int, int] = {}
        for i, system_data in enumerate(route_systems_data):
            system_id = expanded_route[i]
            if isinstance(system_data, Exception):
                continue
            constellation_id = system_data.constellation_id
            if constellation_id:
                try:
                    constellation = await self.repository.get_constellation_details(
                        constellation_id
                    )
                    region_id = constellation.region_id
                    if region_id:
                        system_to_region[system_id] = region_id
                except Exception as e:
                    logger.warning(f"Error getting region for system {system_id}: {e}")

        if not system_to_region:
            return {}, None, []

        all_region_ids = list(set(system_to_region.values()))
        first_system_id = expanded_route[0] if expanded_route else None
        from_region_id = system_to_region.get(first_system_id) if first_system_id else None
        additional_region_ids = [r for r in all_region_ids if r != from_region_id]

        return system_to_region, from_region_id, additional_region_ids

    async def _process_and_filter_deals(
        self,
        market_deals_result: MarketDealsResult,
        expanded_route: list[int],
        original_route: list[int],
        from_system_id: int,
        to_system_id: int,
        route_segments: list[tuple[int, int]],
        min_profit_isk: float,
        max_transport_volume: float | None,
        max_buy_cost: float | None,
    ) -> SystemToSystemDealsResult:
        """
        Process market deals result and filter by route order

        Args:
            market_deals_result: Result from find_market_deals
            expanded_route: Expanded route including detour systems
            original_route: Original route without detour systems
            from_system_id: System ID where to start
            to_system_id: System ID where to end
            route_segments: Route segments
            min_profit_isk: Minimum profit threshold
            max_transport_volume: Maximum transport volume
            max_buy_cost: Maximum buy cost

        Returns:
            SystemToSystemDealsResult with filtered deals and statistics
        """
        filtered_deals = self._filter_deals_by_route_order(
            market_deals_result.deals, expanded_route, original_route
        )
        filtered_deals = self._sort_deals_by_profit(filtered_deals)
        total_profit_isk = self._calculate_total_profit(filtered_deals)

        logger.info(
            f"Found {len(filtered_deals)} deals with profit >= {min_profit_isk} ISK "
            f"along route from system {from_system_id} to system {to_system_id} "
            f"({len(route_segments)} segments)"
            f"{f', volume <= {max_transport_volume} m³' if max_transport_volume else ''}"
            f"{f', buy amount <= {max_buy_cost} ISK' if max_buy_cost else ''}"
        )

        return SystemToSystemDealsResult(
            from_system_id=from_system_id,
            to_system_id=to_system_id,
            route=original_route,
            route_segments=route_segments,
            min_profit_isk=min_profit_isk,
            max_transport_volume=max_transport_volume,
            max_buy_cost=max_buy_cost,
            total_types=market_deals_result.total_types,
            total_profit_isk=total_profit_isk,
            deals=filtered_deals,
        )

    def _build_empty_result(
        self,
        from_system_id: int,
        to_system_id: int,
        route: list[int],
        route_segments: list[tuple[int, int]],
        min_profit_isk: float,
    ) -> SystemToSystemDealsResult:
        """
        Build empty result for error cases

        Args:
            from_system_id: System ID where to start
            to_system_id: System ID where to end
            route: Original route
            route_segments: Route segments
            min_profit_isk: Minimum profit threshold

        Returns:
            Empty SystemToSystemDealsResult
        """
        return SystemToSystemDealsResult(
            from_system_id=from_system_id,
            to_system_id=to_system_id,
            route=route,
            route_segments=route_segments,
            min_profit_isk=min_profit_isk,
            max_transport_volume=None,
            max_buy_cost=None,
            total_types=0,
            total_profit_isk=0.0,
            deals=[],
        )

    def _log_search_start(
        self,
        from_system_id: int,
        to_system_id: int,
        min_profit_isk: float,
        max_transport_volume: float | None,
        max_buy_cost: float | None,
        group_id: int | None,
        max_detour_jumps: int,
    ) -> None:
        """Log the start of a system-to-system deals search"""
        logger.info(
            f"Searching for deals along route from system {from_system_id} to system {to_system_id} "
            f"(threshold: {min_profit_isk} ISK"
            f"{f', max volume: {max_transport_volume} m³' if max_transport_volume else ''}"
            f"{f', max buy amount: {max_buy_cost} ISK' if max_buy_cost else ''}"
            f"{f', group: {group_id}' if group_id else ''}"
            f"{f', max detour jumps: {max_detour_jumps}' if max_detour_jumps > 0 else ''})"
        )

    async def find_system_to_system_deals(
        self,
        from_system_id: int,
        to_system_id: int,
        min_profit_isk: float = DEFAULT_MIN_PROFIT_ISK,
        max_transport_volume: float | None = None,
        max_buy_cost: float | None = None,
        group_id: int | None = None,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT_ANALYSES,
        max_detour_jumps: int = 0,
    ) -> SystemToSystemDealsResult:
        """
        Finds profitable deals along a route between two systems
        Calculates the route and searches for deals on all segments of the route

        For a route [source, A, B, C, destination], searches deals for:
        - source -> A, source -> B, source -> C, source -> destination
        - A -> B, A -> C, A -> destination
        - B -> C, B -> destination
        - C -> destination

        Args:
            from_system_id: System ID where to start (source)
            to_system_id: System ID where to end (destination)
            min_profit_isk: Minimum profit threshold in ISK (default: 100000.0)
            max_transport_volume: Maximum transport volume allowed in m³ (None = unlimited)
            max_buy_cost: Maximum purchase amount in ISK (None = unlimited)
            group_id: Market group ID to filter by (None = all groups)
            max_concurrent: Maximum number of concurrent analyses (default: 20)
            max_detour_jumps: Maximum number of jumps to consider systems connected to route systems (default: 0)

        Returns:
            Dictionary containing search results with deals from all route segments
        """
        self._log_search_start(
            from_system_id,
            to_system_id,
            min_profit_isk,
            max_transport_volume,
            max_buy_cost,
            group_id,
            max_detour_jumps,
        )

        original_route, expanded_route = await self._calculate_and_expand_route(
            from_system_id, to_system_id, max_detour_jumps
        )

        if not original_route:
            logger.warning(f"No route found between systems {from_system_id} and {to_system_id}")
            return self._build_empty_result(from_system_id, to_system_id, [], [], min_profit_isk)

        route_segments = self._generate_route_segments(original_route)
        logger.info(
            f"Route: {original_route} ({len(original_route)} systems, {len(route_segments)} segments)"
        )

        return await self._search_deals_for_route(
            expanded_route,
            original_route,
            route_segments,
            from_system_id,
            to_system_id,
            min_profit_isk,
            max_transport_volume,
            max_buy_cost,
            group_id,
            max_concurrent,
        )

    async def _search_deals_for_route(
        self,
        expanded_route: list[int],
        original_route: list[int],
        route_segments: list[tuple[int, int]],
        from_system_id: int,
        to_system_id: int,
        min_profit_isk: float,
        max_transport_volume: float | None,
        max_buy_cost: float | None,
        group_id: int | None,
        max_concurrent: int,
    ) -> SystemToSystemDealsResult:
        """
        Search for deals along the route

        Args:
            expanded_route: Expanded route including detour systems
            original_route: Original route without detour systems
            route_segments: Route segments
            from_system_id: System ID where to start
            to_system_id: System ID where to end
            min_profit_isk: Minimum profit threshold
            max_transport_volume: Maximum transport volume
            max_buy_cost: Maximum buy cost
            group_id: Market group ID
            max_concurrent: Maximum concurrent analyses

        Returns:
            Dictionary with search results
        """
        system_to_region, from_region_id, additional_region_ids = await self._get_route_regions(
            expanded_route
        )

        if not system_to_region or not from_region_id:
            logger.warning(f"Could not find regions for systems in route {original_route}")
            return self._build_empty_result(
                from_system_id, to_system_id, original_route, route_segments, min_profit_isk
            )

        market_deals_result = await self.find_market_deals(
            region_id=from_region_id,
            group_id=group_id,
            min_profit_isk=min_profit_isk,
            max_transport_volume=max_transport_volume,
            max_buy_cost=max_buy_cost,
            additional_regions=additional_region_ids if additional_region_ids else None,
            max_concurrent=max_concurrent,
        )

        return await self._process_and_filter_deals(
            market_deals_result,
            expanded_route,
            original_route,
            from_system_id,
            to_system_id,
            route_segments,
            min_profit_isk,
            max_transport_volume,
            max_buy_cost,
        )
