"""
Application FastAPI principale
Configuration et initialisation selon Clean Architecture (version asynchrone)
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from eve import EveAPIClient
from eve.repository import EveRepositoryImpl
from utils.cache import create_cache, CacheManager
from domain.region_service import RegionService
from domain.deals_service import DealsService
from domain.market_service import MarketService
from application.region_api import router as region_router, set_region_service
from application.health_api import health_router
from application.deals_api import router as deals_router, set_deals_service
from application.market_api import router as market_router, set_market_service

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le cycle de vie de l'application
    Initialise et nettoie les ressources
    """
    # Démarrage
    logger.info("Initialisation de l'application...")

    # Configuration du cache Redis via factory
    cache = create_cache()

    # Initialiser le gestionnaire de cache statique
    CacheManager.initialize(cache)

    # Infrastructure Layer : Repository
    api_client = EveAPIClient()
    eve_repository = EveRepositoryImpl(api_client)

    # Domain Layer : Services
    region_service = RegionService(eve_repository)
    deals_service = DealsService(eve_repository)
    market_service = MarketService(eve_repository)

    # Initialiser les services dans les modules API
    set_region_service(region_service)
    set_deals_service(deals_service)
    set_market_service(market_service)

    # Stocker les instances dans l'état de l'application
    app.state.api_client = api_client
    app.state.region_service = region_service

    logger.info("Application initialisée")

    yield

    # Nettoyage
    logger.info("Fermeture de l'application...")
    await api_client.close()
    logger.info("Application fermée")


app = FastAPI(
    title="Eve Trade Helper API",
    description="API pour l'application Eve Trade Helper",
    version="1.0.0",
    lifespan=lifespan,
)

# Configuration CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifier les origines autorisées
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Enregistrer les routers (les routes sont déjà définies avec les décorateurs)
app.include_router(region_router)
app.include_router(health_router)
app.include_router(deals_router)
app.include_router(market_router)


if __name__ == "__main__":
    import uvicorn

    # Lecture de FLASK_DEBUG depuis les variables d'environnement pour compatibilité
    # FastAPI utilise plutôt RELOAD
    debug_mode = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    reload_mode = os.getenv("RELOAD", str(debug_mode)).lower() in ("1", "true", "yes")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5000,
        reload=reload_mode,
        log_level="info",
    )
