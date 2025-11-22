from dataclasses import dataclass
from typing import Any


@dataclass
class Order:
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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Order":
        return cls(
            order_id=data["order_id"],
            type_id=data["order_id"],
            location_id=data["location_id"],
            volume_total=data["volume_total"],
            volume_remain=data["volume_remain"],
            min_volume=data["min_volume"],
            price=data["price"],
            is_buy_order=data["is_buy_order"],
            duration=data["duration"],
            issued=data["issued"],
            range=data["range"],
        )
