from dataclasses import dataclass
from typing import Any


@dataclass
class ConstellationSearchResult:
    constellation_id: int
    name: str
    region_id: int | None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "constellation_id": self.constellation_id,
            "name": self.name,
        }
        if self.region_id is not None:
            result["region_id"] = self.region_id
        return result
