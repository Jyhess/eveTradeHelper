"""
API pour la gestion des régions
Endpoints FastAPI pour les régions (asynchrone)
"""

import os
import logging
from cachetools import TTLCache
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from domain.region_service import RegionService
from application.utils import cached_async

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache LRU avec TTL pour les catégories de marché (en mémoire)
# Taille max: 1 entrée, TTL: 1 heure (3600 secondes)
_market_categories_cache = TTLCache(maxsize=1, ttl=3600)


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


@router.get("/api/v1/markets/categories")
async def get_market_categories(
    region_service: RegionService = Depends(get_region_service),
):
    """
    Récupère la liste des catégories du marché
    Utilise un cache LRU avec TTL (1 heure) en mémoire pour améliorer les performances

    Returns:
        Réponse JSON avec les catégories du marché
    """
    # Vérifier le cache LRU (clé fixe car pas de paramètres variables)
    cache_key = "market_categories"
    if cache_key in _market_categories_cache:
        logger.info("Récupération des catégories depuis le cache LRU")
        return _market_categories_cache[cache_key]

    try:
        logger.info("Récupération des catégories du marché (non caché)")

        # Récupérer la liste des groupes de marché
        group_ids = await region_service.repository.get_market_groups_list()

        # Récupérer les détails de chaque groupe en parallèle
        async def fetch_group(group_id: int):
            try:
                group_data = await region_service.repository.get_market_group_details(
                    group_id
                )
                return {
                    "group_id": group_id,
                    "name": group_data.get("name", "Unknown"),
                    "description": group_data.get("description", ""),
                    "parent_group_id": group_data.get("parent_group_id"),
                    "types": group_data.get("types", []),
                }
            except Exception as e:
                logger.warning(
                    f"Erreur lors de la récupération du groupe {group_id}: {e}"
                )
                return None

        import asyncio

        results = await asyncio.gather(*[fetch_group(gid) for gid in group_ids])

        # Filtrer les résultats None et trier par nom
        categories = sorted(
            [c for c in results if c is not None], key=lambda x: x.get("name", "")
        )

        result = {
            "total": len(categories),
            "categories": categories,
        }

        # Mettre en cache LRU
        _market_categories_cache[cache_key] = result

        return result

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des catégories: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion à l'API ESI: {str(e)}",
        )


@router.get("/api/v1/universe/types/{type_id}")
async def get_item_type(
    type_id: int,
    region_service: RegionService = Depends(get_region_service),
):
    """
    Récupère les détails d'un type d'item
    Le cache est géré automatiquement par la couche infrastructure (EveAPIClient)

    Args:
        type_id: ID du type d'item

    Returns:
        Réponse JSON avec les détails du type d'item
    """
    try:
        logger.info(f"Récupération des détails du type {type_id}")
        type_data = await region_service.repository.get_item_type(type_id)

        return type_data

    except Exception as e:
        logger.error(f"Erreur lors de la récupération du type: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion à l'API ESI: {str(e)}",
        )


@router.get("/api/v1/markets/regions/{region_id}/orders")
async def get_market_orders(
    region_id: int,
    type_id: int = None,
    region_service: RegionService = Depends(get_region_service),
):
    """
    Récupère les ordres de marché pour une région, optionnellement filtrés par type
    Le cache est géré automatiquement par la couche infrastructure (EveAPIClient)

    Args:
        region_id: ID de la région
        type_id: Optionnel, ID du type d'item pour filtrer les ordres

    Returns:
        Réponse JSON avec les ordres de marché
    """
    try:
        logger.info(
            f"Récupération des ordres de marché pour la région {region_id}"
            + (f" et le type {type_id}" if type_id else "")
        )

        orders = await region_service.repository.get_market_orders(region_id, type_id)

        # Séparer les ordres d'achat et de vente
        buy_orders = [o for o in orders if o.get("is_buy_order", False)]
        sell_orders = [o for o in orders if not o.get("is_buy_order", False)]

        # Trier par prix (meilleur prix en premier)
        buy_orders.sort(key=lambda x: x.get("price", 0), reverse=True)
        sell_orders.sort(key=lambda x: x.get("price", 0))

        return {
            "region_id": region_id,
            "type_id": type_id,
            "total": len(orders),
            "buy_orders": buy_orders[:50],  # Limiter à 50 meilleurs ordres
            "sell_orders": sell_orders[:50],
        }

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des ordres: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion à l'API ESI: {str(e)}",
        )
