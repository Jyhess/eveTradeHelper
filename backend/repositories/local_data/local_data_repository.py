import json
import logging
from pathlib import Path
from typing import Any

from utils.cache import SimpleCache

from .id_ranges import IdRanges

logger = logging.getLogger(__name__)

STATIC_DATA_DIR = Path(__file__).parent.parent.parent / "eve-online-static-data-jsonl"
TYPES_FROM_ID_FILE = STATIC_DATA_DIR / "typesFromId.json"
INVALID_LOCATION_IDS_KEY_PREFIX = "invalid_location_ids"
MAX_INT32 = 2147483647


class LocalDataRepository:
    def __init__(self, cache: SimpleCache):
        self.cache = cache
        self.id_ranges: list[dict[str, Any]] = []
        self._load_id_ranges()

    def _load_id_ranges(self) -> None:
        self.id_ranges = []

        if not TYPES_FROM_ID_FILE.exists():
            logger.warning(
                f"TypesFromId file not found: {TYPES_FROM_ID_FILE}. "
                "Location validation will be disabled."
            )
            return

        try:
            with open(TYPES_FROM_ID_FILE, encoding="utf-8") as f:
                data = json.load(f)
                id_map = data.get("id_map", [])
                self.id_ranges = id_map
                logger.info(f"Loaded {len(self.id_ranges)} ID ranges from typesFromId.json")
        except Exception as e:
            logger.error(f"Error loading ID ranges from typesFromId.json: {e}")
            self.id_ranges = []

    def get_id_ranges(self) -> IdRanges:
        return IdRanges(self.id_ranges)

    def is_invalid_location_id_cached(self, location_id: int) -> bool:
        if self.cache is None:
            return False

        try:
            key = f"{INVALID_LOCATION_IDS_KEY_PREFIX}:{location_id}"
            return self.cache.redis_client.exists(key) > 0
        except Exception as e:
            logger.warning(f"Error checking invalid location IDs cache: {e}")

        return False

    def mark_location_id_as_invalid(self, location_id: int) -> None:
        if self.cache is None:
            return

        try:
            key = f"{INVALID_LOCATION_IDS_KEY_PREFIX}:{location_id}"
            self.cache.redis_client.set(key, "1")
            logger.debug(f"Added invalid location ID {location_id} to cache")
        except Exception as e:
            logger.warning(f"Error adding invalid location ID to cache: {e}")

    def get_max_int32(self) -> int:
        return MAX_INT32
