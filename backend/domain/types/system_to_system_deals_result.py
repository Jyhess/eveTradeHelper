from dataclasses import dataclass
from typing import Any

from .deal import Deal


@dataclass
class SystemToSystemDealsResult:
    from_system_id: int
    to_system_id: int
    route: list[int]
    route_segments: list[tuple[int, int]]
    min_profit_isk: float
    max_transport_volume: float | None
    max_buy_cost: float | None
    total_types: int
    total_profit_isk: float
    deals: list[Deal]

    def to_dict(self) -> dict[str, Any]:
        return {
            "from_system_id": self.from_system_id,
            "to_system_id": self.to_system_id,
            "route": self.route,
            "route_segments": [{"from": seg[0], "to": seg[1]} for seg in self.route_segments],
            "min_profit_isk": self.min_profit_isk,
            "max_transport_volume": self.max_transport_volume,
            "max_buy_cost": self.max_buy_cost,
            "total_types": self.total_types,
            "total_profit_isk": round(self.total_profit_isk, 2),
            "deals": [deal.to_dict() for deal in self.deals],
        }
