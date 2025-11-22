from dataclasses import dataclass
from typing import Any

from .contraband_system import ContrabandSystem
from .route_detail import RouteDetail


@dataclass
class Deal:
    type_id: int
    type_name: str
    buy_price: float
    sell_price: float
    profit_percent: float
    profit_isk: float
    tradable_volume: int
    item_volume: float
    total_buy_cost: float
    total_sell_revenue: float
    total_transport_volume: float
    buy_order_count: int
    sell_order_count: int
    jumps: int | None
    estimated_time_minutes: int | None
    route_details: list[RouteDetail]
    buy_system_id: int | None
    sell_system_id: int | None
    contraband_systems: list[ContrabandSystem]
    is_contraband: bool
    buy_region_id: int | None = None
    sell_region_id: int | None = None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "type_id": self.type_id,
            "type_name": self.type_name,
            "buy_price": self.buy_price,
            "sell_price": self.sell_price,
            "profit_isk": round(self.profit_isk, 2),
            "tradable_volume": self.tradable_volume,
            "item_volume": self.item_volume,
            "total_buy_cost": round(self.total_buy_cost, 2),
            "total_sell_revenue": round(self.total_sell_revenue, 2),
            "total_transport_volume": round(self.total_transport_volume, 2),
            "buy_order_count": self.buy_order_count,
            "sell_order_count": self.sell_order_count,
            "jumps": self.jumps,
            "estimated_time_minutes": self.estimated_time_minutes,
            "route_details": [
                {
                    "system_id": rd.system_id,
                    "name": rd.name,
                    "security_status": rd.security_status,
                    **({"faction_id": rd.faction_id} if rd.faction_id is not None else {}),
                }
                for rd in self.route_details
            ],
            "buy_system_id": self.buy_system_id,
            "sell_system_id": self.sell_system_id,
            "contraband_systems": [
                {
                    "system_id": cs.system_id,
                    "system_name": cs.system_name,
                    "faction_id": cs.faction_id,
                }
                for cs in self.contraband_systems
            ],
            "is_contraband": self.is_contraband,
        }
        if self.buy_region_id is not None:
            result["buy_region_id"] = self.buy_region_id
        if self.sell_region_id is not None:
            result["sell_region_id"] = self.sell_region_id
        return result
