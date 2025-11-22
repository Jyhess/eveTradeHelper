from dataclasses import dataclass
from typing import Any

from .enriched_order import EnrichedOrder


@dataclass
class EnrichedMarketOrders:
    total: int
    buy_orders: list[EnrichedOrder]
    sell_orders: list[EnrichedOrder]
    is_contraband: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "total": self.total,
            "buy_orders": [order.to_dict() for order in self.buy_orders],
            "sell_orders": [order.to_dict() for order in self.sell_orders],
            "is_contraband": self.is_contraband,
        }
