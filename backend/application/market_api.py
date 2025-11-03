"""
API pour la gestion des marchés et des types d'items
Endpoints FastAPI pour les marchés (asynchrone)
"""

import logging
from cachetools import TTLCache
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from domain.market_service import MarketService

logger = logging.getLogger(__name__)
router = APIRouter()

# Cache LRU avec TTL pour les catégories de marché (en mémoire)
# Taille max: 1 entrée, TTL: 1 heure (3600 secondes)
_market_categories_cache = TTLCache(maxsize=1, ttl=3600)


# Variable globale pour stocker le service (sera initialisé dans app.py)
_market_service: Optional[MarketService] = None


def get_market_service() -> MarketService:
    """Dependency pour obtenir le service de marché"""
    if _market_service is None:
        raise HTTPException(status_code=503, detail="Service non initialisé")
    return _market_service


def set_market_service(service: MarketService):
    """Initialise le service de marché"""
    global _market_service
    _market_service = service


@router.get("/api/v1/markets/categories")
async def get_market_categories(
    market_service: MarketService = Depends(get_market_service),
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

        categories = await market_service.get_market_categories()

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
    market_service: MarketService = Depends(get_market_service),
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
        type_data = await market_service.repository.get_item_type(type_id)

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
    type_id: Optional[int] = None,
    market_service: MarketService = Depends(get_market_service),
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

        enriched_orders = await market_service.get_enriched_market_orders(
            region_id, type_id
        )

        return {
            "region_id": region_id,
            "type_id": type_id,
            **enriched_orders,
        }

    except Exception as e:
        logger.error(f"Erreur lors de la récupération des ordres: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion à l'API ESI: {str(e)}",
        )
