"""
Module cache - Gestion du cache Redis et décorateurs associés
"""

from .simple_cache import SimpleCache
from .factory import create_cache
from .manager import CacheManager
from .decorator import cached

__all__ = [
    "SimpleCache",
    "create_cache",
    "CacheManager",
    "cached",
]
