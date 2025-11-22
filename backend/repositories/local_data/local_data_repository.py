import json
import logging
from pathlib import Path
from typing import Any, Iterable

from utils.cache import SimpleCache

from .id_ranges import IdRanges

logger = logging.getLogger(__name__)

STATIC_DATA_DIR = Path(__file__).parent.parent.parent / "eve-online-static-data-jsonl"
TYPES_FROM_ID_FILE = STATIC_DATA_DIR / "typesFromId.json"
TYPES_JSONL_FILE = STATIC_DATA_DIR / "types.jsonl"
INVALID_LOCATION_IDS_KEY_PREFIX = "invalid_location_ids"
MAX_INT32 = 2147483647


class LocalDataRepository:
    def __init__(self, cache: SimpleCache):
        self.cache = cache
        self.id_ranges: list[dict[str, Any]] = []
        self._types_data: list[dict[str, Any]] | None = None
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

    def _ensure_types_data_loaded(self) -> None:
        if self._types_data is not None:
            return

        self._types_data = []

        if not TYPES_JSONL_FILE.exists():
            logger.warning(
                "Types JSONL file not found at %s. Type search will be disabled.",
                TYPES_JSONL_FILE,
            )
            return

        try:
            with open(TYPES_JSONL_FILE, encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    type_id = data.get("_key")
                    if not isinstance(type_id, int):
                        continue

                    names = data.get("name")
                    english_name: str | None = None
                    if isinstance(names, dict):
                        english_name = names.get("en") or names.get("fr")
                    elif isinstance(names, str):
                        english_name = names

                    if not english_name:
                        continue

                    published = data.get("published", True)
                    self._types_data.append(
                        {
                            "type_id": type_id,
                            "name": english_name,
                            "published": published,
                        }
                    )
            logger.info("Loaded %d types from %s", len(self._types_data), TYPES_JSONL_FILE)
        except Exception as exc:  # pragma: no cover - logging only
            logger.error("Error loading types from %s: %s", TYPES_JSONL_FILE, exc)
            self._types_data = []

    def search_types(
        self, query: str | None = None, limit: int = 20
    ) -> list[dict[str, Any]]:
        self._ensure_types_data_loaded()
        if not self._types_data:
            return []

        # If no query, return all published types (sorted by name)
        if not query or not query.strip():
            all_types = [
                {"type_id": entry["type_id"], "name": entry["name"]}
                for entry in self._types_data
                if entry["published"]
            ]
            all_types.sort(key=lambda x: x["name"].lower())
            return all_types[:limit]

        query_normalized = query.strip().lower()

        def sort_key(entry: dict[str, Any]):
            name_lower = entry["name"].lower()
            exact = name_lower == query_normalized
            starts = name_lower.startswith(query_normalized)
            return (
                0 if exact else 1,
                0 if starts else 1,
                len(name_lower),
                name_lower,
            )

        matches: Iterable[dict[str, Any]] = (
            {"type_id": entry["type_id"], "name": entry["name"]}
            for entry in self._types_data
            if entry["published"] and query_normalized in entry["name"].lower()
        )

        sorted_matches = sorted(matches, key=sort_key)
        return sorted_matches[:limit]
