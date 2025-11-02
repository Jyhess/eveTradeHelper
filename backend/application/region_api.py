"""
API pour la gestion des régions
Endpoints FastAPI pour les régions (asynchrone)
"""

import os
import logging
from cachetools import TTLCache
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any, List
from domain.region_service import RegionService
from application.utils import cached_async

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache LRU avec TTL pour les catégories de marché (en mémoire)
# Taille max: 1 entrée, TTL: 1 heure (3600 secondes)
_market_categories_cache = TTLCache(maxsize=1, ttl=3600)

# Cache LRU avec TTL pour les régions adjacentes (en mémoire)
# Taille max: 100 régions, TTL: 24 heures (86400 secondes)
# Les régions adjacentes changent rarement, donc un TTL long est approprié
_adjacent_regions_cache = TTLCache(maxsize=100, ttl=86400)


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
        region_details = await region_service.repository.get_region_details(region_id)
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
                region_service.repository.get_constellation_details(cid)
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
                system_details = await region_service.repository.get_system_details(
                    system_id
                )
                stargate_ids = system_details.get("stargates", [])

                if not stargate_ids:
                    return set()

                # Récupérer les détails de chaque stargate pour trouver le système de destination
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
                                dest_system_details = (
                                    await region_service.repository.get_system_details(
                                        destination_system_id
                                    )
                                )
                                dest_constellation_id = dest_system_details.get(
                                    "constellation_id"
                                )
                                if dest_constellation_id:
                                    # Récupérer la constellation pour obtenir la région
                                    dest_constellation = await region_service.repository.get_constellation_details(
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
                region_data = await region_service.repository.get_region_details(
                    adj_region_id
                )
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
    Enrichit les ordres avec les noms des systèmes et stations

    Args:
        region_id: ID de la région
        type_id: Optionnel, ID du type d'item pour filtrer les ordres

    Returns:
        Réponse JSON avec les ordres de marché enrichis
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

        # Limiter à 50 meilleurs ordres pour éviter trop d'appels API
        buy_orders = buy_orders[:50]
        sell_orders = sell_orders[:50]

        # Enrichir les ordres avec les noms des systèmes et stations
        import asyncio

        async def enrich_order(order: Dict[str, Any]) -> Dict[str, Any]:
            """Enrichit un ordre avec les noms du système et de la station"""
            location_id = order.get("location_id")
            if not location_id:
                return order

            enriched_order = order.copy()

            # Les IDs >= 60000000 sont des stations, sinon ce sont des systèmes
            if location_id >= 60000000:
                # C'est une station
                try:
                    station_data = await region_service.repository.get_station_details(
                        location_id
                    )
                    enriched_order["station_name"] = station_data.get(
                        "name", "Unknown Station"
                    )
                    enriched_order["station_id"] = location_id

                    # Récupérer aussi le système de la station
                    system_id = station_data.get("system_id")
                    if system_id:
                        system_data = (
                            await region_service.repository.get_system_details(
                                system_id
                            )
                        )
                        enriched_order["system_name"] = system_data.get(
                            "name", "Unknown System"
                        )
                        enriched_order["system_id"] = system_id
                except Exception as e:
                    logger.warning(
                        f"Erreur lors de la récupération de la station {location_id}: {e}"
                    )
                    enriched_order["station_name"] = f"Station {location_id}"
                    enriched_order["station_id"] = location_id
            else:
                # C'est un système
                try:
                    system_data = await region_service.repository.get_system_details(
                        location_id
                    )
                    enriched_order["system_name"] = system_data.get(
                        "name", "Unknown System"
                    )
                    enriched_order["system_id"] = location_id
                except Exception as e:
                    logger.warning(
                        f"Erreur lors de la récupération du système {location_id}: {e}"
                    )
                    enriched_order["system_name"] = f"Système {location_id}"
                    enriched_order["system_id"] = location_id

            return enriched_order

        # Enrichir tous les ordres en parallèle
        buy_orders_enriched = await asyncio.gather(
            *[enrich_order(order) for order in buy_orders], return_exceptions=True
        )
        sell_orders_enriched = await asyncio.gather(
            *[enrich_order(order) for order in sell_orders], return_exceptions=True
        )

        # Filtrer les erreurs (garder les ordres même si l'enrichissement a échoué)
        buy_orders_final = [
            order if not isinstance(order, Exception) else buy_orders[i]
            for i, order in enumerate(buy_orders_enriched)
        ]
        sell_orders_final = [
            order if not isinstance(order, Exception) else sell_orders[i]
            for i, order in enumerate(sell_orders_enriched)
        ]

        return {
            "region_id": region_id,
            "type_id": type_id,
            "total": len(orders),
            "buy_orders": buy_orders_final,
            "sell_orders": sell_orders_final,
        }

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des ordres: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion à l'API ESI: {str(e)}",
        )
