from dataclasses import dataclass
from typing import Any

from .deal import Deal


@dataclass
class MarketDealsResult:
    region_id: int
    min_profit_isk: float
    max_transport_volume: float | None
    max_buy_cost: float | None
    total_types: int
    total_profit_isk: float
    deals: list[Deal]
    group_ids: list[int]

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "region_id": self.region_id,
            "min_profit_isk": self.min_profit_isk,
            "max_transport_volume": self.max_transport_volume,
            "max_buy_cost": self.max_buy_cost,
            "total_types": self.total_types,
            "total_profit_isk": round(self.total_profit_isk, 2),
            "deals": [deal.to_dict() for deal in self.deals],
        }
        if self.group_ids is not None:
            result["group_ids"] = self.group_ids
        return result
