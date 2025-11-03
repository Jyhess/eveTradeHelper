"""
Fonctions utilitaires pour le domaine
"""

from typing import Dict, Any, Optional
from .constants import STATION_ID_THRESHOLD


def is_station(location_id: int) -> bool:
    return location_id >= STATION_ID_THRESHOLD


async def get_system_id_from_location(
    repository, location_id: int
) -> Optional[int]:
    if not location_id:
        return None
    
    if is_station(location_id):
        try:
            station_data = await repository.get_station_details(location_id)
            return station_data.get("system_id")
        except Exception:
            return None
    
    return location_id


def calculate_tradable_volume(
    buy_volume: int,
    sell_volume: int,
    item_volume: float,
    max_transport_volume: Optional[float] = None,
) -> Optional[int]:
    tradable_volume = min(buy_volume, sell_volume)
    
    if tradable_volume <= 0:
        return None
    
    if max_transport_volume is not None and max_transport_volume > 0:
        if item_volume > 0:
            max_tradable_by_volume = int(max_transport_volume / item_volume)
            if max_tradable_by_volume <= 0:
                return None
            tradable_volume = min(tradable_volume, max_tradable_by_volume)
    
    return tradable_volume if tradable_volume > 0 else None


def apply_buy_cost_limit(
    tradable_volume: int,
    buy_price: float,
    max_buy_cost: Optional[float] = None,
) -> Optional[int]:
    if max_buy_cost is None or max_buy_cost <= 0:
        return tradable_volume
    
    total_buy_cost = buy_price * tradable_volume
    if total_buy_cost <= max_buy_cost:
        return tradable_volume
    
    if buy_price > 0:
        max_tradable_by_cost = int(max_buy_cost / buy_price)
        if max_tradable_by_cost <= 0:
            return None
        return min(tradable_volume, max_tradable_by_cost)
    
    return None

