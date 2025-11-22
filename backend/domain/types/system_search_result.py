from dataclasses import dataclass
from typing import Any


@dataclass
class SystemSearchResult:
    system_id: int
    name: str
    security_status: float
    security_class: str
    constellation_id: int | None
    region_id: int | None

    def to_dict(self) -> dict[str, Any]:
        result = {
            "system_id": self.system_id,
            "name": self.name,
            "security_status": self.security_status,
            "security_class": self.security_class,
        }
        if self.constellation_id is not None:
            result["constellation_id"] = self.constellation_id
        if self.region_id is not None:
            result["region_id"] = self.region_id
        return result
