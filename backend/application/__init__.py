"""
Module Application - Cas d'usage et endpoints API
"""

from .region_api import RegionAPI
from .health_api import HealthAPI

__all__ = [
    "RegionAPI",
    "HealthAPI",
]

