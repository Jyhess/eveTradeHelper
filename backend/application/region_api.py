"""
API pour la gestion des régions
Endpoints FastAPI pour les régions (asynchrone)
"""

import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from domain.region_service import RegionService

logger = logging.getLogger(__name__)
router = APIRouter()


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
        system_data = await region_service.repository.get_system_details(system_id)

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
        constellation_data = await region_service.repository.get_constellation_details(
            constellation_id
        )
        region_id = constellation_data.get("region_id")

        # Récupérer les détails de la région
        region_data = None
        if region_id:
            region_data = await region_service.repository.get_region_details(region_id)

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
