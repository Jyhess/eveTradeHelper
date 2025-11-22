from dataclasses import dataclass
from typing import Any


@dataclass
class SystemConnection:
    system_id: int
    name: str
    security_status: float
    security_class: str
    stargate_id: int
    constellation_id: int | None
    constellation_name: str | None
    region_id: int | None
    region_name: str | None
    same_constellation: bool
    same_region: bool

    def to_dict(self) -> dict[str, Any]:
        result = {
            "system_id": self.system_id,
            "name": self.name,
            "security_status": self.security_status,
            "security_class": self.security_class,
            "stargate_id": self.stargate_id,
            "same_constellation": self.same_constellation,
            "same_region": self.same_region,
        }
        if self.constellation_id is not None:
            result["constellation_id"] = self.constellation_id
        if self.constellation_name is not None:
            result["constellation_name"] = self.constellation_name
        if self.region_id is not None:
            result["region_id"] = self.region_id
        if self.region_name is not None:
            result["region_name"] = self.region_name
        return result
