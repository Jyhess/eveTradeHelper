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

    def is_valid(self, key: str) -> bool:
        """
        Checks if the cache for a key is still valid

        Args:
            key: Cache key

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
            expiry_time = last_updated + timedelta(hours=self.expiry_hours)
            return datetime.now(UTC) < expiry_time
        except (ValueError, TypeError):
            return False

    def get(self, key: str) -> list[dict[str, Any]] | None:
        """
        Retrieves data from cache

        Args:
            key: Cache key

        Returns:
            Cached data or None if not available
        """
        if not self.is_valid(key):
            return None

        cache_key = f"cache:{key}"
        cache_data = self._cache_data.get(cache_key)
        if cache_data:
            return cache_data.get("items", [])
        return None

    def set(self, key: str, items: list[dict[str, Any]], metadata: dict | None = None):
        """
        Saves data to cache

        Args:
            key: Cache key
            items: List of items to cache
            metadata: Optional metadata (e.g., region_ids)
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
        else:
            self._cache_data.clear()
            self._metadata.clear()
