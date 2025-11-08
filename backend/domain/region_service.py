"""
Domain service for region management
Contains pure business logic, independent of infrastructure (async version)
"""

import asyncio
import logging
from typing import Any

from .repository import EveRepository

logger = logging.getLogger(__name__)


class RegionService:
    """Domain service for Eve Online regions (async)"""

    def __init__(self, repository: EveRepository):
        """
        Initialize the service with a repository

        Args:
            repository: Eve repository implementation
        """
        self.repository = repository

    async def get_regions_with_details(self, limit: int | None = None) -> list[dict[str, Any]]:
        """
        Retrieves the list of regions with their details
        Business logic: orchestration of repository calls (parallelized)

        Args:
            limit: Maximum number of regions to retrieve (None = all)

        Returns:
            List of regions with their formatted details

        Raises:
            Exception: If an error occurs during retrieval
        """
        # Fetch the list of IDs from the repository
        region_ids = await self.repository.get_regions_list()

        # Apply limit if specified (business logic)
        if limit:
            region_ids = region_ids[:limit]

        # Fetch details of each region in parallel
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
                # Log the error but continue with other regions
                logger.warning(f"Error retrieving region {region_id}: {e}")
                return None

        # Execute all requests in parallel
        results = await asyncio.gather(*[fetch_region(rid) for rid in region_ids])

        # Filter None results
        regions = [r for r in results if r is not None]
        return regions

    async def get_region_constellations_with_details(self, region_id: int) -> list[dict[str, Any]]:
        """
        Retrieves details of all constellations in a region
        Business logic: orchestration of repository calls (parallelized)

        Args:
            region_id: Region ID

        Returns:
            List of constellations with their formatted details

        Raises:
            Exception: If an error occurs during retrieval
        """
        # Fetch region details to get constellation IDs
        region_data = await self.repository.get_region_details(region_id)
        constellation_ids = region_data.get("constellations", [])

        # Fetch details of each constellation in parallel
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
                logger.warning(
                    f"Error retrieving constellation {constellation_id}: {e}"
                )
                return None

        # Execute all requests in parallel
        results = await asyncio.gather(*[fetch_constellation(cid) for cid in constellation_ids])

        # Filter None results
        constellations = [c for c in results if c is not None]
        return constellations

    async def get_constellation_systems_with_details(
        self, constellation_id: int
    ) -> list[dict[str, Any]]:
        """
        Retrieves details of all systems in a constellation
        Business logic: orchestration of repository calls (parallelized)

        Args:
            constellation_id: Constellation ID

        Returns:
            List of systems with their formatted details

        Raises:
            Exception: If an error occurs during retrieval
        """
        # Fetch constellation details to get system IDs
        constellation_data = await self.repository.get_constellation_details(constellation_id)
        system_ids = constellation_data.get("systems", [])

        # Fetch details of each system in parallel
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

        # Execute all requests in parallel
        results = await asyncio.gather(*[fetch_system(sid) for sid in system_ids])

        # Filter None results
        systems = [s for s in results if s is not None]
        return systems

    async def get_system_connections(self, system_id: int) -> list[dict[str, Any]]:
        """
        Retrieves systems connected to a given system via stargates
        Business logic: orchestration of repository calls

        Args:
            system_id: System ID

        Returns:
            List of connected systems with their details

        Raises:
            Exception: If an error occurs during retrieval
        """
        # Fetch system details to get stargate IDs
        system_data = await self.repository.get_system_details(system_id)
        stargate_ids = system_data.get("stargates", [])

        # Fetch source system's constellation and region for comparison
        source_constellation_id = system_data.get("constellation_id")
        source_region_id = None
        if source_constellation_id:
            source_constellation = await self.repository.get_constellation_details(
                source_constellation_id
            )
            source_region_id = source_constellation.get("region_id")

        # Function to fetch connection details
        async def fetch_connection(stargate_id: int) -> dict[str, Any] | None:
            try:
                stargate_data = await self.repository.get_stargate_details(stargate_id)
                destination = stargate_data.get("destination", {})
                destination_system_id = destination.get("system_id")

                if destination_system_id and destination_system_id != system_id:
                    # Fetch destination system details
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

        # Execute all requests in parallel
        results = await asyncio.gather(*[fetch_connection(sid) for sid in stargate_ids])

        # Filter None results
        connected_systems = [c for c in results if c is not None]
        return connected_systems

    async def get_system_details(self, system_id: int) -> dict[str, Any]:
        return await self.repository.get_system_details(system_id)

    async def get_constellation_details(self, constellation_id: int) -> dict[str, Any]:
        return await self.repository.get_constellation_details(constellation_id)

    async def get_region_details(self, region_id: int) -> dict[str, Any]:
        return await self.repository.get_region_details(region_id)
