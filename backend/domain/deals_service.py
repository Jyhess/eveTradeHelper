"""
Domain service for finding deals
Contains pure business logic, independent of infrastructure (async version)
"""

import asyncio
import logging
from typing import Any

from utils.cache import cached

from .constants import (
    DEFAULT_MAX_CONCURRENT_ANALYSES,
    DEFAULT_MIN_PROFIT_ISK,
)
from .helpers import (
    apply_buy_cost_limit,
    calculate_tradable_volume,
    get_system_id_from_location,
)
from .location_validator import LocationValidator
from .orders_service import OrdersService
from .repository import EveRepository

logger = logging.getLogger(__name__)


class DealsService:
    """Domain service for finding deals (async)"""

    def __init__(
        self,
        repository: EveRepository,
        location_validator: LocationValidator,
        orders_service: OrdersService,
    ):
        self.repository = repository
        self.location_validator = location_validator
        self.orders_service = orders_service

    async def _collect_orders_from_regions(
        self, region_ids: list[int], type_id: int
    ) -> tuple[list[tuple[dict[str, Any], int]], list[tuple[dict[str, Any], int]]]:
        # Fetch orders from all regions using OrdersService (with caching and validation)
        # OrdersService already filters out invalid orders
        all_buy_orders, all_sell_orders = await self.orders_service.get_orders_for_regions(
            region_ids, type_id
        )

        return all_buy_orders, all_sell_orders

    async def _calculate_route_details(
        self, buy_location_id: int, sell_location_id: int, type_id: int
    ) -> tuple[int | None, int | None, int | None, list[dict[str, Any]]]:
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
                    {
                        "system_id": buy_system_id,
                        "name": system_data.get("name", f"Système {buy_system_id}"),
                        "security_status": system_data.get("security_status", 0.0),
                    }
                ]
                return buy_system_id, sell_system_id, 0, route_details

            # Different systems, calculate route
            route_with_details = await self.repository.get_route_with_details(
                buy_system_id, sell_system_id
            )
            jumps = len(route_with_details) - 1 if route_with_details else None
            return buy_system_id, sell_system_id, jumps, route_with_details or []

        except Exception as e:
            logger.warning(f"Error calculating route for {type_id}: {e}")
            return None, None, None, []

    def _filter_valid_deals(self, results: list[Any]) -> list[dict[str, Any]]:
        return [r for r in results if isinstance(r, dict) and r is not None]

    def _sort_deals_by_profit(self, deals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deals.sort(
            key=lambda x: (x.get("profit_isk", 0), x.get("profit_percent", 0)),
            reverse=True,
        )
        return deals

    def _calculate_total_profit(self, deals: list[dict[str, Any]]) -> float:
        return sum(deal.get("profit_isk", 0) for deal in deals)

    async def _filter_orders_by_system(
        self,
        all_buy_orders: list[tuple[dict[str, Any], int]],
        all_sell_orders: list[tuple[dict[str, Any], int]],
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

        # Filter sell_orders (is_buy_order=False) by from_system_id if provided
        # These are orders we can BUY from
        for order, region_id in all_sell_orders:
            if from_system_id is not None:
                location_id = order.get("location_id")
                if location_id:
                    try:
                        order_system_id = await get_system_id_from_location(
                            location_id, self.location_validator
                        )
                        if order_system_id == from_system_id:
                            filtered_sell_orders.append((order, region_id))
                    except (ValueError, Exception):
                        # Skip orders with invalid locations
                        continue
                else:
                    continue
            else:
                filtered_sell_orders.append((order, region_id))

        # Filter buy_orders (is_buy_order=True) by to_system_id if provided
        # These are orders we can SELL to
        for order, region_id in all_buy_orders:
            if to_system_id is not None:
                location_id = order.get("location_id")
                if location_id:
                    try:
                        order_system_id = await get_system_id_from_location(
                            location_id, self.location_validator
                        )
                        if order_system_id == to_system_id:
                            filtered_buy_orders.append((order, region_id))
                    except (ValueError, Exception):
                        # Skip orders with invalid locations
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

        Returns:
            Tuple of (profit_isk, total_buy_cost, total_sell_revenue, total_transport_volume, profit_percent)
        """
        profit_isk = (sell_price - buy_price) * tradable_volume
        total_buy_cost = buy_price * tradable_volume
        total_sell_revenue = sell_price * tradable_volume
        total_transport_volume = item_volume * tradable_volume
        profit_percent = ((sell_price - buy_price) / buy_price) * 100 if buy_price > 0 else 0.0
        return (
            profit_isk,
            total_buy_cost,
            total_sell_revenue,
            total_transport_volume,
            profit_percent,
        )

    def _build_deal_dict(
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
        route_details: list[dict[str, Any]],
        buy_region_id: int | None = None,
        sell_region_id: int | None = None,
    ) -> dict[str, Any]:
        """
        Build a deal dictionary with all required fields

        Returns:
            Dictionary containing deal information
        """
        deal = {
            "type_id": type_id,
            "type_name": type_name,
            "buy_price": buy_price,
            "sell_price": sell_price,
            "profit_percent": round(profit_percent, 2),
            "profit_isk": round(profit_isk, 2),
            "tradable_volume": tradable_volume,
            "item_volume": item_volume,
            "total_buy_cost": round(total_buy_cost, 2),
            "total_sell_revenue": round(total_sell_revenue, 2),
            "total_transport_volume": round(total_transport_volume, 2),
            "buy_order_count": buy_order_count,
            "sell_order_count": sell_order_count,
            "jumps": jumps,
            "estimated_time_minutes": jumps if jumps is not None else None,
            "route_details": route_details,
            "buy_system_id": buy_system_id,
            "sell_system_id": sell_system_id,
        }

        if buy_region_id is not None:
            deal["buy_region_id"] = buy_region_id
        if sell_region_id is not None:
            deal["sell_region_id"] = sell_region_id

        return deal

    @cached(cache_key_prefix="collect_all_types_from_group2")
    async def collect_all_types_from_group(self, group_id: int) -> set[int]:
        all_group_ids = await self.repository.get_market_groups_list()
        all_groups_data = await asyncio.gather(
            *[self.repository.get_market_group_details(gid) for gid in all_group_ids],
            return_exceptions=True,
        )

        # Construire un map des groupes avec leur parent_group_id
        groups_map = {}
        for i, group_data in enumerate(all_groups_data):
            if isinstance(group_data, dict):
                gid = all_group_ids[i]
                groups_map[gid] = {
                    "data": group_data,
                    "types": group_data.get("types", []),
                    "parent_id": group_data.get("parent_group_id"),
                    "children": [],
                }

        # Construire l'arbre des enfants
        for gid, group_info in groups_map.items():
            parent_id = group_info["parent_id"]
            if parent_id and parent_id in groups_map:
                groups_map[parent_id]["children"].append(gid)

        # Recursive function to collect all types
        def collect_all_types_recursive(gid: int, collected_types: set[int]) -> set[int]:
            """Recursively collects all types from a market group"""
            if gid not in groups_map:
                return collected_types

            group_info = groups_map[gid]
            collected_types.update(group_info["types"])

            # Recursively traverse subgroups
            for child_id in group_info["children"]:
                collect_all_types_recursive(child_id, collected_types)

            return collected_types

        # Collect all types from the group (and subgroups)
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
    ) -> dict[str, Any] | None:
        try:
            # Build the complete list of regions to search
            all_regions = [region_id]
            if additional_regions:
                all_regions.extend(additional_regions)

            # Collect orders from all regions
            all_buy_orders, all_sell_orders = await self._collect_orders_from_regions(
                all_regions, type_id
            )

            # Filter orders by system if system filters are provided
            if from_system_id is not None or to_system_id is not None:
                all_buy_orders, all_sell_orders = await self._filter_orders_by_system(
                    all_buy_orders, all_sell_orders, from_system_id, to_system_id
                )

            if not all_buy_orders or not all_sell_orders:
                return None

            # In Eve Online:
            # - buy_order (is_buy_order=True) = someone wants to BUY → we can SELL at this price
            # - sell_order (is_buy_order=False) = someone wants to SELL → we can BUY at this price

            # Best price to SELL (highest among all buy_orders)
            best_sell_order_tuple = max(all_buy_orders, key=lambda x: x[0].get("price", 0))
            best_sell_order, sell_region_id = best_sell_order_tuple
            sell_price = best_sell_order.get("price", 0)
            sell_location_id: int | None = best_sell_order.get("location_id")
            sell_volume = min(
                best_sell_order.get("volume_remain", 0),
                best_sell_order.get("volume_total", 0),
            )

            # Best price to BUY (lowest among all sell_orders)
            best_buy_order_tuple = min(
                all_sell_orders, key=lambda x: x[0].get("price", float("inf"))
            )
            best_buy_order, buy_region_id = best_buy_order_tuple
            buy_price = best_buy_order.get("price", float("inf"))
            buy_location_id: int | None = best_buy_order.get("location_id")
            buy_volume = min(
                best_buy_order.get("volume_remain", 0),
                best_buy_order.get("volume_total", 0),
            )

            if sell_price <= 0 or buy_price <= 0:
                return None

            # Fetch type details for unit volume
            type_details = await self.repository.get_item_type(type_id)
            item_volume = type_details.get("volume", 0.0)

            # Calculate tradable volume considering limits
            tradable_volume = calculate_tradable_volume(
                buy_volume, sell_volume, item_volume, max_transport_volume
            )
            if tradable_volume is None:
                return None

            # Apply buy cost limit if necessary
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
                route_details: list[dict[str, Any]] = []
            else:
                (
                    buy_system_id,
                    sell_system_id,
                    jumps,
                    route_details,
                ) = await self._calculate_route_details(buy_location_id, sell_location_id, type_id)

            # Count orders in all regions
            total_buy_order_count = len(all_buy_orders)
            total_sell_order_count = len(all_sell_orders)

            return self._build_deal_dict(
                type_id=type_id,
                type_name=type_details.get("name", f"Type {type_id}"),
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
    ) -> dict[str, Any]:
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
            result: dict[str, Any] = {
                "region_id": region_id,
                "min_profit_isk": min_profit_isk,
                "max_transport_volume": max_transport_volume,
                "max_buy_cost": max_buy_cost,
                "total_types": 0,
                "deals": [],
            }
            if group_id is not None:
                result["group_id"] = group_id
            return result

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

        deals = self._filter_valid_deals(results)
        deals = self._sort_deals_by_profit(deals)
        total_profit_isk = self._calculate_total_profit(deals)

        logger.info(
            f"Found {len(deals)} deals with profit >= {min_profit_isk} ISK"
            f"{f', volume <= {max_transport_volume} m³' if max_transport_volume else ''}"
            f"{f', buy amount <= {max_buy_cost} ISK' if max_buy_cost else ''}"
        )

        result = {
            "region_id": region_id,
            "min_profit_isk": min_profit_isk,
            "max_transport_volume": max_transport_volume,
            "max_buy_cost": max_buy_cost,
            "total_types": len(all_types),
            "total_profit_isk": round(total_profit_isk, 2),
            "deals": deals,
        }
        if group_id is not None:
            result["group_id"] = group_id
        return result

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
        self, deals: list[dict[str, Any]], route: list[int]
    ) -> list[dict[str, Any]]:
        """
        Filter deals to keep only those where buy_system_id and sell_system_id
        are in the route and in the correct order (buy_system comes before sell_system)

        Args:
            deals: List of deal dictionaries
            route: List of system IDs forming the route

        Returns:
            Filtered list of deals
        """
        route_set = set(route)
        filtered_deals = []

        for deal in deals:
            buy_system_id = deal.get("buy_system_id")
            sell_system_id = deal.get("sell_system_id")

            if buy_system_id is None or sell_system_id is None:
                continue

            if buy_system_id not in route_set or sell_system_id not in route_set:
                continue

            buy_index = route.index(buy_system_id)
            sell_index = route.index(sell_system_id)

            if buy_index < sell_index:
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
            if isinstance(group_data, dict):
                parent_group_id = group_data.get("parent_group_id")
                if parent_group_id is None:
                    top_level_group_ids.append(all_group_ids[i])

        all_types = set()
        for top_level_group_id in top_level_group_ids:
            group_types = await self.collect_all_types_from_group(top_level_group_id)
            all_types.update(group_types)

        return all_types

    async def find_system_to_system_deals(
        self,
        from_system_id: int,
        to_system_id: int,
        min_profit_isk: float = DEFAULT_MIN_PROFIT_ISK,
        max_transport_volume: float | None = None,
        max_buy_cost: float | None = None,
        group_id: int | None = None,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT_ANALYSES,
    ) -> dict[str, Any]:
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

        Returns:
            Dictionary containing search results with deals from all route segments
        """
        logger.info(
            f"Searching for deals along route from system {from_system_id} to system {to_system_id} "
            f"(threshold: {min_profit_isk} ISK"
            f"{f', max volume: {max_transport_volume} m³' if max_transport_volume else ''}"
            f"{f', max buy amount: {max_buy_cost} ISK' if max_buy_cost else ''}"
            f"{f', group: {group_id}' if group_id else ''})"
        )

        # Step 1: Calculate route between systems
        route = await self.repository.get_route(from_system_id, to_system_id)

        if not route:
            logger.warning(f"No route found between systems {from_system_id} and {to_system_id}")
            return {
                "from_system_id": from_system_id,
                "to_system_id": to_system_id,
                "route": [],
                "route_segments": [],
                "min_profit_isk": min_profit_isk,
                "total_types": 0,
                "deals": [],
            }

        # Generate all route segments
        route_segments = self._generate_route_segments(route)
        logger.info(f"Route: {route} ({len(route)} systems, {len(route_segments)} segments)")

        # Step 2: Find all regions present on the route
        route_systems_data = await asyncio.gather(
            *[self.repository.get_system_details(system_id) for system_id in route],
            return_exceptions=True,
        )

        # Build a map of system_id -> region_id
        system_to_region: dict[int, int] = {}
        for i, system_data in enumerate(route_systems_data):
            if isinstance(system_data, dict):
                system_id = route[i]
                constellation_id = system_data.get("constellation_id")
                if constellation_id:
                    try:
                        constellation = await self.repository.get_constellation_details(
                            constellation_id
                        )
                        region_id = constellation.get("region_id")
                        if region_id:
                            system_to_region[system_id] = region_id
                    except Exception as e:
                        logger.warning(f"Error getting region for system {system_id}: {e}")

        if not system_to_region:
            logger.warning(f"Could not find regions for systems in route {route}")
            return {
                "from_system_id": from_system_id,
                "to_system_id": to_system_id,
                "route": route,
                "route_segments": route_segments,
                "min_profit_isk": min_profit_isk,
                "total_types": 0,
                "deals": [],
            }

        # Collect all unique region IDs from the route
        all_region_ids = list(set(system_to_region.values()))
        from_region_id = system_to_region.get(from_system_id)
        additional_region_ids = [r for r in all_region_ids if r != from_region_id]

        if not from_region_id:
            logger.warning(f"Could not find region for source system {from_system_id}")
            return {
                "from_system_id": from_system_id,
                "to_system_id": to_system_id,
                "route": route,
                "route_segments": route_segments,
                "min_profit_isk": min_profit_isk,
                "total_types": 0,
                "deals": [],
            }

        # Step 3: Call find_market_deals with the route regions
        market_deals_result = await self.find_market_deals(
            region_id=from_region_id,
            group_id=group_id,
            min_profit_isk=min_profit_isk,
            max_transport_volume=max_transport_volume,
            max_buy_cost=max_buy_cost,
            additional_regions=additional_region_ids if additional_region_ids else None,
            max_concurrent=max_concurrent,
        )

        # Step 4: Filter deals where buy_system_id and sell_system_id are in route and in correct order
        all_deals = market_deals_result.get("deals", [])
        filtered_deals = self._filter_deals_by_route_order(all_deals, route)
        filtered_deals = self._sort_deals_by_profit(filtered_deals)
        total_profit_isk = self._calculate_total_profit(filtered_deals)

        logger.info(
            f"Found {len(filtered_deals)} deals with profit >= {min_profit_isk} ISK "
            f"along route from system {from_system_id} to system {to_system_id} "
            f"({len(route_segments)} segments)"
            f"{f', volume <= {max_transport_volume} m³' if max_transport_volume else ''}"
            f"{f', buy amount <= {max_buy_cost} ISK' if max_buy_cost else ''}"
        )

        return {
            "from_system_id": from_system_id,
            "to_system_id": to_system_id,
            "route": route,
            "route_segments": route_segments,
            "min_profit_isk": min_profit_isk,
            "max_transport_volume": max_transport_volume,
            "max_buy_cost": max_buy_cost,
            "total_types": market_deals_result.get("total_types", 0),
            "total_profit_isk": round(total_profit_isk, 2),
            "deals": filtered_deals,
        }
