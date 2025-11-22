from dataclasses import dataclass
from typing import Any


@dataclass
class MarketGroupDetails:
    market_group_id: int
    name: str
    description: str
    parent_group_id: int | None
    types: list[int]
    icon_id: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MarketGroupDetails":
        return cls(
            market_group_id=data["market_group_id"],
            name=data.get("name", "Unknown"),
            description=data.get("description", ""),
            parent_group_id=data.get("parent_group_id"),
            types=data.get("types", []),
            icon_id=data.get("icon_id"),
        )
