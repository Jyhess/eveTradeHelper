from dataclasses import dataclass
from typing import Any


@dataclass
class TypePriceByRegion:
    region_id: int
    region_name: str
    max_buy_price: float | None
    min_sell_price: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "region_name": self.region_name,
            "max_buy_price": self.max_buy_price,
            "min_sell_price": self.min_sell_price,
        }
