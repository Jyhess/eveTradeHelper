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
CONTRABAND_TYPES_FILE = STATIC_DATA_DIR / "contrabandTypes.jsonl"
MAP_SOLAR_SYSTEMS_FILE = STATIC_DATA_DIR / "mapSolarSystems.jsonl"
MAP_REGIONS_FILE = STATIC_DATA_DIR / "mapRegions.jsonl"
INVALID_LOCATION_IDS_KEY_PREFIX = "invalid_location_ids"
MAX_INT32 = 2147483647


class LocalDataRepository:
    def __init__(self, cache: SimpleCache):
        self.cache = cache
        self.id_ranges: list[dict[str, Any]] = []
        self._types_data: list[dict[str, Any]] | None = None
        self._contraband_data: dict[int, list[int]] | None = None
        self._systems_faction_map: dict[int, int | None] | None = None
        self._regions_faction_map: dict[int, int | None] | None = None
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

    def _load_contraband_data(self) -> None:
        """Load contraband types data from JSONL file"""
        if self._contraband_data is not None:
            return

        self._contraband_data = {}

        if not CONTRABAND_TYPES_FILE.exists():
            logger.warning(f"Contraband types file not found: {CONTRABAND_TYPES_FILE}")
            return

        try:
            with open(CONTRABAND_TYPES_FILE, encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        type_id = data.get("_key")
                        factions = data.get("factions", [])

                        if isinstance(type_id, int) and isinstance(factions, list):
                            faction_ids: list[int] = []
                            for f in factions:
                                if isinstance(f, dict):
                                    faction_key = f.get("_key")
                                    if isinstance(faction_key, int):
                                        faction_ids.append(faction_key)
                            if faction_ids:
                                self._contraband_data[type_id] = faction_ids
                    except json.JSONDecodeError:
                        continue
            logger.info("Loaded %d contraband types from %s", len(self._contraband_data), CONTRABAND_TYPES_FILE)
        except Exception as exc:  # pragma: no cover - logging only
            logger.error("Error loading contraband types from %s: %s", CONTRABAND_TYPES_FILE, exc)
            self._contraband_data = {}

    def _load_systems_faction_map(self) -> None:
        """Load systems to faction mapping from JSONL file"""
        if self._systems_faction_map is not None:
            return

        self._systems_faction_map = {}

        if not MAP_SOLAR_SYSTEMS_FILE.exists():
            logger.warning(f"Solar systems file not found: {MAP_SOLAR_SYSTEMS_FILE}")
            return

        try:
            with open(MAP_SOLAR_SYSTEMS_FILE, encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        system_id = data.get("_key")
                        faction_id = data.get("factionID")

                        if isinstance(system_id, int):
                            self._systems_faction_map[system_id] = (
                                faction_id if isinstance(faction_id, int) else None
                            )
                    except json.JSONDecodeError:
                        continue
            logger.info(
                "Loaded %d systems with faction mapping from %s",
                len(self._systems_faction_map),
                MAP_SOLAR_SYSTEMS_FILE,
            )
        except Exception as exc:  # pragma: no cover - logging only
            logger.error("Error loading systems faction map from %s: %s", MAP_SOLAR_SYSTEMS_FILE, exc)
            self._systems_faction_map = {}

    def is_contraband_for_faction(self, type_id: int, faction_id: int) -> bool:
        """Check if an item is contraband for a specific faction"""
        self._load_contraband_data()
        if not self._contraband_data:
            return False

        contraband_factions = self._contraband_data.get(type_id, [])
        return faction_id in contraband_factions

    def get_system_faction_id(self, system_id: int) -> int | None:
        """Get the faction ID for a system, or None if not available"""
        self._load_systems_faction_map()
        if not self._systems_faction_map:
            return None

        return self._systems_faction_map.get(system_id)

    def _load_regions_faction_map(self) -> None:
        """Load regions to faction mapping from JSONL file"""
        if self._regions_faction_map is not None:
            return

        self._regions_faction_map = {}

        if not MAP_REGIONS_FILE.exists():
            logger.warning(f"Regions file not found: {MAP_REGIONS_FILE}")
            return

        try:
            with open(MAP_REGIONS_FILE, encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                        region_id = data.get("_key")
                        faction_id = data.get("factionID")

                        if isinstance(region_id, int):
                            self._regions_faction_map[region_id] = (
                                faction_id if isinstance(faction_id, int) else None
                            )
                    except json.JSONDecodeError:
                        continue
            logger.info(
                "Loaded %d regions with faction mapping from %s",
                len(self._regions_faction_map),
                MAP_REGIONS_FILE,
            )
        except Exception as exc:  # pragma: no cover - logging only
            logger.error("Error loading regions faction map from %s: %s", MAP_REGIONS_FILE, exc)
            self._regions_faction_map = {}

    def get_region_faction_id(self, region_id: int) -> int | None:
        """Get the faction ID for a region, or None if not available"""
        self._load_regions_faction_map()
        if not self._regions_faction_map:
            return None

        return self._regions_faction_map.get(region_id)
