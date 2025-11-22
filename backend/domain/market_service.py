"""
Domain service for market management
Contains pure business logic, independent of infrastructure (async version)
"""

import asyncio
import logging

from .constants import DEFAULT_MARKET_ORDERS_LIMIT
from .i_local_data_repository import ILocalDataRepository
from .location_validator import LocationValidator
from .orders_service import OrdersService
from .repository import EveRepository
from .types import (
    EnrichedMarketOrders,
    EnrichedOrder,
    ItemType,
    ItemTypeSearchResult,
    MarketCategory,
    MarketGroupDetails,
    Order,
    TypePriceByRegion,
)

logger = logging.getLogger(__name__)


class MarketService:
    """Domain service for market management (async)"""

    def __init__(
        self,
        repository: EveRepository,
        location_validator: LocationValidator,
        orders_service: OrdersService,
        local_data_repository: ILocalDataRepository,
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

    async def get_market_categories(self) -> list[MarketCategory]:
        """
        Retrieves the list of market categories with their details from static data

        Returns:
            List of formatted categories, sorted by name
        """
        if not self.local_data_repository:
            raise ValueError(
                "local_data_repository is required for getting market categories. "
                "Static data must be available."
            )

        group_ids = self.local_data_repository.get_all_market_group_ids()

        categories = []
        for group_id in group_ids:
            market_group_details = self.local_data_repository.get_market_group_details(group_id)
            if not market_group_details:
                continue

            category = MarketCategory.from_market_group_details(market_group_details)
            categories.append(category)

        return sorted(categories, key=lambda x: x.name)

    async def get_item_type(self, type_id: int) -> ItemType:
        return await self.repository.get_item_type(type_id)

    async def get_enriched_market_orders(
        self,
        region_id: int,
        type_id: int | None = None,
        limit: int = DEFAULT_MARKET_ORDERS_LIMIT,
    ) -> EnrichedMarketOrders:
        """
        Retrieves enriched market orders for a region
        Business logic: sorting, limiting and enriching orders

        Args:
            region_id: Region ID
            type_id: Optional, item type ID to filter orders
            limit: Maximum number of orders per type (buy/sell) to return

        Returns:
            EnrichedMarketOrders containing enriched buy and sell orders
        """
        buy_orders, sell_orders = await self.orders_service.get_orders_separated(region_id, type_id)

        total_before_limit = len(buy_orders) + len(sell_orders)

        buy_orders.sort(key=lambda x: x.price, reverse=True)
        sell_orders.sort(key=lambda x: x.price)

        buy_orders = buy_orders[:limit]
        sell_orders = sell_orders[:limit]

        async def enrich_order(order: Order) -> EnrichedOrder:
            """Enriches an order with system and station names"""
            enriched_order = EnrichedOrder.from_order(order)

            # IDs >= STATION_ID_THRESHOLD are stations, otherwise they are systems
            if await self.location_validator.is_station(order.location_id):
                # It's a station
                try:
                    station_data = await self.repository.get_station_details(order.location_id)
                    enriched_order.station_name = station_data.name
                    enriched_order.station_id = order.location_id

                    # Also fetch the station's system
                    if station_data.system_id:
                        system_data = await self.repository.get_system_details(
                            station_data.system_id
                        )
                        enriched_order.system_name = system_data.name
                        enriched_order.system_id = station_data.system_id
                except Exception as e:
                    logger.warning(f"Error retrieving station {order.location_id}: {e}")
                    enriched_order.station_name = f"Station {order.location_id}"
                    enriched_order.station_id = order.location_id
            else:
                # It's a system
                try:
                    system_data = await self.repository.get_system_details(order.location_id)
                    enriched_order.system_name = system_data.name
                    enriched_order.system_id = order.location_id
                except Exception as e:
                    logger.warning(f"Error retrieving system {order.location_id}: {e}")
                    enriched_order.system_name = f"System {order.location_id}"
                    enriched_order.system_id = order.location_id

            return enriched_order

        buy_orders_enriched = await asyncio.gather(
            *[enrich_order(order) for order in buy_orders], return_exceptions=True
        )
        sell_orders_enriched = await asyncio.gather(
            *[enrich_order(order) for order in sell_orders], return_exceptions=True
        )

        buy_orders_final: list[EnrichedOrder] = [
            order for order in buy_orders_enriched if isinstance(order, EnrichedOrder)
        ]
        sell_orders_final: list[EnrichedOrder] = [
            order for order in sell_orders_enriched if isinstance(order, EnrichedOrder)
        ]

        is_contraband = False
        if type_id and self.local_data_repository:
            region_faction_id = self.local_data_repository.get_region_faction_id(region_id)
            if region_faction_id is not None:
                is_contraband = self.local_data_repository.is_contraband_for_faction(
                    type_id, region_faction_id
                )

        return EnrichedMarketOrders(
            total=total_before_limit,
            buy_orders=buy_orders_final,
            sell_orders=sell_orders_final,
            is_contraband=is_contraband,
        )

    async def search_item_types(
        self, query: str | None = None, limit: int = 20
    ) -> list[ItemTypeSearchResult]:
        # If no query, return all types
        if not query or not query.strip():
            if not self.local_data_repository:
                logger.warning("Local data repository not configured for type search")
                return []
            results = self.local_data_repository.search_types(None, limit)
            return [ItemTypeSearchResult(type_id=r["type_id"], name=r["name"]) for r in results]

        query = query.strip()

        if query.isdigit():
            type_id = int(query)
            try:
                type_data = await self.repository.get_item_type(type_id)
            except Exception:  # pragma: no cover - ESI errors already logged upstream
                logger.warning("Error retrieving type %s for search", type_id)
                return []

            name: str | dict[str, str] = type_data.name
            if isinstance(name, dict):
                name_str = name.get("en") or name.get("fr")
                if not isinstance(name_str, str) or not name_str:
                    name_str = f"Type {type_id}"
                name = name_str
            elif not isinstance(name, str) or not name:
                name = f"Type {type_id}"

            return [ItemTypeSearchResult(type_id=type_id, name=name)]

        if not self.local_data_repository:
            logger.warning("Local data repository not configured for type search")
            return []

        results = self.local_data_repository.search_types(query, limit)
        return [ItemTypeSearchResult(type_id=r["type_id"], name=r["name"]) for r in results]

    async def get_type_prices_by_region(
        self, type_id: int, max_concurrent: int = 10
    ) -> list[TypePriceByRegion]:
        """
        Retrieves minimum sell price and maximum buy price for a type across all regions
        Business logic: parallelized fetching with concurrency limit

        Args:
            type_id: Item type ID
            max_concurrent: Maximum number of concurrent region queries (default: 10)

        Returns:
            List of TypePriceByRegion with region_id, region_name, min_sell_price, max_buy_price
        """
        # Get all region IDs
        region_ids = await self.repository.get_regions_list()

        semaphore = asyncio.Semaphore(max_concurrent)

        async def get_region_prices(region_id: int) -> TypePriceByRegion | None:
            """Get prices for a single region"""
            async with semaphore:
                try:
                    buy_orders, sell_orders = await self.orders_service.get_orders_separated(
                        region_id, type_id
                    )

                    # Find max buy price (highest price someone is willing to buy at)
                    max_buy_price = None
                    if buy_orders:
                        max_buy_price = max(order.price for order in buy_orders)

                    # Find min sell price (lowest price someone is willing to sell at)
                    min_sell_price = None
                    if sell_orders:
                        min_sell_price = min(order.price for order in sell_orders)

                    # Get region name
                    region_data = await self.repository.get_region_details(region_id)
                    region_name = region_data.name

                    return TypePriceByRegion(
                        region_id=region_id,
                        region_name=region_name,
                        max_buy_price=max_buy_price,
                        min_sell_price=min_sell_price,
                    )
                except Exception as e:
                    logger.warning(f"Error retrieving prices for region {region_id}: {e}")
                    return None

        # Fetch prices for all regions in parallel (with concurrency limit)
        results = await asyncio.gather(
            *[get_region_prices(region_id) for region_id in region_ids], return_exceptions=True
        )

        # Filter out None results, exceptions, and regions without any prices
        # Only include regions that have at least one price (buy or sell)
        prices: list[TypePriceByRegion] = []
        for result in results:
            if isinstance(result, TypePriceByRegion) and (
                result.max_buy_price is not None or result.min_sell_price is not None
            ):
                prices.append(result)
        prices.sort(key=lambda x: x.region_name)

        return prices
