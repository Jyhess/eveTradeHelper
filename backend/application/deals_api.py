"""
API pour la recherche de bonnes affaires
Endpoints FastAPI pour les deals (version asynchrone)
"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from domain.deals_service import DealsService

logger = logging.getLogger(__name__)
router = APIRouter()

# Variable globale pour stocker le service (sera initialisé dans app.py)
_deals_service: Optional[DealsService] = None


def get_deals_service() -> DealsService:
    """Dependency pour obtenir le service de deals"""
    if _deals_service is None:
        raise HTTPException(status_code=503, detail="Service non initialisé")
    return _deals_service


def set_deals_service(service: DealsService):
    """Initialise le service de deals pour les endpoints"""
    global _deals_service
    _deals_service = service


@router.get("/api/v1/markets/deals")
async def get_market_deals(
    region_id: int,
    group_id: int,
    min_profit_isk: float = 100000.0,
    max_transport_volume: Optional[float] = None,
    deals_service: DealsService = Depends(get_deals_service),
):
    """
    Trouve les bonnes affaires dans un groupe de marché pour une région
    Parcourt tous les types d'items du groupe (y compris les sous-groupes) et calcule
    le bénéfice potentiel entre les meilleurs ordres d'achat et de vente

    Args:
        region_id: ID de la région
        group_id: ID du groupe de marché
        min_profit_isk: Seuil de bénéfice minimum en ISK (défaut: 100000.0)
        max_transport_volume: Volume de transport maximum autorisé en m³ (None = illimité)

    Returns:
        Réponse JSON avec les items permettant un bénéfice supérieur au seuil
    """
    try:
        result = await deals_service.find_market_deals(
            region_id, group_id, min_profit_isk, max_transport_volume
        )
        return result

    except Exception as e:
        logger.error(f"Erreur lors de la recherche de bonnes affaires: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Erreur de connexion à l'API ESI: {str(e)}",
        )
