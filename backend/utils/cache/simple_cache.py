"""
Redis-based cache
"""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class SimpleCache:
    """Cache using Redis"""

    def __init__(
        self,
        expiry_hours: int,
        redis_url: str | None = None,
        redis_host: str | None = None,
        redis_port: int = 6379,
        redis_db: int = 0,
    ):
        """
        Initialize Redis cache

        Args:
            expiry_hours: Cache lifetime in hours
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
            redis_host: Redis host (ignored if redis_url is provided)
            redis_port: Redis port (ignored if redis_url is provided)
            redis_db: Redis database (ignored if redis_url is provided)

        Raises:
            ImportError: If redis-py is not installed
            ConnectionError: If connection to Redis fails
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis is required but redis-py is not installed. "
                "Install it with: pip install redis"
            )

        self.expiry_hours = expiry_hours

        # Check that at least one Redis configuration is provided
        if not redis_url and not redis_host:
            raise ValueError(
                "Redis is required but no configuration is provided. "
                "Please provide REDIS_URL or REDIS_HOST in environment variables."
            )

        try:
            if redis_url:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                )
            # Test connection
            self.redis_client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(
                f"❌ Unable to connect to Redis.\n"
                f"   Check that Redis is started with: docker-compose up -d redis\n"
                f"   Or start the Redis service in Docker: docker-compose up redis\n"
                f"   Error details: {e}"
            ) from e
        except Exception as e:
            raise ConnectionError(
                f"❌ Error connecting to Redis.\n"
                f"   Check that Redis is started with: docker-compose up -d redis\n"
                f"   Error details: {e}"
            ) from e

    def is_valid(self, key: str) -> bool:
        """
        Checks if the cache for a key is still valid

        Args:
            key: Cache key

        Returns:
            True if cache is valid, False otherwise
        """
        metadata_key = f"metadata:{key}"
        last_updated_str = self.redis_client.hget(metadata_key, "last_updated")

        if not last_updated_str:
            return False

        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            # Ensure the date is timezone-aware
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

        try:
            cache_data_str = self.redis_client.get(f"cache:{key}")
            if cache_data_str:
                cache_data = json.loads(cache_data_str)
                return cache_data.get("items", [])
            return None
        except (json.JSONDecodeError, Exception):
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

        # Save data
        cache_data = {
            "key": key,
            "items": items,
            "cached_at": now.isoformat(),
        }

        try:
            # Save data to Redis
            cache_key = f"cache:{key}"
            self.redis_client.set(cache_key, json.dumps(cache_data, ensure_ascii=False))

            # Update metadata
            metadata_key = f"metadata:{key}"
            metadata_data = {
                "last_updated": now.isoformat(),
                "count": len(items),
                "metadata": json.dumps(metadata or {}, ensure_ascii=False),
            }
            self.redis_client.hset(metadata_key, mapping=metadata_data)
        except Exception as e:
            raise Exception(f"Error writing to Redis cache: {e}") from e

    def clear(self, key: str | None = None):
        """
        Clears cache for a specific key or all cache

        Args:
            key: Key to delete, or None to delete all
        """
        try:
            if key:
                cache_key = f"cache:{key}"
                metadata_key = f"metadata:{key}"
                self.redis_client.delete(cache_key, metadata_key)
            else:
                # Delete all cache keys
                for cache_key in self.redis_client.scan_iter(match="cache:*"):
                    self.redis_client.delete(cache_key)
                for metadata_key in self.redis_client.scan_iter(match="metadata:*"):
                    self.redis_client.delete(metadata_key)
        except Exception as e:
            raise Exception(f"Error deleting Redis cache: {e}") from e
