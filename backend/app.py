"""
Application FastAPI principale
Configuration et initialisation selon Clean Architecture (version asynchrone)
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from application import AppFactory
from domain import Services
from eve import make_eve_repository
from utils.cache import create_cache

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gère le cycle de vie de l'application
    Initialise et nettoie les ressources
    """
    logger.info("Initialisation de l'application...")

    create_cache()

    # Infrastructure Layer : Repository
    eve_repository = make_eve_repository()
    services = Services(eve_repository)
    AppFactory.set_services(app, services)

    logger.info("Application initialisée")

    yield

    # Nettoyage
    logger.info("Fermeture de l'application...")
    await eve_repository.close()
    logger.info("Application fermée")


app = AppFactory.make_app(lifespan)

if __name__ == "__main__":
    import uvicorn

    # Lecture de FLASK_DEBUG depuis les variables d'environnement pour compatibilité
    # FastAPI utilise plutôt RELOAD
    debug_mode = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    reload_mode = os.getenv("RELOAD", str(debug_mode)).lower() in ("1", "true", "yes")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5001,
        reload=reload_mode,
        log_level="info",
    )
