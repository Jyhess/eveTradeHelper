from dataclasses import dataclass
from typing import Any


@dataclass
class ItemType:
    type_id: int
    name: str | dict[str, str]
    volume: float
    description: str | None = None
    group_id: int | None = None
    category_id: int | None = None
    market_group_id: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ItemType":
        return cls(
            type_id=data["type_id"],
            name=data.get("name", "Unknown"),
            volume=data.get("volume", 0.0),
            description=data.get("description"),
            group_id=data.get("group_id"),
            category_id=data.get("category_id"),
            market_group_id=data.get("market_group_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "type_id": self.type_id,
            "name": self.name,
            "volume": self.volume,
        }
        if self.description is not None:
            result["description"] = self.description
        if self.group_id is not None:
            result["group_id"] = self.group_id
        if self.category_id is not None:
            result["category_id"] = self.category_id
        if self.market_group_id is not None:
            result["market_group_id"] = self.market_group_id
        return result
