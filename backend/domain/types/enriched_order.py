from dataclasses import dataclass
from typing import Any

from .order import Order


@dataclass
class EnrichedOrder:
    order_id: int
    type_id: int
    location_id: int
    volume_total: int
    volume_remain: int
    min_volume: int
    price: float
    is_buy_order: bool
    duration: int
    issued: str
    range: str
    station_name: str | None = None
    station_id: int | None = None
    system_name: str | None = None
    system_id: int | None = None

    @classmethod
    def from_order(cls, order: Order) -> "EnrichedOrder":
        return cls(
            order_id=order.order_id,
            type_id=order.type_id,
            location_id=order.location_id,
            volume_total=order.volume_total,
            volume_remain=order.volume_remain,
            min_volume=order.min_volume,
            price=order.price,
            is_buy_order=order.is_buy_order,
            duration=order.duration,
            issued=order.issued,
            range=order.range,
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "order_id": self.order_id,
            "type_id": self.type_id,
            "location_id": self.location_id,
            "volume_total": self.volume_total,
            "volume_remain": self.volume_remain,
            "min_volume": self.min_volume,
            "price": self.price,
            "is_buy_order": self.is_buy_order,
            "duration": self.duration,
            "issued": self.issued,
            "range": self.range,
        }
        if self.station_name is not None:
            result["station_name"] = self.station_name
        if self.station_id is not None:
            result["station_id"] = self.station_id
        if self.system_name is not None:
            result["system_name"] = self.system_name
        if self.system_id is not None:
            result["system_id"] = self.system_id
        return result
