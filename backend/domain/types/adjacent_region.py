from dataclasses import dataclass
from typing import Any


@dataclass
class AdjacentRegion:
    region_id: int
    name: str
    description: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "region_id": self.region_id,
            "name": self.name,
            "description": self.description,
        }
