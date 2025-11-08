"""
API for market and item type management
FastAPI endpoints for markets (async)
"""

import logging
from collections.abc import Hashable
from typing import Any

from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException

from domain.constants import MARKET_CATEGORIES_CACHE_TTL
from domain.market_service import MarketService

from .services_provider import ServicesProvider

logger = logging.getLogger(__name__)
router = APIRouter()
market_router = router

# LRU cache with TTL for market categories (in memory)
_market_categories_cache: TTLCache[Hashable, Any] = TTLCache(
    maxsize=1, ttl=MARKET_CATEGORIES_CACHE_TTL
)


@router.get("/api/v1/markets/categories")
async def get_market_categories(
    market_service: MarketService = Depends(ServicesProvider.get_market_service),
):
    """
    Retrieves the list of market categories
    Uses an LRU cache with TTL (1 hour) in memory to improve performance

    Returns:
        JSON response with market categories
    """
    # Check LRU cache (fixed key as there are no variable parameters)
    cache_key = "market_categories"
    if cache_key in _market_categories_cache:
        logger.info("Retrieving categories from LRU cache")
        return _market_categories_cache[cache_key]

    try:
        logger.info("Retrieving market categories (not cached)")

        categories = await market_service.get_market_categories()

        result = {
            "total": len(categories),
            "categories": categories,
        }

        # Store in LRU cache
        _market_categories_cache[cache_key] = result

        return result

    except Exception as e:
        logger.error(f"Error retrieving categories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ESI API connection error: {str(e)}",
        ) from None


@router.get("/api/v1/universe/types/{type_id}")
async def get_item_type(
    type_id: int,
    market_service: MarketService = Depends(ServicesProvider.get_market_service),
):
    """
    Retrieves details of an item type
    Cache is automatically managed by the infrastructure layer (EveAPIClient)

    Args:
        type_id: Item type ID

    Returns:
        JSON response with item type details
    """
    try:
        logger.info(f"Retrieving type details for {type_id}")
        type_data = await market_service.get_item_type(type_id)

        return type_data

    except Exception as e:
        logger.error(f"Error retrieving type: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ESI API connection error: {str(e)}",
        ) from None


@router.get("/api/v1/markets/regions/{region_id}/orders")
async def get_market_orders(
    region_id: int,
    type_id: int | None = None,
    market_service: MarketService = Depends(ServicesProvider.get_market_service),
):
    """
    Retrieves market orders for a region, optionally filtered by type
    Cache is automatically managed by the infrastructure layer (EveAPIClient)
    Enriches orders with system and station names

    Args:
        region_id: Region ID
        type_id: Optional, item type ID to filter orders

    Returns:
        JSON response with enriched market orders
    """
    try:
        logger.info(
            f"Retrieving market orders for region {region_id}"
            + (f" and type {type_id}" if type_id else "")
        )

        enriched_orders = await market_service.get_enriched_market_orders(region_id, type_id)

        return {
            "region_id": region_id,
            "type_id": type_id,
            **enriched_orders,
        }

    except Exception as e:
        logger.error(f"Error retrieving orders: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ESI API connection error: {str(e)}",
        ) from None
