"""
Module Application - Cas d'usage et endpoints API
"""

from .region_api import router as region_router, set_region_service
from .health_api import health_router

__all__ = [
    "region_router",
    "set_region_service",
    "health_router",
]