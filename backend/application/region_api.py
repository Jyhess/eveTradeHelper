"""
API pour la gestion des régions
Endpoints FastAPI pour les régions (asynchrone)
"""

import os
import logging
from cachetools import TTLCache
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from domain.region_service import RegionService
from domain.constants import ADJACENT_REGIONS_CACHE_TTL
from application.utils import cached_async

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache LRU avec TTL pour les régions adjacentes (en mémoire)
# Les régions adjacentes changent rarement, donc un TTL long est approprié
_adjacent_regions_cache = TTLCache(maxsize=100, ttl=ADJACENT_REGIONS_CACHE_TTL)


# Variable globale pour stocker le service (sera initialisé dans app.py)
_region_service: Optional[RegionService] = None


def get_region_service() -> RegionService:
    """Dependency pour obtenir le service de région"""
    if _region_service is None:
        raise HTTPException(status_code=503, detail="Service non initialisé")
    return _region_service


def set_region_service(service: RegionService):
    """Initialise le service de région"""
    global _region_service
    _region_service = service


@router.get("/api/v1/regions")
async def get_regions(region_service: RegionService = Depends(get_region_service)):
    """
    Récupère la liste des régions d'Eve Online avec leurs détails
    Le cache est géré automatiquement par la couche infrastructure (EveAPIClient)

    Returns:
        Réponse JSON avec les régions
    """
    try:
        logger.info("Récupération des régions")
        limit = int(os.getenv("REGIONS_LIMIT", "50"))
        regions = await region_service.get_regions_with_details(limit=limit)

        # Trier par nom
        regions_sorted = sorted(regions, key=lambda x: x.get("name", ""))

        return {
            "total": len(regions_sorted),
            "regions": regions_sorted,
        }

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des régions: {e}")
        raise HTTPException(
            status_code=500, detail=f"Erreur de connexion à l'API ESI: {str(e)}"
        )


@router.get("/api/v1/regions/{region_id}/constellations")
async def get_region_constellations(
    region_id: int, region_service: RegionService = Depends(get_region_service)
):
    """
    Récupère les détails de toutes les constellations d'une région
    Le cache est géré automatiquement par la couche infrastructure (EveAPIClient)

    Args:
        region_id: ID de la région

    Returns:
        Réponse JSON avec les constellations
    """
    try:
        logger.info(f"Récupération des constellations de la région {region_id}")
        constellations = await region_service.get_region_constellations_with_details(
            region_id
        )

        # Trier par nom
        constellations_sorted = sorted(constellations, key=lambda x: x.get("name", ""))

        return {
            "region_id": region_id,
            "total": len(constellations_sorted),
            "constellations": constellations_sorted,
        }

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des constellations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion à l'API ESI: {str(e)}",
        )


@router.get("/api/v1/constellations/{constellation_id}/systems")
async def get_constellation_systems(
    constellation_id: int,
    region_service: RegionService = Depends(get_region_service),
):
    """
    Récupère les détails de tous les systèmes d'une constellation
    Le cache est géré automatiquement par la couche infrastructure (EveAPIClient)

    Args:
        constellation_id: ID de la constellation

    Returns:
        Réponse JSON avec les systèmes
    """
    try:
        logger.info(f"Récupération des systèmes de la constellation {constellation_id}")
        systems = await region_service.get_constellation_systems_with_details(
            constellation_id
        )

        # Trier par nom
        systems_sorted = sorted(systems, key=lambda x: x.get("name", ""))

        return {
            "constellation_id": constellation_id,
            "total": len(systems_sorted),
            "systems": systems_sorted,
        }

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des systèmes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion à l'API ESI: {str(e)}",
        )


@router.get("/api/v1/systems/{system_id}")
async def get_system_details(
    system_id: int, region_service: RegionService = Depends(get_region_service)
):
    """
    Récupère les détails d'un système solaire
    Le cache est géré automatiquement par la couche infrastructure (EveAPIClient)

    Args:
        system_id: ID du système

    Returns:
        Réponse JSON avec les détails du système
    """
    try:
        logger.info(f"Récupération des détails du système {system_id}")
        system_data = await region_service.get_system_details(system_id)

        # Formater les données selon le besoin
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
        logger.error(f"Erreur lors de la récupération des détails du système: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion à l'API ESI: {str(e)}",
        )


@router.get("/api/v1/systems/{system_id}/connections")
async def get_system_connections(
    system_id: int, region_service: RegionService = Depends(get_region_service)
):
    """
    Récupère les systèmes connectés à un système donné via les stargates
    Le cache est géré automatiquement par la couche infrastructure (EveAPIClient)

    Args:
        system_id: ID du système

    Returns:
        Réponse JSON avec les systèmes connectés
    """
    try:
        logger.info(f"Récupération des connexions du système {system_id}")
        connections = await region_service.get_system_connections(system_id)

        # Trier par nom
        connections_sorted = sorted(connections, key=lambda x: x.get("name", ""))

        return {
            "system_id": system_id,
            "total": len(connections_sorted),
            "connections": connections_sorted,
        }

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des connexions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion à l'API ESI: {str(e)}",
        )


@router.get("/api/v1/constellations/{constellation_id}")
async def get_constellation_info(
    constellation_id: int,
    region_service: RegionService = Depends(get_region_service),
):
    """
    Récupère les informations d'une constellation et de sa région parente.
    Le cache est géré automatiquement par la couche infrastructure (EveAPIClient).

    Args:
        constellation_id: ID de la constellation

    Returns:
        Réponse JSON avec les détails de la constellation et de la région.
    """
    try:
        logger.info(f"Récupération des infos de la constellation {constellation_id}")

        # Récupérer les détails de la constellation
        constellation_data = await region_service.get_constellation_details(
            constellation_id
        )
        region_id = constellation_data.get("region_id")

        # Récupérer les détails de la région
        region_data = None
        if region_id:
            region_data = await region_service.get_region_details(region_id)

        # Formater les données
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
        logger.error(
            f"Erreur lors de la récupération des infos de la constellation: {e}"
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion à l'API ESI: {str(e)}",
        )


@router.get("/api/v1/regions/{region_id}/adjacent")
@cached_async(_adjacent_regions_cache, exclude_types=(RegionService,))
async def get_adjacent_regions(
    region_id: int,
    region_service: RegionService = Depends(get_region_service),
):
    """
    Récupère la liste des régions adjacentes à une région donnée
    Les régions adjacentes sont déterminées en parcourant les systèmes de la région
    et leurs connexions via stargates vers d'autres régions

    Logique métier dans la couche application

    Args:
        region_id: ID de la région

    Returns:
        Réponse JSON avec les régions adjacentes
    """
    import asyncio

    try:
        logger.info(f"Récupération des régions adjacentes à la région {region_id}")

        # Récupérer les détails de la région pour obtenir les constellations
        region_details = await region_service.get_region_details(region_id)
        constellation_ids = region_details.get("constellations", [])

        if not constellation_ids:
            return {
                "region_id": region_id,
                "total": 0,
                "adjacent_regions": [],
            }

        # Récupérer les détails des constellations pour obtenir les systèmes
        constellation_details_list = await asyncio.gather(
            *[
                region_service.get_constellation_details(cid)
                for cid in constellation_ids
            ],
            return_exceptions=True,
        )

        # Collecter tous les systèmes de la région
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

        # Pour chaque système, récupérer ses détails et trouver les systèmes adjacents
        async def get_system_adjacent_regions(system_id: int) -> set:
            """Retourne les IDs des régions adjacentes via ce système"""
            try:
                system_details = await region_service.get_system_details(system_id)
                stargate_ids = system_details.get("stargates", [])

                if not stargate_ids:
                    return set()

                # Récupérer les détails de chaque stargate pour trouver le système de destination
                # Note: get_stargate_details n'est pas encore dans RegionService, utilisation directe temporaire
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
                        destination_system_id = stargate_data.get(
                            "destination", {}
                        ).get("system_id")
                        if destination_system_id:
                            # Récupérer les détails du système de destination pour obtenir sa constellation
                            try:
                                dest_system_details = await region_service.get_system_details(
                                    destination_system_id
                                )
                                dest_constellation_id = dest_system_details.get(
                                    "constellation_id"
                                )
                                if dest_constellation_id:
                                    # Récupérer la constellation pour obtenir la région
                                    dest_constellation = await region_service.get_constellation_details(
                                        dest_constellation_id
                                    )
                                    dest_region_id = dest_constellation.get("region_id")
                                    if dest_region_id and dest_region_id != region_id:
                                        adjacent_regions.add(dest_region_id)
                            except Exception as e:
                                logger.warning(
                                    f"Erreur lors de la récupération du système {destination_system_id}: {e}"
                                )
                                continue

                return adjacent_regions
            except Exception as e:
                logger.warning(
                    f"Erreur lors de la récupération du système {system_id}: {e}"
                )
                return set()

        # Récupérer les régions adjacentes pour tous les systèmes en parallèle
        results = await asyncio.gather(
            *[get_system_adjacent_regions(sid) for sid in systems_in_region],
            return_exceptions=True,
        )

        # Collecter toutes les régions adjacentes uniques
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

        # Récupérer les détails de chaque région adjacente en parallèle
        async def fetch_adjacent_region(adj_region_id: int) -> Optional[Dict[str, Any]]:
            try:
                region_data = await region_service.get_region_details(adj_region_id)
                return {
                    "region_id": adj_region_id,
                    "name": region_data.get("name", f"Région {adj_region_id}"),
                    "description": region_data.get("description", ""),
                }
            except Exception as e:
                logger.warning(
                    f"Erreur lors de la récupération de la région {adj_region_id}: {e}"
                )
                return None

        adjacent_regions_results = await asyncio.gather(
            *[fetch_adjacent_region(rid) for rid in adjacent_region_ids],
            return_exceptions=True,
        )

        # Filtrer les résultats None et les exceptions
        adjacent_regions = [
            r for r in adjacent_regions_results if isinstance(r, dict) and r is not None
        ]

        # Trier par nom
        adjacent_regions.sort(key=lambda x: x.get("name", ""))

        return {
            "region_id": region_id,
            "total": len(adjacent_regions),
            "adjacent_regions": adjacent_regions,
        }

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des régions adjacentes: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur lors de la récupération des régions adjacentes: {str(e)}",
        )


