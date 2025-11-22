"""
RegionData class for fast lookup of regions, constellations, and systems
Auto-initializes on first use
"""

import asyncio
import logging
from typing import Any

from .eve_repository import EveRepository

logger = logging.getLogger(__name__)


class RegionData:
    """Fast lookup cache for regions, constellations, and systems"""

    def __init__(self, repository: EveRepository):
        self.repository = repository
        self._regions_by_id: dict[int, dict[str, Any]] = {}
        self._regions_by_name: dict[str, list[dict[str, Any]]] = {}
        self._constellations_by_id: dict[int, dict[str, Any]] = {}
        self._constellations_by_name: dict[str, list[dict[str, Any]]] = {}
        self._systems_by_id: dict[int, dict[str, Any]] = {}
        self._systems_by_name: dict[str, list[dict[str, Any]]] = {}
        self._initialized = False
        self._initializing = False
        self._init_lock = asyncio.Lock()

    async def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        async with self._init_lock:
            if self._initialized:
                return

            if self._initializing:
                while self._initializing:
                    await asyncio.sleep(0.01)
                return

            self._initializing = True
            try:
                await self._initialize()
            finally:
                self._initializing = False
                self._initialized = True

    async def _initialize(self) -> None:
        """
        Initialize the data cache by loading all regions, constellations, and systems
        Internal method - use _ensure_initialized() for thread-safe lazy initialization
        """

        logger.info("Initializing RegionData cache...")
        region_ids = await self.repository.get_regions_list()

        for region_id in region_ids:
            try:
                region_data = await self.repository.get_region_details(region_id)
                region_name = region_data.name
                constellation_ids = region_data.constellations

                region_info = {
                    "region_id": region_id,
                    "name": region_name,
                }
                self._regions_by_id[region_id] = region_info
                self._add_to_name_index(self._regions_by_name, region_name, region_info)

                for constellation_id in constellation_ids:
                    try:
                        constellation_data = await self.repository.get_constellation_details(
                            constellation_id
                        )
                        constellation_name = constellation_data.name
                        system_ids = constellation_data.systems

                        constellation_info = {
                            "constellation_id": constellation_id,
                            "name": constellation_name,
                            "region_id": region_id,
                        }
                        self._constellations_by_id[constellation_id] = constellation_info
                        self._add_to_name_index(
                            self._constellations_by_name, constellation_name, constellation_info
                        )

                        for system_id in system_ids:
                            try:
                                system_data = await self.repository.get_system_details(system_id)
                                system_name = system_data.name
                                security_status = system_data.security_status
                                security_class = system_data.security_class

                                system_info = {
                                    "system_id": system_id,
                                    "name": system_name,
                                    "security_status": security_status,
                                    "security_class": security_class,
                                    "constellation_id": constellation_id,
                                    "region_id": region_id,
                                }
                                self._systems_by_id[system_id] = system_info
                                self._add_to_name_index(
                                    self._systems_by_name, system_name, system_info
                                )
                            except Exception as e:
                                logger.warning(f"Error loading system {system_id}: {e}")
                                continue
                    except Exception as e:
                        logger.warning(f"Error loading constellation {constellation_id}: {e}")
                        continue
            except Exception as e:
                logger.warning(f"Error loading region {region_id}: {e}")
                continue

        self._initialized = True
        logger.info(
            f"RegionData initialized: {len(self._regions_by_id)} regions, "
            f"{len(self._constellations_by_id)} constellations, "
            f"{len(self._systems_by_id)} systems"
        )

    def _add_to_name_index(
        self, index: dict[str, list[dict[str, Any]]], name: str, item: dict[str, Any]
    ) -> None:
        name_lower = name.lower()
        if name_lower not in index:
            index[name_lower] = []
        index[name_lower].append(item)

    async def find_region_by_id(self, region_id: int) -> dict[str, Any] | None:
        await self._ensure_initialized()
        return self._regions_by_id.get(region_id)

    async def find_region_by_name(self, name: str) -> list[dict[str, Any]]:
        await self._ensure_initialized()
        name_lower = name.lower()
        results = []

        for indexed_name, regions in self._regions_by_name.items():
            if name_lower in indexed_name:
                results.extend(regions)

        return results

    async def find_constellation_by_id(self, constellation_id: int) -> dict[str, Any] | None:
        await self._ensure_initialized()
        return self._constellations_by_id.get(constellation_id)

    async def find_constellation_by_name(self, name: str) -> list[dict[str, Any]]:
        await self._ensure_initialized()
        name_lower = name.lower()
        results = []

        for indexed_name, constellations in self._constellations_by_name.items():
            if name_lower in indexed_name:
                results.extend(constellations)

        return results

    async def find_system_by_id(self, system_id: int) -> dict[str, Any] | None:
        await self._ensure_initialized()
        return self._systems_by_id.get(system_id)

    async def find_system_by_name(self, name: str) -> list[dict[str, Any]]:
        await self._ensure_initialized()
        name_lower = name.lower()
        results = []

        for indexed_name, systems in self._systems_by_name.items():
            if name_lower in indexed_name:
                results.extend(systems)

        return results

    async def get_all_systems(self) -> list[dict[str, Any]]:
        await self._ensure_initialized()
        return list(self._systems_by_id.values())

    async def get_all_constellations(self) -> list[dict[str, Any]]:
        await self._ensure_initialized()
        return list(self._constellations_by_id.values())
