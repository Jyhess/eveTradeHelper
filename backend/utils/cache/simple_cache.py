"""
Redis-based cache
"""

import json
from datetime import UTC, datetime, timedelta
from typing import Any


class SimpleCache:
    """Cache using Redis"""

    def __init__(self, redis_client: Any, default_expiry_hours: int):
        """
        Initialize Redis cache

        Args:
            redis_client: Redis client instance (required)
            default_expiry_hours: Default cache lifetime in hours
        """
        self.redis_client = redis_client
        self.default_expiry_hours = default_expiry_hours

    def is_valid(self, key: str, expiry_hours: int | None = None) -> bool:
        metadata_key = f"metadata:{key}"
        last_updated_str = self.redis_client.hget(metadata_key, "last_updated")

        if not last_updated_str:
            return False

        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=UTC)

            # Priority: 1) parameter expiry_hours, 2) metadata expiry_hours, 3) default_expiry_hours
            if expiry_hours is not None:
                hours = expiry_hours
            else:
                metadata_expiry_hours_str = self.redis_client.hget(metadata_key, "expiry_hours")
                if metadata_expiry_hours_str:
                    try:
                        hours = int(metadata_expiry_hours_str)
                    except (ValueError, TypeError):
                        hours = self.default_expiry_hours
                else:
                    hours = self.default_expiry_hours

            expiry_time = last_updated + timedelta(hours=hours)
            return datetime.now(UTC) < expiry_time
        except (ValueError, TypeError):
            return False

    def get(self, key: str, expiry_hours: int | None = None) -> list[dict[str, Any]] | None:
        if not self.is_valid(key, expiry_hours):
            return None

        try:
            cache_data_str = self.redis_client.get(f"cache:{key}")
            if cache_data_str:
                cache_data = json.loads(cache_data_str)
                return cache_data.get("items", [])
            return None
        except (json.JSONDecodeError, Exception):
            return None

    def set(
        self,
        key: str,
        items: list[dict[str, Any]],
        metadata: dict | None = None,
        expiry_hours: int | None = None,
    ):
        now = datetime.now(UTC)

        cache_data = {
            "key": key,
            "items": items,
            "cached_at": now.isoformat(),
        }

        try:
            cache_key = f"cache:{key}"
            self.redis_client.set(cache_key, json.dumps(cache_data, ensure_ascii=False))

            metadata_key = f"metadata:{key}"
            metadata_data = {
                "last_updated": now.isoformat(),
                "count": len(items),
                "metadata": json.dumps(metadata or {}, ensure_ascii=False),
                "expiry_hours": expiry_hours or self.default_expiry_hours,
            }
            self.redis_client.hset(metadata_key, mapping=metadata_data)
        except Exception as e:
            raise Exception(f"Error writing to Redis cache: {e}") from e

    def get_raw_value(self, key: str) -> str | None:
        return self.redis_client.get(key)

    def set_raw_value(self, key: str, value: str) -> None:
        try:
            self.redis_client.set(key, value)
        except Exception as e:
            raise Exception(f"Error writing to Redis cache: {e}") from e

    def delete_raw_value(self, key: str) -> None:
        try:
            self.redis_client.delete(key)
        except Exception as e:
            raise Exception(f"Error deleting from Redis cache: {e}") from e

    def clear(self, key: str | None = None):
        try:
            if key:
                cache_key = f"cache:{key}"
                metadata_key = f"metadata:{key}"
                # Also delete raw value if it exists (for ETag and response caching)
                self.redis_client.delete(cache_key, metadata_key, key)
            else:
                # Delete all cache keys
                for cache_key in self.redis_client.scan_iter(match="cache:*"):
                    self.redis_client.delete(cache_key)
                for metadata_key in self.redis_client.scan_iter(match="metadata:*"):
                    self.redis_client.delete(metadata_key)
                # Delete all raw values (ETag and response keys)
                for raw_key in self.redis_client.scan_iter(match="etag:*"):
                    self.redis_client.delete(raw_key)
                for raw_key in self.redis_client.scan_iter(match="response:*"):
                    self.redis_client.delete(raw_key)
        except Exception as e:
            raise Exception(f"Error deleting Redis cache: {e}") from e
