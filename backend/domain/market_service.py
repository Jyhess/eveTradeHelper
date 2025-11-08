"""
Domain service for market management
Contains pure business logic, independent of infrastructure (async version)
"""

import asyncio
import logging
from typing import Any

from .constants import DEFAULT_MARKET_ORDERS_LIMIT
from .helpers import is_station
from .repository import EveRepository

logger = logging.getLogger(__name__)


class MarketService:
    """Domain service for market management (async)"""

    def __init__(self, repository: EveRepository):
        """
        Initialize the service with a repository

        Args:
            repository: Eve repository implementation
        """
        self.repository = repository

    async def get_market_categories(self) -> list[dict[str, Any]]:
        """
        Retrieves the list of market categories with their details
        Business logic: orchestration of repository calls (parallelized)

        Returns:
            List of formatted categories, sorted by name
        """
        # Fetch the list of market groups
        group_ids = await self.repository.get_market_groups_list()

        # Fetch details of each group in parallel
        async def fetch_group(group_id: int) -> dict[str, Any] | None:
            try:
                group_data = await self.repository.get_market_group_details(group_id)
                return {
                    "group_id": group_id,
                    "name": group_data.get("name", "Unknown"),
                    "description": group_data.get("description", ""),
                    "parent_group_id": group_data.get("parent_group_id"),
                    "types": group_data.get("types", []),
                }
            except Exception as e:
                logger.warning(f"Error retrieving group {group_id}: {e}")
                return None

        results = await asyncio.gather(*[fetch_group(gid) for gid in group_ids])

        # Filter None results and sort by name
        categories = sorted([c for c in results if c is not None], key=lambda x: x.get("name", ""))

        return categories

    async def get_item_type(self, type_id: int) -> dict[str, Any]:
        return await self.repository.get_item_type(type_id)

    async def get_enriched_market_orders(
        self,
        region_id: int,
        type_id: int | None = None,
        limit: int = DEFAULT_MARKET_ORDERS_LIMIT,
    ) -> dict[str, Any]:
        """
        Retrieves enriched market orders for a region
        Business logic: sorting, limiting and enriching orders

        Args:
            region_id: Region ID
            type_id: Optional, item type ID to filter orders
            limit: Maximum number of orders per type (buy/sell) to return

        Returns:
            Dictionary containing enriched buy and sell orders
        """
        # Fetch orders from repository
        orders = await self.repository.get_market_orders(region_id, type_id)

        # Separate buy and sell orders
        buy_orders = [o for o in orders if o.get("is_buy_order", False)]
        sell_orders = [o for o in orders if not o.get("is_buy_order", False)]

        # Sort by price (best price first)
        buy_orders.sort(key=lambda x: x.get("price", 0), reverse=True)
        sell_orders.sort(key=lambda x: x.get("price", 0))

        # Limit to N best orders to avoid too many API calls
        buy_orders = buy_orders[:limit]
        sell_orders = sell_orders[:limit]

        # Enrich orders with system and station names
        async def enrich_order(order: dict[str, Any]) -> dict[str, Any]:
            """Enriches an order with system and station names"""
            location_id = order.get("location_id")
            if not location_id:
                return order

            enriched_order = order.copy()

            # IDs >= STATION_ID_THRESHOLD are stations, otherwise they are systems
            if is_station(location_id):
                # It's a station
                try:
                    station_data = await self.repository.get_station_details(location_id)
                    enriched_order["station_name"] = station_data.get("name", "Unknown Station")
                    enriched_order["station_id"] = location_id

                    # Also fetch the station's system
                    system_id = station_data.get("system_id")
                    if system_id:
                        system_data = await self.repository.get_system_details(system_id)
                        enriched_order["system_name"] = system_data.get("name", "Unknown System")
                        enriched_order["system_id"] = system_id
                except Exception as e:
                    logger.warning(f"Error retrieving station {location_id}: {e}")
                    enriched_order["station_name"] = f"Station {location_id}"
                    enriched_order["station_id"] = location_id
            else:
                # It's a system
                try:
                    system_data = await self.repository.get_system_details(location_id)
                    enriched_order["system_name"] = system_data.get("name", "Unknown System")
                    enriched_order["system_id"] = location_id
                except Exception as e:
                    logger.warning(f"Error retrieving system {location_id}: {e}")
                    enriched_order["system_name"] = f"System {location_id}"
                    enriched_order["system_id"] = location_id

            return enriched_order

        # Enrich all orders in parallel
        buy_orders_enriched = await asyncio.gather(
            *[enrich_order(order) for order in buy_orders], return_exceptions=True
        )
        sell_orders_enriched = await asyncio.gather(
            *[enrich_order(order) for order in sell_orders], return_exceptions=True
        )

        # Filter errors (keep orders even if enrichment failed)
        buy_orders_final = [
            order if not isinstance(order, Exception) else buy_orders[i]
            for i, order in enumerate(buy_orders_enriched)
        ]
        sell_orders_final = [
            order if not isinstance(order, Exception) else sell_orders[i]
            for i, order in enumerate(sell_orders_enriched)
        ]

        return {
            "total": len(orders),
            "buy_orders": buy_orders_final,
            "sell_orders": sell_orders_final,
        }
