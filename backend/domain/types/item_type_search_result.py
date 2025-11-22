from dataclasses import dataclass
from typing import Any


@dataclass
class ItemTypeSearchResult:
    type_id: int
    name: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "type_id": self.type_id,
            "name": self.name,
        }
