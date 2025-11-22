from dataclasses import dataclass


@dataclass
class SystemMapSystem:
    system_id: int
    name: str
    security_status: float
    security_class: str
    jumps: int
    constellation_id: int | None
    region_id: int | None
