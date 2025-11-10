"""
ETag cache manager for EVE ESI API responses
Handles caching of ETags and responses for 304 Not Modified support
"""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class EtagCache:
    """Manages ETag and response caching for API requests"""

    def __init__(self, cache: Any):
        """
        Initialize the ETag cache manager

        Args:
            cache: Cache instance (SimpleCache) for ETag and response caching
        """
        if cache is None:
            raise ValueError("Cache instance is required for EtagCache")
        if not hasattr(cache, "get_raw_value") or not hasattr(cache, "set_raw_value"):
            raise ValueError("Cache instance must have get_raw_value and set_raw_value methods")
        self.cache = cache

    def get_etag(self, url: str) -> str | None:
        """
        Gets ETag from cache

        Args:
            url: Request URL

        Returns:
            ETag value or None if not found
        """
        etag_key = f"etag:{url}"
        etag = self.cache.get_raw_value(etag_key)
        return etag if etag else None

    def set_etag(self, url: str, etag: str) -> None:
        """
        Stores ETag in cache

        Args:
            url: Request URL
            etag: ETag value
        """
        etag_key = f"etag:{url}"
        self.cache.set_raw_value(etag_key, etag)

    def get_cached_response(self, url: str) -> dict[str, Any] | None:
        """
        Gets cached response from cache

        Args:
            url: Request URL

        Returns:
            Cached response or None if not found
        """
        response_key = f"response:{url}"
        response_str = self.cache.get_raw_value(response_key)
        if response_str:
            try:
                return json.loads(response_str)
            except json.JSONDecodeError:
                return None
        return None

    def get_cached_response_for_304(self, url: str) -> dict[str, Any]:
        """
        Gets cached response for a 304 Not Modified response
        Raises exception if no cached response is available

        Args:
            url: Request URL

        Returns:
            Cached response

        Raises:
            Exception: If no cached response is available
        """
        cached_response = self.get_cached_response(url)
        if cached_response:
            return cached_response

        # If no cached response, invalidate ETag and raise exception
        logger.error(f"304 Not Modified for {url} but no cached response available")
        self.clear_etag(url)
        raise Exception(f"304 Not Modified for {url} but no cached response available")

    def set_cached_response(self, url: str, response_data: dict[str, Any]) -> None:
        """
        Stores cached response in cache

        Args:
            url: Request URL
            response_data: Response data to cache
        """
        response_key = f"response:{url}"
        self.cache.set_raw_value(response_key, json.dumps(response_data, ensure_ascii=False))

    def get_request_headers(self, url: str) -> dict[str, str]:
        """
        Gets request headers including If-None-Match if ETag is cached

        Args:
            url: Request URL

        Returns:
            Dictionary of headers
        """
        headers: dict[str, str] = {}
        etag = self.get_etag(url)
        if etag:
            headers["If-None-Match"] = etag
        return headers

    def _delete_from_cache(self, key: str) -> None:
        """
        Deletes a key from cache

        Args:
            key: Cache key to delete
        """
        if hasattr(self.cache, "redis_client"):
            self.cache.redis_client.delete(key)
        elif hasattr(self.cache, "delete_raw_value"):
            self.cache.delete_raw_value(key)

    def clear_etag(self, url: str) -> None:
        """
        Clears ETag for a URL

        Args:
            url: Request URL
        """
        etag_key = f"etag:{url}"
        self._delete_from_cache(etag_key)

    def clear_cached_response(self, url: str) -> None:
        """
        Clears cached response for a URL

        Args:
            url: Request URL
        """
        response_key = f"response:{url}"
        self._delete_from_cache(response_key)

    def clear_all(self, url: str) -> None:
        """
        Clears both ETag and cached response for a URL

        Args:
            url: Request URL
        """
        self.clear_etag(url)
        self.clear_cached_response(url)

    def update_from_response(self, url: str, response: Any) -> None:
        """
        Updates ETag cache from response headers
        Clears old cached response if ETag changed

        Args:
            url: Request URL
            response: HTTP response object with headers attribute
        """
        new_etag = response.headers.get("ETag")
        old_etag = self.get_etag(url)

        # If we have a new ETag
        if new_etag:
            # If ETag changed, clear old cached response (it's obsolete)
            if old_etag and old_etag != new_etag:
                self.clear_cached_response(url)
            self.set_etag(url, new_etag)
        else:
            # If response has no ETag, clear the cached one (resource no longer supports ETags)
            if old_etag:
                self.clear_all(url)

    def cache_response(self, url: str, response: Any, response_data: dict[str, Any]) -> None:
        """
        Updates ETag from response headers and caches the response data
        This is the main method to use after a successful API response

        Args:
            url: Request URL
            response: HTTP response object with headers attribute
            response_data: Response data to cache
        """
        # Update ETag from headers (this will clear old cached response if ETag changed)
        self.update_from_response(url, response)
        # Cache the new response
        self.set_cached_response(url, response_data)
