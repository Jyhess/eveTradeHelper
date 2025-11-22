from dataclasses import dataclass
from typing import Any

from .market_group_details import MarketGroupDetails


@dataclass
class MarketCategory:
    group_id: int
    name: str
    description: str
    parent_group_id: int | None
    types: list[int]

    @classmethod
    def from_market_group_details(cls, details: MarketGroupDetails) -> "MarketCategory":
        return cls(
            group_id=details.market_group_id,
            name=details.name,
            description=details.description,
            parent_group_id=details.parent_group_id,
            types=details.types,
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "group_id": self.group_id,
            "name": self.name,
            "description": self.description,
            "types": self.types,
        }
        if self.parent_group_id is not None:
            result["parent_group_id"] = self.parent_group_id
        return result
