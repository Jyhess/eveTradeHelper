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
from .repository import EveRepository

logger = logging.getLogger(__name__)


class DealsService:
    """Domain service for finding deals (async)"""

    def __init__(self, repository: EveRepository):
        """
        Initialize the service with a repository

        Args:
            repository: Eve repository implementation
        """
        self.repository = repository

    async def _collect_orders_from_regions(
        self, region_ids: list[int], type_id: int
    ) -> tuple[list[tuple[dict[str, Any], int]], list[tuple[dict[str, Any], int]]]:
        # Fetch orders from all regions in parallel
        all_orders_promises = [
            self.repository.get_market_orders(reg_id, type_id) for reg_id in region_ids
        ]
        all_orders_results = await asyncio.gather(*all_orders_promises, return_exceptions=True)

        # Collect all valid orders from all regions
        all_buy_orders = []
        all_sell_orders = []

        for i, orders_result in enumerate(all_orders_results):
            if isinstance(orders_result, list):
                reg_id = region_ids[i]
                for order in orders_result:
                    order_with_region = (order, reg_id)
                    if order.get("is_buy_order", False):
                        all_buy_orders.append(order_with_region)
                    else:
                        all_sell_orders.append(order_with_region)

        return all_buy_orders, all_sell_orders

    async def _calculate_route_details(
        self, buy_location_id: int, sell_location_id: int, type_id: int
    ) -> tuple[int | None, int | None, int | None, list[dict[str, Any]]]:
        if not buy_location_id or not sell_location_id:
            return None, None, None, []

        try:
            buy_system_id = await get_system_id_from_location(self.repository, buy_location_id)
            sell_system_id = await get_system_id_from_location(self.repository, sell_location_id)

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

    @cached(cache_key_prefix="collect_all_types_from_group2")
    async def collect_all_types_from_group(self, group_id: int) -> set[int]:
        """
        Recursively collects all item types from a market group and its subgroups

        Args:
            group_id: Market group ID

        Returns:
            Set of item type IDs in the group and its subgroups
        """
        # Fetch all groups to build the parent tree
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
        # The @cached decorator normalizes to a list, but we return a set
        # The decorator will automatically convert it back to Set if needed via typing
        return result_set

    async def analyze_type_profitability(
        self,
        region_id: int,
        type_id: int,
        min_profit_isk: float,
        max_transport_volume: float | None = None,
        max_buy_cost: float | None = None,
        additional_regions: list[int] | None = None,
    ) -> dict[str, Any] | None:
        """
        Analyzes an item type to find profit opportunities
        Searches in the main region and additional regions to find the best profit

        Args:
            region_id: Main region ID
            type_id: Item type ID
            min_profit_isk: Minimum profit threshold in ISK
            max_transport_volume: Maximum transport volume allowed in m³ (None = unlimited)
            max_buy_cost: Maximum purchase amount in ISK (None = unlimited)
            additional_regions: List of additional region IDs to search (None = none)

        Returns:
            Dictionary with opportunity details if profit >= threshold, volume <= limit and cost <= limit,
            None otherwise
        """
        try:
            # Build the complete list of regions to search
            all_regions = [region_id]
            if additional_regions:
                all_regions.extend(additional_regions)

            # Collect orders from all regions
            all_buy_orders, all_sell_orders = await self._collect_orders_from_regions(
                all_regions, type_id
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
            profit_isk = (sell_price - buy_price) * tradable_volume
            total_buy_cost = buy_price * tradable_volume
            total_sell_revenue = sell_price * tradable_volume
            total_transport_volume = item_volume * tradable_volume

            # Filter according to minimum profit threshold
            if profit_isk < min_profit_isk:
                return None

            # Calculate profit percentage
            profit_percent = ((sell_price - buy_price) / buy_price) * 100

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
            estimated_time_minutes = jumps if jumps is not None else None

            # Count orders in all regions
            total_buy_order_count = len(all_buy_orders)
            total_sell_order_count = len(all_sell_orders)

            return {
                "type_id": type_id,
                "type_name": type_details.get("name", f"Type {type_id}"),
                "buy_price": buy_price,  # Price at which we BUY
                "sell_price": sell_price,  # Price at which we SELL
                "profit_percent": round(profit_percent, 2),
                "profit_isk": round(profit_isk, 2),
                "tradable_volume": tradable_volume,
                "item_volume": item_volume,  # Unit volume in m³
                "total_buy_cost": round(total_buy_cost, 2),
                "total_sell_revenue": round(total_sell_revenue, 2),
                "total_transport_volume": round(total_transport_volume, 2),
                "buy_order_count": total_buy_order_count,
                "sell_order_count": total_sell_order_count,
                "jumps": jumps,
                "estimated_time_minutes": estimated_time_minutes,
                "route_details": route_details,
                "buy_system_id": buy_system_id if buy_location_id else None,
                "sell_system_id": sell_system_id if sell_location_id else None,
                "buy_region_id": buy_region_id,
                "sell_region_id": sell_region_id,
            }
        except Exception as e:
            logger.warning(f"Error analyzing type {type_id}: {e}")
            return None

    async def find_market_deals(
        self,
        region_id: int,
        group_id: int,
        min_profit_isk: float = DEFAULT_MIN_PROFIT_ISK,
        max_transport_volume: float | None = None,
        max_buy_cost: float | None = None,
        additional_regions: list[int] | None = None,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT_ANALYSES,
    ) -> dict[str, Any]:
        """
        Finds deals in a market group for a region
        Iterates through all item types in the group (including subgroups) and calculates
        potential profit between best buy and sell orders in all specified regions

        Args:
            region_id: Main region ID
            group_id: Market group ID
            min_profit_isk: Minimum profit threshold in ISK (default: 100000.0)
            max_transport_volume: Maximum transport volume allowed in m³ (None = unlimited)
            max_buy_cost: Maximum purchase amount in ISK (None = unlimited)
            additional_regions: List of additional region IDs to search (None = none)
            max_concurrent: Maximum number of concurrent analyses (default: 20)

        Returns:
            Dictionary containing search results
        """
        regions_str = str(region_id)
        if additional_regions:
            regions_str += f" + {len(additional_regions)} other(s)"

        logger.info(
            f"Searching for deals in group {group_id} "
            f"in regions: {regions_str} (threshold: {min_profit_isk} ISK"
            f"{f', max volume: {max_transport_volume} m³' if max_transport_volume else ''}"
            f"{f', max buy amount: {max_buy_cost} ISK' if max_buy_cost else ''})"
        )

        # Collect all types from the group (and subgroups)
        # The @cached decorator returns a list, we convert it to Set
        all_types_list = await self.collect_all_types_from_group(group_id)
        all_types = set(all_types_list) if isinstance(all_types_list, list) else all_types_list

        if not all_types:
            return {
                "region_id": region_id,
                "group_id": group_id,
                "min_profit_isk": min_profit_isk,
                "max_transport_volume": max_transport_volume,
                "max_buy_cost": max_buy_cost,
                "total_types": 0,
                "deals": [],
            }

        logger.info(f"Found {len(all_types)} item types in group {group_id}")

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

        return {
            "region_id": region_id,
            "group_id": group_id,
            "min_profit_isk": min_profit_isk,
            "max_transport_volume": max_transport_volume,
            "max_buy_cost": max_buy_cost,
            "total_types": len(all_types),
            "total_profit_isk": round(total_profit_isk, 2),
            "deals": deals,
        }
