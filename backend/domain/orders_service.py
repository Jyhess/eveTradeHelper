"""
Domain service for managing market orders
Provides in-memory caching and optimized access patterns for orders
"""

import asyncio
import logging
from typing import Any

from .location_validator import LocationValidator
from .repository import EveRepository

logger = logging.getLogger(__name__)


class OrdersService:
    """Service for managing market orders with in-memory cache"""

    def __init__(self, repository: EveRepository, location_validator: LocationValidator):
        """
        Initialize the service with a repository and location validator

        Args:
            repository: Eve repository implementation
            location_validator: LocationValidator instance for validating order locations
        """
        self.repository = repository
        self.location_validator = location_validator
        self._cache: dict[tuple[int, int | None], list[dict[str, Any]]] = {}

    async def _filter_valid_orders(
        self, orders: list[dict[str, Any]], region_id: int, type_id: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Filter out orders with invalid location_id

        Args:
            orders: List of orders to filter
            region_id: Region ID (for logging)
            type_id: Optional type ID (for logging)

        Returns:
            List of valid orders
        """
        valid_orders = []

        for order in orders:
            location_id = order.get("location_id")
            if await self.location_validator.is_valid_location_id(location_id):
                valid_orders.append(order)
            else:
                logger.error(
                    f"Invalid location_id {location_id} in market order from "
                    f"region_id={region_id}, type_id={type_id}. Order ignored: {order}"
                )

        return valid_orders

    async def get_orders(
        self, region_id: int, type_id: int | None = None
    ) -> list[dict[str, Any]]:
        """
        Get orders for a region and optional type
        Results are cached in memory for fast access
        Invalid orders (with invalid location_id) are filtered out

        Args:
            region_id: Region ID
            type_id: Optional item type ID to filter orders

        Returns:
            List of valid market orders
        """
        cache_key = (region_id, type_id)

        if cache_key in self._cache:
            return self._cache[cache_key]

        orders = await self.repository.get_market_orders(region_id, type_id)
        valid_orders = await self._filter_valid_orders(orders, region_id, type_id)
        self._cache[cache_key] = valid_orders

        return valid_orders

    async def get_orders_separated(
        self, region_id: int, type_id: int | None = None
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        """
        Get orders separated by buy/sell type
        Results are cached in memory

        Args:
            region_id: Region ID
            type_id: Optional item type ID to filter orders

        Returns:
            Tuple of (buy_orders, sell_orders)
        """
        orders = await self.get_orders(region_id, type_id)

        buy_orders = [o for o in orders if o.get("is_buy_order", False)]
        sell_orders = [o for o in orders if not o.get("is_buy_order", False)]

        return buy_orders, sell_orders

    async def get_orders_separated_with_region(
        self, region_id: int, type_id: int | None = None
    ) -> tuple[list[tuple[dict[str, Any], int]], list[tuple[dict[str, Any], int]]]:
        """
        Get orders separated by buy/sell type with region_id attached
        Results are cached in memory

        Args:
            region_id: Region ID
            type_id: Optional item type ID to filter orders

        Returns:
            Tuple of (buy_orders_with_region, sell_orders_with_region)
            Each order is a tuple (order_dict, region_id)
        """
        orders = await self.get_orders(region_id, type_id)

        buy_orders = [
            (o, region_id) for o in orders if o.get("is_buy_order", False)
        ]
        sell_orders = [
            (o, region_id) for o in orders if not o.get("is_buy_order", False)
        ]

        return buy_orders, sell_orders

    async def get_orders_for_regions(
        self, region_ids: list[int], type_id: int | None = None
    ) -> tuple[list[tuple[dict[str, Any], int]], list[tuple[dict[str, Any], int]]]:
        """
        Get orders from multiple regions, separated by buy/sell type with region_id
        Results are cached per region for fast access
        Fetches from all regions in parallel

        Args:
            region_ids: List of region IDs
            type_id: Optional item type ID to filter orders

        Returns:
            Tuple of (buy_orders_with_region, sell_orders_with_region)
            Each order is a tuple (order_dict, region_id)
        """
        all_orders_promises = [
            self.get_orders_separated_with_region(reg_id, type_id) for reg_id in region_ids
        ]
        all_orders_results = await asyncio.gather(*all_orders_promises, return_exceptions=True)

        all_buy_orders = []
        all_sell_orders = []

        for orders_result in all_orders_results:
            if isinstance(orders_result, tuple) and len(orders_result) == 2:
                buy_orders, sell_orders = orders_result
                all_buy_orders.extend(buy_orders)
                all_sell_orders.extend(sell_orders)

        return all_buy_orders, all_sell_orders

    def clear_cache(self) -> None:
        """Clear the in-memory cache"""
        self._cache.clear()

    def clear_cache_for_region(self, region_id: int, type_id: int | None = None) -> None:
        """
        Clear cache for a specific region and optional type

        Args:
            region_id: Region ID
            type_id: Optional item type ID
        """
        cache_key = (region_id, type_id)
        if cache_key in self._cache:
            del self._cache[cache_key]

