from dataclasses import dataclass
from typing import Any


@dataclass
class SystemDetails:
    system_id: int
    name: str
    security_status: float
    security_class: str
    position: dict[str, Any]
    constellation_id: int | None
    planets: list[int]
    star_id: int | None
    stargates: list[int] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SystemDetails":
        return cls(
            system_id=data["system_id"],
            name=data.get("name", "Unknown"),
            security_status=data.get("security_status", 0.0),
            security_class=data.get("security_class", ""),
            position=data.get("position", {}),
            constellation_id=data.get("constellation_id"),
            planets=data.get("planets", []),
            star_id=data.get("star_id"),
            stargates=data.get("stargates"),
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "system_id": self.system_id,
            "name": self.name,
            "security_status": self.security_status,
            "security_class": self.security_class,
            "position": self.position,
            "planets": self.planets,
        }
        if self.constellation_id is not None:
            result["constellation_id"] = self.constellation_id
        if self.star_id is not None:
            result["star_id"] = self.star_id
        if self.stargates is not None:
            result["stargates"] = self.stargates
        return result
