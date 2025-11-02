"""
Module Application - Cas d'usage et endpoints API
"""

from .region_api import router as region_router, set_region_service
from .health_api import health_router
from .deals_api import router as deals_router, set_deals_service

__all__ = [
    "region_router",
    "set_region_service",
    "health_router",
    "deals_router",
    "set_deals_service",
]