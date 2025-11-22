from dataclasses import dataclass
from typing import Any


@dataclass
class StationDetails:
    station_id: int
    name: str
    system_id: int
    type_id: int | None = None
    position: dict[str, Any] | None = None
    owner: int | None = None
    race_id: int | None = None
    reprocessing_efficiency: float | None = None
    reprocessing_stations_take: float | None = None
    max_dockable_ship_volume: float | None = None
    office_rental_cost: int | None = None
    services: list[str] | None = None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StationDetails":
        return cls(
            station_id=data.get("station_id", 0),
            name=data.get("name", "Unknown Station"),
            system_id=data.get("system_id", 0),
            type_id=data.get("type_id"),
            position=data.get("position"),
            owner=data.get("owner"),
            race_id=data.get("race_id"),
            reprocessing_efficiency=data.get("reprocessing_efficiency"),
            reprocessing_stations_take=data.get("reprocessing_stations_take"),
            max_dockable_ship_volume=data.get("max_dockable_ship_volume"),
            office_rental_cost=data.get("office_rental_cost"),
            services=data.get("services"),
        )
