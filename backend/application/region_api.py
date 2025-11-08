"""
API for region management
FastAPI endpoints for regions (async)
"""

import logging
import os
from collections.abc import Hashable
from typing import Any

from cachetools import TTLCache
from fastapi import APIRouter, Depends, HTTPException

from application.utils import cached_async
from domain.constants import ADJACENT_REGIONS_CACHE_TTL
from domain.region_service import RegionService

from .services_provider import ServicesProvider

logger = logging.getLogger(__name__)
router = APIRouter()
region_router = router

# LRU cache with TTL for adjacent regions (in memory)
# Adjacent regions change rarely, so a long TTL is appropriate
_adjacent_regions_cache: TTLCache[Hashable, Any] = TTLCache(
    maxsize=100, ttl=ADJACENT_REGIONS_CACHE_TTL
)


@router.get("/api/v1/regions")
async def get_regions(region_service: RegionService = Depends(ServicesProvider.get_region_service)):
    """
    Retrieves the list of Eve Online regions with their details
    Cache is automatically managed by the infrastructure layer (EveAPIClient)

    Returns:
        JSON response with regions
    """
    try:
        logger.info("Retrieving regions")
        limit = int(os.getenv("REGIONS_LIMIT", "50"))
        regions = await region_service.get_regions_with_details(limit=limit)

        # Sort by name
        regions_sorted = sorted(regions, key=lambda x: x.get("name", ""))

        return {
            "total": len(regions_sorted),
            "regions": regions_sorted,
        }

    except Exception as e:
        logger.error(f"Error retrieving regions: {e}")
        raise HTTPException(
            status_code=500, detail=f"ESI API connection error: {str(e)}"
        ) from None


@router.get("/api/v1/regions/{region_id}/constellations")
async def get_region_constellations(
    region_id: int, region_service: RegionService = Depends(ServicesProvider.get_region_service)
):
    """
    Retrieves details of all constellations in a region
    Cache is automatically managed by the infrastructure layer (EveAPIClient)

    Args:
        region_id: Region ID

    Returns:
        JSON response with constellations
    """
    try:
        logger.info(f"Retrieving constellations for region {region_id}")
        constellations = await region_service.get_region_constellations_with_details(region_id)

        # Sort by name
        constellations_sorted = sorted(constellations, key=lambda x: x.get("name", ""))

        return {
            "region_id": region_id,
            "total": len(constellations_sorted),
            "constellations": constellations_sorted,
        }

    except Exception as e:
        logger.error(f"Error retrieving constellations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ESI API connection error: {str(e)}",
        ) from None


@router.get("/api/v1/constellations/{constellation_id}/systems")
async def get_constellation_systems(
    constellation_id: int,
    region_service: RegionService = Depends(ServicesProvider.get_region_service),
):
    """
    Retrieves details of all systems in a constellation
    Cache is automatically managed by the infrastructure layer (EveAPIClient)

    Args:
        constellation_id: Constellation ID

    Returns:
        JSON response with systems
    """
    try:
        logger.info(f"Retrieving systems for constellation {constellation_id}")
        systems = await region_service.get_constellation_systems_with_details(constellation_id)

        # Sort by name
        systems_sorted = sorted(systems, key=lambda x: x.get("name", ""))

        return {
            "constellation_id": constellation_id,
            "total": len(systems_sorted),
            "systems": systems_sorted,
        }

    except Exception as e:
        logger.error(f"Error retrieving systems: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ESI API connection error: {str(e)}",
        ) from None


@router.get("/api/v1/systems/{system_id}")
async def get_system_details(
    system_id: int, region_service: RegionService = Depends(ServicesProvider.get_region_service)
):
    """
    Retrieves details of a solar system
    Cache is automatically managed by the infrastructure layer (EveAPIClient)

    Args:
        system_id: System ID

    Returns:
        JSON response with system details
    """
    try:
        logger.info(f"Retrieving system details for {system_id}")
        system_data = await region_service.get_system_details(system_id)

        # Format data as needed
        system = {
            "system_id": system_id,
            "name": system_data.get("name", "Unknown"),
            "security_status": system_data.get("security_status", 0.0),
            "security_class": system_data.get("security_class", ""),
            "position": system_data.get("position", {}),
            "constellation_id": system_data.get("constellation_id"),
            "planets": system_data.get("planets", []),
            "star_id": system_data.get("star_id"),
        }

        return {
            "system_id": system_id,
            "system": system,
        }

    except Exception as e:
        logger.error(f"Error retrieving system details: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ESI API connection error: {str(e)}",
        ) from None


@router.get("/api/v1/systems/{system_id}/connections")
async def get_system_connections(
    system_id: int, region_service: RegionService = Depends(ServicesProvider.get_region_service)
):
    """
    Retrieves systems connected to a given system via stargates
    Cache is automatically managed by the infrastructure layer (EveAPIClient)

    Args:
        system_id: System ID

    Returns:
        JSON response with connected systems
    """
    try:
        logger.info(f"Retrieving connections for system {system_id}")
        connections = await region_service.get_system_connections(system_id)

        # Sort by name
        connections_sorted = sorted(connections, key=lambda x: x.get("name", ""))

        return {
            "system_id": system_id,
            "total": len(connections_sorted),
            "connections": connections_sorted,
        }

    except Exception as e:
        logger.error(f"Error retrieving connections: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ESI API connection error: {str(e)}",
        ) from None


@router.get("/api/v1/constellations/{constellation_id}")
async def get_constellation_info(
    constellation_id: int,
    region_service: RegionService = Depends(ServicesProvider.get_region_service),
):
    """
    Retrieves information about a constellation and its parent region.
    Cache is automatically managed by the infrastructure layer (EveAPIClient).

    Args:
        constellation_id: Constellation ID

    Returns:
        JSON response with constellation and region details.
    """
    try:
        logger.info(f"Retrieving constellation info for {constellation_id}")

        # Fetch constellation details
        constellation_data = await region_service.get_constellation_details(constellation_id)
        region_id = constellation_data.get("region_id")

        # Fetch region details
        region_data = None
        if region_id:
            region_data = await region_service.get_region_details(region_id)

        # Format data
        info = {
            "constellation": {
                "constellation_id": constellation_id,
                "name": constellation_data.get("name", "Unknown"),
                "region_id": region_id,
            },
        }

        if region_data:
            info["region"] = {
                "region_id": region_id,
                "name": region_data.get("name", "Unknown"),
            }

        return info

    except Exception as e:
        logger.error(f"Error retrieving constellation info: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"ESI API connection error: {str(e)}",
        ) from None


@router.get("/api/v1/regions/{region_id}/adjacent")
@cached_async(_adjacent_regions_cache, exclude_types=(RegionService,))
async def get_adjacent_regions(
    region_id: int,
    region_service: RegionService = Depends(ServicesProvider.get_region_service),
):
    """
    Retrieves the list of regions adjacent to a given region
    Adjacent regions are determined by traversing the region's systems
    and their connections via stargates to other regions

    Business logic in the application layer

    Args:
        region_id: Region ID

    Returns:
        JSON response with adjacent regions
    """
    import asyncio

    try:
        logger.info(f"Retrieving adjacent regions for region {region_id}")

        # Fetch region details to get constellations
        region_details = await region_service.get_region_details(region_id)
        constellation_ids = region_details.get("constellations", [])

        if not constellation_ids:
            return {
                "region_id": region_id,
                "total": 0,
                "adjacent_regions": [],
            }

        # Fetch constellation details to get systems
        constellation_details_list = await asyncio.gather(
            *[region_service.get_constellation_details(cid) for cid in constellation_ids],
            return_exceptions=True,
        )

        # Collect all systems in the region
        systems_in_region = set()
        for constellation_data in constellation_details_list:
            if isinstance(constellation_data, dict):
                systems_in_region.update(constellation_data.get("systems", []))

        if not systems_in_region:
            return {
                "region_id": region_id,
                "total": 0,
                "adjacent_regions": [],
            }

        # For each system, fetch its details and find adjacent systems
        async def get_system_adjacent_regions(system_id: int) -> set:
            """Returns IDs of adjacent regions via this system"""
            try:
                system_details = await region_service.get_system_details(system_id)
                stargate_ids = system_details.get("stargates", [])

                if not stargate_ids:
                    return set()

                # Fetch details of each stargate to find the destination system
                # Note: get_stargate_details is not yet in RegionService, temporary direct usage
                stargate_details_list = await asyncio.gather(
                    *[
                        region_service.repository.get_stargate_details(sgid)
                        for sgid in stargate_ids
                    ],
                    return_exceptions=True,
                )

                adjacent_regions = set()
                for stargate_data in stargate_details_list:
                    if isinstance(stargate_data, dict):
                        destination_system_id = stargate_data.get("destination", {}).get(
                            "system_id"
                        )
                        if destination_system_id:
                            # Fetch destination system details to get its constellation
                            try:
                                dest_system_details = await region_service.get_system_details(
                                    destination_system_id
                                )
                                dest_constellation_id = dest_system_details.get("constellation_id")
                                if dest_constellation_id:
                                    # Fetch constellation to get the region
                                    dest_constellation = (
                                        await region_service.get_constellation_details(
                                            dest_constellation_id
                                        )
                                    )
                                    dest_region_id = dest_constellation.get("region_id")
                                    if dest_region_id and dest_region_id != region_id:
                                        adjacent_regions.add(dest_region_id)
                            except Exception as e:
                                logger.warning(
                                    f"Error retrieving system {destination_system_id}: {e}"
                                )
                                continue

                return adjacent_regions
            except Exception as e:
                logger.warning(f"Error retrieving system {system_id}: {e}")
                return set()

        # Fetch adjacent regions for all systems in parallel
        results = await asyncio.gather(
            *[get_system_adjacent_regions(sid) for sid in systems_in_region],
            return_exceptions=True,
        )

        # Collect all unique adjacent regions
        adjacent_region_ids = set()
        for result_set in results:
            if isinstance(result_set, set):
                adjacent_region_ids.update(result_set)

        if not adjacent_region_ids:
            return {
                "region_id": region_id,
                "total": 0,
                "adjacent_regions": [],
            }

        # Fetch details of each adjacent region in parallel
        async def fetch_adjacent_region(adj_region_id: int) -> dict[str, Any] | None:
            try:
                region_data = await region_service.get_region_details(adj_region_id)
                return {
                    "region_id": adj_region_id,
                    "name": region_data.get("name", f"Region {adj_region_id}"),
                    "description": region_data.get("description", ""),
                }
            except Exception as e:
                logger.warning(f"Error retrieving region {adj_region_id}: {e}")
                return None

        adjacent_regions_results = await asyncio.gather(
            *[fetch_adjacent_region(rid) for rid in adjacent_region_ids],
            return_exceptions=True,
        )

        # Filter None results and exceptions
        adjacent_regions = [
            r for r in adjacent_regions_results if isinstance(r, dict) and r is not None
        ]

        # Sort by name
        adjacent_regions.sort(key=lambda x: x.get("name", ""))

        return {
            "region_id": region_id,
            "total": len(adjacent_regions),
            "adjacent_regions": adjacent_regions,
        }

    except Exception as e:
        logger.error(f"Error retrieving adjacent regions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving adjacent regions: {str(e)}",
        ) from None
