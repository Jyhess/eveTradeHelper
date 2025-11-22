from dataclasses import dataclass


@dataclass
class SystemMapConnection:
    from_system_id: int
    to_system_id: int
