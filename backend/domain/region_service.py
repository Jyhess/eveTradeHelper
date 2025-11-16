"""
Domain service for region management
Contains pure business logic, independent of infrastructure (async version)
"""

import asyncio
import logging
from collections import deque
from typing import Any

from .constants import DEFAULT_MAX_JUMPS
from .region_data import RegionData
from .repository import EveRepository

logger = logging.getLogger(__name__)


class RegionService:
    """Domain service for Eve Online regions (async)"""

    def __init__(self, repository: EveRepository, region_data: RegionData):
        """
        Initialize RegionService with a repository and RegionData

        Args:
            repository: Eve repository implementation
            region_data: RegionData instance for fast lookups
        """
        self.repository = repository
        self.region_data = region_data

    async def get_regions_with_details(self) -> list[dict[str, Any]]:
        region_ids = await self.repository.get_regions_list()

        async def fetch_region(region_id: int) -> dict[str, Any] | None:
            try:
                region_data = await self.repository.get_region_details(region_id)
                return {
                    "region_id": region_id,
                    "name": region_data.get("name", "Unknown"),
                    "description": region_data.get("description", ""),
                    "constellations": region_data.get("constellations", []),
                }
            except Exception as e:
                logger.warning(f"Error retrieving region {region_id}: {e}")
                return None

        results = await asyncio.gather(*[fetch_region(rid) for rid in region_ids])

        regions = [r for r in results if r is not None]
        return regions

    async def get_region_constellations_with_details(self, region_id: int) -> list[dict[str, Any]]:
        region_data = await self.repository.get_region_details(region_id)
        constellation_ids = region_data.get("constellations", [])

        async def fetch_constellation(
            constellation_id: int,
        ) -> dict[str, Any] | None:
            try:
                constellation_data = await self.repository.get_constellation_details(
                    constellation_id
                )
                return {
                    "constellation_id": constellation_id,
                    "name": constellation_data.get("name", "Unknown"),
                    "systems": constellation_data.get("systems", []),
                    "position": constellation_data.get("position", {}),
                }
            except Exception as e:
                logger.warning(f"Error retrieving constellation {constellation_id}: {e}")
                return None

        results = await asyncio.gather(*[fetch_constellation(cid) for cid in constellation_ids])

        constellations = [c for c in results if c is not None]
        return constellations

    async def get_constellation_systems_with_details(
        self, constellation_id: int
    ) -> list[dict[str, Any]]:
        constellation_data = await self.repository.get_constellation_details(constellation_id)
        system_ids = constellation_data.get("systems", [])

        async def fetch_system(system_id: int) -> dict[str, Any] | None:
            try:
                system_data = await self.repository.get_system_details(system_id)
                return {
                    "system_id": system_id,
                    "name": system_data.get("name", "Unknown"),
                    "security_status": system_data.get("security_status", 0.0),
                    "security_class": system_data.get("security_class", ""),
                    "position": system_data.get("position", {}),
                    "constellation_id": system_data.get("constellation_id"),
                    "planets": system_data.get("planets", []),
                    "star_id": system_data.get("star_id"),
                }
            except Exception as e:
                logger.warning(f"Error retrieving system {system_id}: {e}")
                return None

        results = await asyncio.gather(*[fetch_system(sid) for sid in system_ids])

        systems = [s for s in results if s is not None]
        return systems

    async def get_system_connections(self, system_id: int) -> list[dict[str, Any]]:
        system_data = await self.repository.get_system_details(system_id)
        stargate_ids = system_data.get("stargates", [])

        source_constellation_id = system_data.get("constellation_id")
        source_region_id = None
        if source_constellation_id:
            source_constellation = await self.repository.get_constellation_details(
                source_constellation_id
            )
            source_region_id = source_constellation.get("region_id")

        async def fetch_connection(stargate_id: int) -> dict[str, Any] | None:
            try:
                stargate_data = await self.repository.get_stargate_details(stargate_id)
                destination = stargate_data.get("destination", {})
                destination_system_id = destination.get("system_id")

                if destination_system_id and destination_system_id != system_id:
                    destination_system = await self.repository.get_system_details(
                        destination_system_id
                    )
                    destination_constellation_id = destination_system.get("constellation_id")

                    # Determine if the system is in the same constellation/region
                    same_constellation = destination_constellation_id == source_constellation_id
                    same_region = False
                    destination_region_id = None
                    destination_constellation_name = None
                    destination_region_name = None

                    if destination_constellation_id:
                        destination_constellation = await self.repository.get_constellation_details(
                            destination_constellation_id
                        )
                        destination_region_id = destination_constellation.get("region_id")
                        destination_constellation_name = destination_constellation.get(
                            "name", "Unknown"
                        )
                        same_region = destination_region_id == source_region_id

                        # Fetch region name if different
                        if destination_region_id and not same_region:
                            destination_region = await self.repository.get_region_details(
                                destination_region_id
                            )
                            destination_region_name = destination_region.get("name", "Unknown")

                    return {
                        "system_id": destination_system_id,
                        "name": destination_system.get("name", "Unknown"),
                        "security_status": destination_system.get("security_status", 0.0),
                        "security_class": destination_system.get("security_class", ""),
                        "stargate_id": stargate_id,
                        "constellation_id": destination_constellation_id,
                        "constellation_name": destination_constellation_name,
                        "region_id": destination_region_id,
                        "region_name": destination_region_name,
                        "same_constellation": same_constellation,
                        "same_region": same_region,
                    }
            except Exception as e:
                logger.warning(f"Error retrieving stargate {stargate_id}: {e}")
                return None

            return None

        results = await asyncio.gather(*[fetch_connection(sid) for sid in stargate_ids])

        connected_systems = [c for c in results if c is not None]
        return connected_systems

    async def get_system_details(self, system_id: int) -> dict[str, Any]:
        return await self.repository.get_system_details(system_id)

    async def get_constellation_details(self, constellation_id: int) -> dict[str, Any]:
        return await self.repository.get_constellation_details(constellation_id)

    async def get_region_details(self, region_id: int) -> dict[str, Any]:
        return await self.repository.get_region_details(region_id)

    async def _get_connected_system_ids(self, system_id: int) -> list[int]:
        try:
            system_data = await self.repository.get_system_details(system_id)
            stargate_ids = system_data.get("stargates", [])

            if not stargate_ids:
                return []

            async def get_destination_system_id(stargate_id: int) -> int | None:
                try:
                    stargate_data = await self.repository.get_stargate_details(stargate_id)
                    destination = stargate_data.get("destination", {})
                    return destination.get("system_id")
                except Exception as e:
                    logger.warning(f"Error retrieving stargate {stargate_id}: {e}")
                    return None

            results = await asyncio.gather(
                *[get_destination_system_id(sid) for sid in stargate_ids],
                return_exceptions=True,
            )

            connected_systems = [
                sid for sid in results if isinstance(sid, int) and sid != system_id
            ]
            return connected_systems
        except Exception as e:
            logger.warning(f"Error getting connected systems for {system_id}: {e}")
            return []

    async def get_systems_within_jumps(
        self, system_id: int, max_jumps: int = DEFAULT_MAX_JUMPS
    ) -> dict[str, Any]:
        systems_map: dict[int, dict[str, Any]] = {}
        connections: list[dict[str, Any]] = []
        visited: set[int] = set()
        queue: deque[tuple[int, int]] = deque([(system_id, 0)])

        while queue:
            current_system_id, current_jumps = queue.popleft()

            if current_system_id in visited:
                continue

            if current_jumps > max_jumps:
                continue

            visited.add(current_system_id)

            try:
                system_data = await self.repository.get_system_details(current_system_id)
                constellation_id = system_data.get("constellation_id")
                region_id = None
                if constellation_id:
                    constellation_data = await self.repository.get_constellation_details(
                        constellation_id
                    )
                    region_id = constellation_data.get("region_id")

                systems_map[current_system_id] = {
                    "system_id": current_system_id,
                    "name": system_data.get("name", "Unknown"),
                    "security_status": system_data.get("security_status", 0.0),
                    "security_class": system_data.get("security_class", ""),
                    "jumps": current_jumps,
                    "constellation_id": constellation_id,
                    "region_id": region_id,
                }

                if current_jumps < max_jumps:
                    connected_ids = await self._get_connected_system_ids(current_system_id)

                    for connected_id in connected_ids:
                        connections.append(
                            {
                                "from_system_id": current_system_id,
                                "to_system_id": connected_id,
                            }
                        )

                        if connected_id not in visited:
                            queue.append((connected_id, current_jumps + 1))

            except Exception as e:
                logger.warning(f"Error retrieving system {current_system_id}: {e}")

        return {
            "systems": list(systems_map.values()),
            "connections": connections,
        }

    async def get_all_systems(self, name_filter: str | None = None) -> list[dict[str, Any]]:
        """
        Retrieves all systems with optional name filter
        Uses RegionData cache for fast lookup

        Args:
            name_filter: Optional filter to match system names (case-insensitive)

        Returns:
            List of systems with their details
        """
        if name_filter:
            systems = await self.region_data.find_system_by_name(name_filter)
        else:
            systems = await self.region_data.get_all_systems()

        return sorted(systems, key=lambda x: x.get("name", ""))

    async def get_all_constellations(self, name_filter: str | None = None) -> list[dict[str, Any]]:
        if name_filter:
            constellations = await self.region_data.find_constellation_by_name(name_filter)
        else:
            constellations = await self.region_data.get_all_constellations()

        return sorted(constellations, key=lambda x: x.get("name", ""))

    async def search_systems(self, name_filter: str | None = None) -> list[dict[str, Any]]:
        all_systems = []
        region_ids = await self.repository.get_regions_list()

        for region_id in region_ids:
            try:
                constellations = await self.get_region_constellations_with_details(region_id)

                for constellation in constellations:
                    constellation_id_raw = constellation.get("constellation_id")
                    if not isinstance(constellation_id_raw, int):
                        continue
                    constellation_id = constellation_id_raw
                    system_ids = constellation.get("systems", [])

                    for system_id in system_ids:
                        try:
                            system_data = await self.repository.get_system_details(system_id)
                            system_name = system_data.get("name", "")

                            if name_filter and name_filter.lower() not in system_name.lower():
                                continue

                            constellation_data = await self.repository.get_constellation_details(
                                constellation_id
                            )
                            region_id_from_constellation = constellation_data.get("region_id")

                            all_systems.append(
                                {
                                    "system_id": system_id,
                                    "name": system_name,
                                    "security_status": system_data.get("security_status", 0.0),
                                    "security_class": system_data.get("security_class", ""),
                                    "constellation_id": constellation_id,
                                    "region_id": region_id_from_constellation,
                                }
                            )
                        except Exception as e:
                            logger.warning(f"Error retrieving system {system_id}: {e}")
                            continue
            except Exception as e:
                logger.warning(f"Error retrieving constellations for region {region_id}: {e}")
                continue

        return all_systems

    async def search_constellations(self, name_filter: str | None = None) -> list[dict[str, Any]]:
        all_constellations = []
        region_ids = await self.repository.get_regions_list()

        for region_id in region_ids:
            try:
                constellations = await self.get_region_constellations_with_details(region_id)

                for constellation in constellations:
                    constellation_id_raw = constellation.get("constellation_id")
                    if not isinstance(constellation_id_raw, int):
                        continue
                    constellation_id = constellation_id_raw
                    constellation_name = constellation.get("name", "")

                    if name_filter and name_filter.lower() not in constellation_name.lower():
                        continue

                    try:
                        constellation_data = await self.repository.get_constellation_details(
                            constellation_id
                        )
                        region_id_from_constellation = constellation_data.get("region_id")

                        all_constellations.append(
                            {
                                "constellation_id": constellation_id,
                                "name": constellation_name,
                                "region_id": region_id_from_constellation,
                            }
                        )
                    except Exception as e:
                        logger.warning(
                            f"Error retrieving constellation details {constellation_id}: {e}"
                        )
                        continue
            except Exception as e:
                logger.warning(f"Error retrieving constellations for region {region_id}: {e}")
                continue

        return all_constellations
