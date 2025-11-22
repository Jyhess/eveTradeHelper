from dataclasses import dataclass
from typing import Any


@dataclass
class StargateDetails:

    stargate_id: int
    system_id: int
    destination_system_id: int
    position: dict[str, Any]
    type_id: int
    name: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StargateDetails":
        return cls(
            stargate_id=data["stargate_id"],
            system_id=data["system_id"],
            destination_system_id=data.get('destination_system_id') or data["destination"]["system_id"],
            position=data["position"],
            type_id=data["type_id"],
            name=data["name"],
        )
