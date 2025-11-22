from dataclasses import dataclass


@dataclass
class RouteDetail:
    system_id: int
    name: str
    security_status: float
    faction_id: int | None = None
