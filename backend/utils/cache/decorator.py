"""
Decorator to automatically cache method results
Supports synchronous and asynchronous functions
"""

import functools
import hashlib
import inspect
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from .manager import CacheManager
from .simple_cache import SimpleCache

if TYPE_CHECKING:
    from .fake_cache import FakeCache
else:
    try:
        from .fake_cache import FakeCache
    except ImportError:
        FakeCache = None  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)


def _generate_cache_key(func_name: str, prefix: str | None, args: tuple, kwargs: dict) -> str:
    """
    Generates a unique cache key based on the function name and its parameters

    Args:
        func_name: Function name
        prefix: Optional prefix for the key
        args: Positional arguments
        kwargs: Named arguments

    Returns:
        Hashed cache key
    """
    prefix = prefix or func_name
    cache_key_parts = [prefix]

    # Add positional arguments
    if args:
        args_str = str(args) if len(args) > 0 else ""
        cache_key_parts.append(args_str)

    # Add named arguments (sorted to ensure consistent order)
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        cache_key_parts.append(str(sorted_kwargs))

    # Create a hashed cache key to avoid overly long names
    cache_key_raw = "_".join(str(part) for part in cache_key_parts)
    cache_key_hash = hashlib.md5(cache_key_raw.encode()).hexdigest()
    return f"{prefix}_{cache_key_hash}"


def _get_cache_instance(expiry_hours: int | None) -> SimpleCache | Any | None:
    """
    Retrieves the cache instance, with custom expiry handling

    Args:
        expiry_hours: Custom cache lifetime in hours

    Returns:
        Cache instance or None if cache is not initialized
    """
    if not CacheManager.is_initialized():
        return None

    cache_instance = CacheManager.get_instance()
    if cache_instance is None:
        return None

    # At this point, cache_instance cannot be None (checked by is_initialized)
    # Use cast to help the type checker
    cache_instance = cast(SimpleCache | Any, cache_instance)

    # Create a temporary instance if expiry_hours is different
    if expiry_hours and expiry_hours != cache_instance.expiry_hours:
        # Detect cache type and create appropriate temporary instance
        if isinstance(cache_instance, SimpleCache):
            temp_cache = SimpleCache.__new__(SimpleCache)
            temp_cache.expiry_hours = expiry_hours
            temp_cache.redis_client = cache_instance.redis_client
            return temp_cache
        elif FakeCache is not None and isinstance(cache_instance, FakeCache):
            # For FakeCache, create a new instance that shares the same storage
            temp_cache = FakeCache.__new__(FakeCache)  # type: ignore[assignment]
            temp_cache.expiry_hours = expiry_hours
            temp_cache._cache_data = cache_instance._cache_data  # type: ignore[attr-defined]
            temp_cache._metadata = cache_instance._metadata  # type: ignore[attr-defined]
            return temp_cache  # type: ignore[return-value]

    return cache_instance


def _get_cached_result(cache_instance: SimpleCache | Any, cache_key: str) -> Any | None:
    """
    Retrieves the result from cache if available and valid

    Args:
        cache_instance: Cache instance
        cache_key: Cache key

    Returns:
        Cached result or None if not available
    """
    if not cache_instance.is_valid(cache_key):
        return None

    cached_result = cache_instance.get(cache_key)
    if cached_result is None:
        return None

    # Cache stores a list, retrieve the first element if necessary
    if isinstance(cached_result, list):
        # If the list has multiple elements or is empty, it's an original list
        if len(cached_result) != 1:
            return cached_result
        # If the list has a single element, check if it's a normalized wrapper
        single_item = cached_result[0]
        if isinstance(single_item, dict) and "_type" in single_item:
            # It's a normalized wrapper with type metadata
            original_type = single_item["_type"]
            value = single_item["value"]

            # Check if it's an original value (list or dict) to preserve
            if single_item.get("_original", False):
                if original_type == "list":
                    # Original list with a single element
                    return value
                elif original_type == "dict":
                    # Original dict (even if it contains "value")
                    return value

            # Restore original type for normalized wrappers
            if original_type == "tuple":
                return tuple(value)
            elif original_type == "set":
                return set(value)
            elif original_type == "int":
                return int(value)
            elif original_type == "float":
                return float(value)
            elif original_type == "str":
                return str(value)
            elif original_type == "bool":
                return bool(value)
            elif original_type == "NoneType" or value is None:
                return None
            else:
                # Unhandled type, return value as is
                return value
        else:
            # It's a unique dict that was the original result
            return single_item

    return cached_result


def _normalize_result_for_cache(result: Any) -> list:
    """
    Normalizes the result for cache storage (always store as list)

    Args:
        result: Result to normalize

    Returns:
        Normalized list for cache with type metadata
    """
    if isinstance(result, list):
        # List: if single element, mark as original list
        if len(result) == 1:
            return [{"_type": "list", "_original": True, "value": result}]
        # List with multiple elements or empty: return as is
        return result
    elif isinstance(result, tuple):
        # Tuple: store with type metadata to restore it
        return [{"_type": "tuple", "value": list(result)}]
    elif isinstance(result, dict):
        # Dict: return in a list with marker to distinguish from wrappers
        return [{"_type": "dict", "_original": True, "value": result}]
    elif isinstance(result, set):
        # Set: store as list with type metadata
        return [{"_type": "set", "value": list(result)}]
    else:
        # Simple types (int, str, float, bool, None): wrap with type metadata
        return [{"_type": type(result).__name__, "value": result}]


def _save_to_cache(cache_instance: SimpleCache | Any, cache_key: str, result: Any) -> None:
    """
    Saves the result to cache

    Args:
        cache_instance: Cache instance
        cache_key: Cache key
        result: Result to cache
    """
    cache_data = _normalize_result_for_cache(result)
    try:
        cache_instance.set(cache_key, cache_data)
    except Exception as e:
        logger.warning(f"Error caching: {e}")


def _try_get_from_cache(
    func_name: str,
    cache_key_prefix: str | None,
    expiry_hours: int | None,
    args: tuple,
    kwargs: dict,
) -> tuple[SimpleCache | None, str | None, Any | None]:
    """
    Tries to retrieve the result from cache

    Args:
        func_name: Function name
        cache_key_prefix: Optional prefix for the key
        expiry_hours: Custom cache lifetime
        args: Positional arguments
        kwargs: Named arguments

    Returns:
        Tuple (cache_instance, cache_key, cached_result)
        If cache is not available, returns (None, None, None)
        If result is not cached, returns (cache_instance, cache_key, None)
    """
    cache_instance = _get_cache_instance(expiry_hours)
    if cache_instance is None:
        return None, None, None

    cache_key = _generate_cache_key(func_name, cache_key_prefix, args, kwargs)
    cached_result = _get_cached_result(cache_instance, cache_key)

    return cache_instance, cache_key, cached_result


def cached(cache_key_prefix: str | None = None, expiry_hours: int | None = None):
    """
    Decorator to automatically cache method results
    Supports synchronous and asynchronous functions

    Uses CacheManager to access the static cache

    Args:
        cache_key_prefix: Prefix for cache key (uses function name if None)
        expiry_hours: Cache lifetime in hours (uses static cache's if None)

    Usage:
        @cached()
        def my_method(self, param1, param2):
            # ...

        @cached()
        async def my_async_method(self, param1, param2):
            # ...
    """

    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                cache_instance, cache_key, cached_result = _try_get_from_cache(
                    func.__name__, cache_key_prefix, expiry_hours, args, kwargs
                )

                if cached_result is not None:
                    return cached_result

                if cache_instance is None:
                    return await func(self, *args, **kwargs)

                # Execute the method and cache the result
                result = await func(self, *args, **kwargs)
                _save_to_cache(cache_instance, cache_key, result)
                return result

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(self, *args, **kwargs):
                cache_instance, cache_key, cached_result = _try_get_from_cache(
                    func.__name__, cache_key_prefix, expiry_hours, args, kwargs
                )

                if cached_result is not None:
                    return cached_result

                if cache_instance is None:
                    return func(self, *args, **kwargs)

                # Execute the method and cache the result
                result = func(self, *args, **kwargs)
                _save_to_cache(cache_instance, cache_key, result)
                return result

            return sync_wrapper

    return decorator
