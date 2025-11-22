"""
In-memory cache for unit tests
Simulates SimpleCache behavior without Redis connection
"""

from datetime import UTC, datetime, timedelta
from typing import Any


class FakeCache:
    """In-memory cache for unit tests, simulating SimpleCache behavior"""

    def __init__(
        self,
        expiry_hours: int,
        redis_url: str | None = None,
        redis_host: str | None = None,
        redis_port: int = 6379,
        redis_db: int = 0,
    ):
        """
        Initialize the in-memory fake cache

        Args:
            expiry_hours: Cache lifetime in hours
            redis_url: Ignored (compatibility with SimpleCache)
            redis_host: Ignored (compatibility with SimpleCache)
            redis_port: Ignored (compatibility with SimpleCache)
            redis_db: Ignored (compatibility with SimpleCache)
        """
        self.expiry_hours = expiry_hours
        self._cache_data: dict[str, dict[str, Any]] = {}
        self._metadata: dict[str, dict[str, Any]] = {}
        self._raw_values: dict[str, str] = {}

    def is_valid(self, key: str, expiry_hours: int | None = None) -> bool:
        """
        Checks if the cache for a key is still valid

        Args:
            key: Cache key
            expiry_hours: Optional expiry hours override (uses self.expiry_hours if None)

        Returns:
            True if cache is valid, False otherwise
        """
        metadata_key = f"metadata:{key}"
        metadata = self._metadata.get(metadata_key)

        if not metadata:
            return False

        last_updated_str = metadata.get("last_updated")
        if not last_updated_str:
            return False

        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=UTC)
            hours = expiry_hours if expiry_hours is not None else self.expiry_hours
            expiry_time = last_updated + timedelta(hours=hours)
            return datetime.now(UTC) < expiry_time
        except (ValueError, TypeError):
            return False

    def get(self, key: str, expiry_hours: int | None = None) -> list[dict[str, Any]] | None:
        """
        Retrieves data from cache

        Args:
            key: Cache key
            expiry_hours: Optional expiry hours override (uses self.expiry_hours if None)

        Returns:
            Cached data or None if not available
        """
        if not self.is_valid(key, expiry_hours):
            return None

        cache_key = f"cache:{key}"
        cache_data = self._cache_data.get(cache_key)
        if cache_data:
            return cache_data.get("items", [])
        return None

    def set(
        self,
        key: str,
        items: list[dict[str, Any]],
        metadata: dict | None = None,
        expiry_hours: int | None = None,
    ):
        """
        Saves data to cache

        Args:
            key: Cache key
            items: List of items to cache
            metadata: Optional metadata (e.g., region_ids)
            expiry_hours: Optional expiry hours override (uses self.expiry_hours if None)
        """
        now = datetime.now(UTC)

        cache_key = f"cache:{key}"
        self._cache_data[cache_key] = {
            "key": key,
            "items": items,
            "cached_at": now.isoformat(),
        }

        metadata_key = f"metadata:{key}"
        self._metadata[metadata_key] = {
            "last_updated": now.isoformat(),
            "count": len(items),
            "metadata": metadata or {},
        }

    def get_raw_value(self, key: str) -> str | None:
        """
        Retrieves a raw string value from cache (without expiration check)

        Args:
            key: Cache key

        Returns:
            Cached value as string or None if not found
        """
        return self._raw_values.get(key)

    def set_raw_value(self, key: str, value: str) -> None:
        """
        Stores a raw string value in cache (without expiration)

        Args:
            key: Cache key
            value: Value to store
        """
        self._raw_values[key] = value

    def delete_raw_value(self, key: str) -> None:
        """
        Deletes a raw string value from cache

        Args:
            key: Cache key to delete
        """
        self._raw_values.pop(key, None)

    def clear(self, key: str | None = None):
        """
        Clears cache for a specific key or all cache

        Args:
            key: Key to delete, or None to delete all
        """
        if key:
            cache_key = f"cache:{key}"
            metadata_key = f"metadata:{key}"
            self._cache_data.pop(cache_key, None)
            self._metadata.pop(metadata_key, None)
            self._raw_values.pop(key, None)
        else:
            self._cache_data.clear()
            self._metadata.clear()
            self._raw_values.clear()
