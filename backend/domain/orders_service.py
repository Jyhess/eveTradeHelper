"""
Domain service for managing market orders
Provides Redis caching and optimized access patterns for orders
"""

import asyncio
import logging
from dataclasses import asdict
from typing import Any

from utils.cache.simple_cache import SimpleCache

from .constants import MARKET_ORDERS_CACHE_EXPIRY_HOURS
from .location_validator import LocationValidator
from .eve_repository import EveRepository
from .types import Order

logger = logging.getLogger(__name__)


class OrdersService:
    """Service for managing market orders with Redis cache"""

    def __init__(
        self,
        repository: EveRepository,
        location_validator: LocationValidator,
        cache: SimpleCache,
    ):
        """
        Initialize the service with a repository, location validator and cache

        Args:
            repository: Eve repository implementation
            location_validator: LocationValidator instance for validating order locations
            cache: SimpleCache instance for Redis caching
        """
        self.repository = repository
        self.location_validator = location_validator
        self._cache = cache
        self._expiry_hours = MARKET_ORDERS_CACHE_EXPIRY_HOURS

    def _generate_cache_key(self, region_id: int, type_id: int | None) -> str:
        """Generate cache key for orders"""
        if type_id is None:
            return f"orders:region:{region_id}"
        return f"orders:region:{region_id}:type:{type_id}"

    def _serialize_orders(self, orders: list[Order]) -> list[dict[str, Any]]:
        """Serialize Order objects to dictionaries"""
        return [asdict(order) for order in orders]

    def _deserialize_orders(self, orders_data: list[dict[str, Any]]) -> list[Order]:
        """Deserialize dictionaries to Order objects"""
        return [Order.from_dict(order_data) for order_data in orders_data]

    async def _filter_valid_orders(
        self, orders: list[Order], region_id: int, type_id: int | None = None
    ) -> list[Order]:
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
            if await self.location_validator.is_valid_location_id(order.location_id):
                valid_orders.append(order)
            else:
                logger.error(
                    f"Invalid location_id {order.location_id} in market order from "
                    f"region_id={region_id}, type_id={type_id}. Order ignored: {order}"
                )

        return valid_orders

    async def get_orders(self, region_id: int, type_id: int | None = None) -> list[Order]:
        """
        Get orders for a region and optional type
        Results are cached in Redis for fast access with 1h expiration
        Invalid orders (with invalid location_id) are filtered out

        Args:
            region_id: Region ID
            type_id: Optional item type ID to filter orders

        Returns:
            List of valid market orders
        """
        cache_key = self._generate_cache_key(region_id, type_id)

        cached_data = self._cache.get(cache_key, expiry_hours=self._expiry_hours)
        if cached_data is not None:
            return self._deserialize_orders(cached_data)

        orders = await self.repository.get_market_orders(region_id, type_id)
        valid_orders = await self._filter_valid_orders(orders, region_id, type_id)

        self._cache.set(
            cache_key, self._serialize_orders(valid_orders), expiry_hours=self._expiry_hours
        )

        return valid_orders

    async def get_orders_separated(
        self, region_id: int, type_id: int | None = None
    ) -> tuple[list[Order], list[Order]]:
        """
        Get orders separated by buy/sell type
        Results are cached in Redis

        Args:
            region_id: Region ID
            type_id: Optional item type ID to filter orders

        Returns:
            Tuple of (buy_orders, sell_orders)
        """
        orders = await self.get_orders(region_id, type_id)

        buy_orders = [o for o in orders if o.is_buy_order]
        sell_orders = [o for o in orders if not o.is_buy_order]

        return buy_orders, sell_orders

    async def get_orders_separated_with_region(
        self, region_id: int, type_id: int | None = None
    ) -> tuple[list[tuple[Order, int]], list[tuple[Order, int]]]:
        """
        Get orders separated by buy/sell type with region_id attached
        Results are cached in Redis

        Args:
            region_id: Region ID
            type_id: Optional item type ID to filter orders

        Returns:
            Tuple of (buy_orders_with_region, sell_orders_with_region)
            Each order is a tuple (order, region_id)
        """
        orders = await self.get_orders(region_id, type_id)

        buy_orders = [(o, region_id) for o in orders if o.is_buy_order]
        sell_orders = [(o, region_id) for o in orders if not o.is_buy_order]

        return buy_orders, sell_orders

    async def get_orders_for_regions(
        self, region_ids: list[int], type_id: int | None = None
    ) -> tuple[list[tuple[Order, int]], list[tuple[Order, int]]]:
        """
        Get orders from multiple regions, separated by buy/sell type with region_id
        Results are cached per region in Redis for fast access
        Fetches from all regions in parallel

        Args:
            region_ids: List of region IDs
            type_id: Optional item type ID to filter orders

        Returns:
            Tuple of (buy_orders_with_region, sell_orders_with_region)
            Each order is a tuple (order, region_id)
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
        """Clear all orders cache in Redis"""
        # Clear all order-related cache keys and their metadata
        for key in self._cache.redis_client.scan_iter(match="cache:orders:*"):
            self._cache.redis_client.delete(key)
        for key in self._cache.redis_client.scan_iter(match="metadata:orders:*"):
            self._cache.redis_client.delete(key)

    def clear_cache_for_region(self, region_id: int, type_id: int | None = None) -> None:
        """
        Clear cache for a specific region and optional type

        Args:
            region_id: Region ID
            type_id: Optional item type ID
        """
        cache_key = self._generate_cache_key(region_id, type_id)
        self._cache.clear(cache_key)
