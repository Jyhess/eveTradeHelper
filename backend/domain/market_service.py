"""
Domain service for market management
Contains pure business logic, independent of infrastructure (async version)
"""

import asyncio
import logging
from typing import Any, cast

from .constants import DEFAULT_MARKET_ORDERS_LIMIT
from repositories.local_data import LocalDataRepository

from .location_validator import LocationValidator
from .orders_service import OrdersService
from .repository import EveRepository

logger = logging.getLogger(__name__)


class MarketService:
    """Domain service for market management (async)"""

    def __init__(
        self,
        repository: EveRepository,
        location_validator: LocationValidator,
        orders_service: OrdersService,
        local_data_repository: LocalDataRepository | None = None,
    ):
        """
        Initialize the service with a repository

        Args:
            repository: Eve repository implementation
            location_validator: LocationValidator instance
            orders_service: OrdersService instance
        """
        self.repository = repository
        self.location_validator = location_validator
        self.orders_service = orders_service
        self.local_data_repository = local_data_repository

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
        # Fetch orders from OrdersService (with caching)
        buy_orders, sell_orders = await self.orders_service.get_orders_separated(
            region_id, type_id
        )

        # Store total before limiting
        total_before_limit = len(buy_orders) + len(sell_orders)

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
            if await self.location_validator.is_station(location_id):
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

        # Check if item is contraband for this region
        is_contraband = False
        if type_id and self.local_data_repository:
            region_faction_id = self.local_data_repository.get_region_faction_id(region_id)
            if region_faction_id is not None:
                is_contraband = self.local_data_repository.is_contraband_for_faction(
                    type_id, region_faction_id
                )

        return {
            "total": total_before_limit,
            "buy_orders": buy_orders_final,
            "sell_orders": sell_orders_final,
            "is_contraband": is_contraband,
        }

    async def search_item_types(
        self, query: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        # If no query, return all types
        if not query or not query.strip():
            if not self.local_data_repository:
                logger.warning("Local data repository not configured for type search")
                return []
            return self.local_data_repository.search_types(None, limit)

        query = query.strip()

        # Handle ID search
        if query.isdigit():
            type_id = int(query)
            try:
                type_data = await self.repository.get_item_type(type_id)
            except Exception:  # pragma: no cover - ESI errors already logged upstream
                logger.warning("Error retrieving type %s for search", type_id)
                return []

            if not type_data:
                return []

            name = type_data.get("name")
            if isinstance(name, dict):
                name = name.get("en") or name.get("fr")

            if not isinstance(name, str) or not name:
                name = f"Type {type_id}"

            return [{"type_id": type_id, "name": name}]

        if not self.local_data_repository:
            logger.warning("Local data repository not configured for type search")
            return []

        return self.local_data_repository.search_types(query, limit)

    async def get_type_prices_by_region(
        self, type_id: int, max_concurrent: int = 10
    ) -> list[dict[str, Any]]:
        """
        Retrieves minimum sell price and maximum buy price for a type across all regions
        Business logic: parallelized fetching with concurrency limit

        Args:
            type_id: Item type ID
            max_concurrent: Maximum number of concurrent region queries (default: 10)

        Returns:
            List of dictionaries with region_id, region_name, min_sell_price, max_buy_price
        """
        # Get all region IDs
        region_ids = await self.repository.get_regions_list()

        semaphore = asyncio.Semaphore(max_concurrent)

        async def get_region_prices(region_id: int) -> dict[str, Any] | None:
            """Get prices for a single region"""
            async with semaphore:
                try:
                    buy_orders, sell_orders = await self.orders_service.get_orders_separated(
                        region_id, type_id
                    )

                    # Find max buy price (highest price someone is willing to buy at)
                    max_buy_price = None
                    if buy_orders:
                        max_buy_price = max(order.get("price", 0) for order in buy_orders)

                    # Find min sell price (lowest price someone is willing to sell at)
                    min_sell_price = None
                    if sell_orders:
                        min_sell_price = min(order.get("price", float("inf")) for order in sell_orders)

                    # Get region name
                    region_data = await self.repository.get_region_details(region_id)
                    region_name = region_data.get("name", f"Region {region_id}")

                    return {
                        "region_id": region_id,
                        "region_name": region_name,
                        "max_buy_price": max_buy_price,
                        "min_sell_price": min_sell_price,
                    }
                except Exception as e:
                    logger.warning(f"Error retrieving prices for region {region_id}: {e}")
                    return None

        # Fetch prices for all regions in parallel (with concurrency limit)
        results = await asyncio.gather(
            *[get_region_prices(region_id) for region_id in region_ids], return_exceptions=True
        )

        # Filter out None results and exceptions, then sort by region name
        prices: list[dict[str, Any]] = []
        for result in results:
            if isinstance(result, dict):
                prices.append(result)
        # Type narrowing: prices contains only dict[str, Any] at this point
        prices.sort(key=lambda x: x.get("region_name", ""))  # type: ignore[union-attr]

        return prices  # type: ignore[return-value]
