from dataclasses import dataclass
from typing import Any


@dataclass
class ConstellationDetails:
    constellation_id: int
    name: str
    systems: list[int]
    position: dict[str, Any]
    region_id: int | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConstellationDetails":
        return cls(
            constellation_id=data["constellation_id"],
            name=data.get("name", "Unknown"),
            systems=data.get("systems", []),
            position=data.get("position", {}),
            region_id=data.get("region_id"),
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "constellation_id": self.constellation_id,
            "name": self.name,
            "systems": self.systems,
            "position": self.position,
        }
        if self.region_id is not None:
            result["region_id"] = self.region_id
        return result
