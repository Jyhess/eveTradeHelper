"""
Module cache - Gestion du cache Redis et décorateurs associés
"""

from .cache_factory import create_cache
from .decorator import cached
from .manager import CacheManager
from .simple_cache import SimpleCache

__all__ = [
    "SimpleCache",
    "create_cache",
    "CacheManager",
    "cached",
]
