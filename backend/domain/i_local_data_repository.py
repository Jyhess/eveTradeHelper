from abc import ABC, abstractmethod

from .types import IdRanges, MarketGroupDetails
from typing import Any


class ILocalDataRepository(ABC):
    @abstractmethod
    def get_id_ranges(self) -> IdRanges:
        pass

    @abstractmethod
    def is_invalid_location_id_cached(self, location_id: int) -> bool:
        pass

    @abstractmethod
    def mark_location_id_as_invalid(self, location_id: int) -> None:
        pass

    @abstractmethod
    def get_max_int32(self) -> int:
        pass

    @abstractmethod
    def search_types(self, query: str | None = None, limit: int = 20) -> list[dict[str, Any]]:
        pass

    @abstractmethod
    def is_contraband_for_faction(self, type_id: int, faction_id: int) -> bool:
        pass

    @abstractmethod
    def get_system_faction_id(self, system_id: int) -> int | None:
        pass

    @abstractmethod
    def get_region_faction_id(self, region_id: int) -> int | None:
        pass
 
    @abstractmethod
    def get_all_market_group_ids(self) -> list[int]:
        pass

    @abstractmethod
    def get_market_group_details(self, group_id: int) -> MarketGroupDetails | None:
        pass

    @abstractmethod
    def get_all_types_from_all_groups(self) -> set[int]:
        pass

    @abstractmethod
    def get_root_market_group_ids(self) -> list[int]:
        pass
