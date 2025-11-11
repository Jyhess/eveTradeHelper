"""
Fonctions utilitaires pour le domaine
"""

from .location_validator import LocationValidator


async def get_system_id_from_location(
    location_id: int, location_validator: LocationValidator
) -> int | None:
    if not location_id:
        raise ValueError("Location ID is required")

    if not await location_validator.is_station(location_id):
        raise ValueError(f"Location {location_id} is not a station")

    station_data = await location_validator.repository.get_station_details(location_id)
    return station_data.get("system_id")


def calculate_tradable_volume(
    buy_volume: int,
    sell_volume: int,
    item_volume: float,
    max_transport_volume: float | None = None,
) -> int | None:
    tradable_volume = min(buy_volume, sell_volume)

    if tradable_volume <= 0:
        return None

    if (
        max_transport_volume is not None
        and max_transport_volume > 0
        and item_volume > 0
        and (max_tradable_by_volume := int(max_transport_volume / item_volume)) > 0
    ):
        tradable_volume = min(tradable_volume, max_tradable_by_volume)
    elif (
        max_transport_volume is not None
        and max_transport_volume > 0
        and item_volume > 0
        and int(max_transport_volume / item_volume) <= 0
    ):
        return None

    return tradable_volume if tradable_volume > 0 else None


def apply_buy_cost_limit(
    tradable_volume: int,
    buy_price: float,
    max_buy_cost: float | None = None,
) -> int | None:
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
