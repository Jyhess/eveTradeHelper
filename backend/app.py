"""
Main FastAPI application
Configuration and initialization following Clean Architecture (async version)
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

from application import AppFactory
from domain import Services
from eve import make_eve_repository
from repositories.local_data import LocalDataRepository
from utils.cache import create_cache

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manages application lifecycle
    Initializes and cleans up resources
    """
    logger.info("Initializing application...")

    cache = create_cache()

    local_data_repository = LocalDataRepository(cache)

    # Infrastructure Layer: Repository
    eve_repository = make_eve_repository(cache, local_data_repository)
    services = Services(eve_repository, local_data_repository)
    AppFactory.set_services(app, services)

    logger.info("Application initialized")

    yield

    # Cleanup
    logger.info("Closing application...")
    await eve_repository.close()
    logger.info("Application closed")


app = AppFactory.make_app(lifespan)

if __name__ == "__main__":
    import uvicorn

    # Read FLASK_DEBUG from environment variables for compatibility
    # FastAPI uses RELOAD instead
    debug_mode = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
    reload_mode = os.getenv("RELOAD", str(debug_mode)).lower() in ("1", "true", "yes")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=5001,
        reload=reload_mode,
        log_level="info",
    )
