"""
Application utilities
Reusable decorators and utility functions
"""

import logging
from collections.abc import Callable
from functools import wraps

from cachetools import TTLCache
from cachetools.keys import hashkey

logger = logging.getLogger(__name__)


def cached_async(cache: TTLCache, exclude_types: tuple = ()):
    """
    Standard decorator to cache async function results
    Uses cachetools with hashkey for cache keys

    Args:
        cache: TTLCache instance to use
        exclude_types: Types to exclude from argument hashing (e.g., RegionService for FastAPI Depends)

    Usage:
        @cached_async(_my_cache, exclude_types=(RegionService,))
        async def my_function(region_service: RegionService = Depends(...)):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Create a cache key based on arguments
            # Exclude specified types (generally FastAPI dependencies)
            cache_args = tuple(a for a in args if not isinstance(a, exclude_types))
            cache_kwargs = {k: v for k, v in kwargs.items() if not isinstance(v, exclude_types)}
            key = hashkey(*cache_args, **cache_kwargs)

            # Check cache
            if key in cache:
                logger.info(f"Cache hit for {func.__name__}")
                return cache[key]

            # Execute function
            logger.info(f"Cache miss for {func.__name__}, executing...")
            result = await func(*args, **kwargs)

            # Cache result
            cache[key] = result
            return result

        return wrapper

    return decorator
