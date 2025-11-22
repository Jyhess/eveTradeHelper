from dataclasses import dataclass
from typing import Any

from .system_map_connection import SystemMapConnection
from .system_map_system import SystemMapSystem


@dataclass
class SystemsWithinJumpsResult:
    systems: list[SystemMapSystem]
    connections: list[SystemMapConnection]

    def to_dict(self) -> dict[str, Any]:
        return {
            "systems": [
                {
                    "system_id": s.system_id,
                    "name": s.name,
                    "security_status": s.security_status,
                    "security_class": s.security_class,
                    "jumps": s.jumps,
                    "constellation_id": s.constellation_id,
                    "region_id": s.region_id,
                }
                for s in self.systems
            ],
            "connections": [
                {
                    "from_system_id": c.from_system_id,
                    "to_system_id": c.to_system_id,
                }
                for c in self.connections
            ],
        }
