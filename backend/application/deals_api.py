"""
API for finding deals
FastAPI endpoints for deals (async version)
"""

import logging

from fastapi import APIRouter, Depends, HTTPException

from domain.deals_service import DealsService

from .services_provider import ServicesProvider

logger = logging.getLogger(__name__)
router = APIRouter()
deals_router = router


@router.get("/api/v1/markets/deals")
async def get_market_deals(
    region_id: int,
    group_id: int,
    min_profit_isk: float = 100000.0,  # Uses DEFAULT_MIN_PROFIT_ISK from service
    max_transport_volume: float | None = None,
    max_buy_cost: float | None = None,
    additional_regions: str | None = None,
    deals_service: DealsService = Depends(ServicesProvider.get_deals_service),
):
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
        additional_regions: List of additional region IDs separated by commas (e.g., "123,456,789")

    Returns:
        JSON response with items allowing profit above the threshold
    """
    try:
        # Parse additional regions
        additional_region_ids = []
        if additional_regions:
            try:
                additional_region_ids = [
                    int(rid.strip()) for rid in additional_regions.split(",") if rid.strip()
                ]
            except ValueError:
                logger.warning(f"Invalid format for additional_regions: {additional_regions}")
                additional_region_ids = []

        result = await deals_service.find_market_deals(
            region_id=region_id,
            group_id=group_id,
            min_profit_isk=min_profit_isk,
            max_transport_volume=max_transport_volume,
            max_buy_cost=max_buy_cost,
            additional_regions=additional_region_ids,
        )
        return result

    except Exception as e:
        logger.error(f"Error searching for deals: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ESI API connection error: {str(e)}",
        ) from None
