import logging

from eve.exceptions import BadRequestError, NotFoundError
from repositories.local_data import LocalDataRepository

from .constants import STATION_ID_THRESHOLD
from .repository import EveRepository

logger = logging.getLogger(__name__)


class LocationValidator:
    def __init__(self, local_data_repository: LocalDataRepository, repository: EveRepository):
        self.local_data_repository = local_data_repository
        self.repository = repository

    def _is_in_known_range(self, location_id: int) -> bool:
        id_ranges = self.local_data_repository.get_id_ranges()
        return id_ranges.contains(location_id)

    async def is_valid_location_id(self, location_id: int | None) -> bool:
        if location_id is None:
            return False

        if self.local_data_repository.is_invalid_location_id_cached(location_id):
            return False

        max_int32 = self.local_data_repository.get_max_int32()
        if location_id > max_int32:
            self.local_data_repository.mark_location_id_as_invalid(location_id)
            return False

        if self._is_in_known_range(location_id):
            return True

        try:
            await self.repository.get_station_details(location_id)
            return True
        except (BadRequestError, NotFoundError):
            self.local_data_repository.mark_location_id_as_invalid(location_id)
            return False
        except Exception:
            return False

    def get_location_type(self, location_id: int | None) -> str | None:
        if location_id is None:
            return None

        id_ranges = self.local_data_repository.get_id_ranges()
        location_type = id_ranges.get_type(location_id)

        if location_type is None:
            logger.warning(f"Location ID {location_id} not found in known ranges")

        return location_type

    def mark_location_id_as_invalid(self, location_id: int) -> None:
        self.local_data_repository.mark_location_id_as_invalid(location_id)

    async def is_station(self, location_id: int) -> bool:
        if location_id < STATION_ID_THRESHOLD:
            return False

        if self.local_data_repository.is_invalid_location_id_cached(location_id):
            return False

        location_type = self.get_location_type(location_id)
        if location_type == "station":
            return True

        try:
            await self.repository.get_station_details(location_id)
            return True
        except (BadRequestError, NotFoundError):
            self.local_data_repository.mark_location_id_as_invalid(location_id)
            return False
        except Exception:
            return False
