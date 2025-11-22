from dataclasses import dataclass
from typing import Any


@dataclass
class RegionDetails:
    region_id: int
    name: str
    description: str
    constellations: list[int]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "RegionDetails":
        return cls(
            region_id=data["region_id"],
            name=data.get("name", "Unknown"),
            description=data.get("description", ""),
            constellations=data.get("constellations", []),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "name": self.name,
            "description": self.description,
            "constellations": self.constellations,
        }
