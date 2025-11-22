"""
ETag cache manager for EVE ESI API responses
Handles caching of ETags and responses for 304 Not Modified support
"""

import json
import logging
from typing import Any
from urllib.parse import urlencode

logger = logging.getLogger(__name__)


class EtagCache:
    def __init__(self, cache: Any):
        if cache is None:
            raise ValueError("Cache instance is required for EtagCache")
        if not hasattr(cache, "get_raw_value") or not hasattr(cache, "set_raw_value"):
            raise ValueError("Cache instance must have get_raw_value and set_raw_value methods")
        self.cache = cache

    def get_request_headers(self, url: str, params: dict | None = None) -> dict[str, str]:
        """Returns request headers with If-None-Match header if ETag is cached for the given URL and parameters"""
        cache_url = self._build_cache_url(url, params)
        headers: dict[str, str] = {}
        etag = self._get_etag_from_cache(cache_url)
        if etag:
            logger.info(f"Returning ETag '{etag}' for {cache_url}")
            headers["If-None-Match"] = etag
        return headers

    def get_cached_response_for_304(self, url: str, params: dict | None = None) -> dict[str, Any]:
        """Returns cached response for a 304 Not Modified response if ETag is cached for the given URL and parameters"""
        cache_url = self._build_cache_url(url, params)
        cached_response = self._get_cached_response(cache_url)
        if cached_response is not None:
            logger.info(f"Returning cached response for {cache_url}")
            return cached_response

        # If no cached response, invalidate ETag and raise exception
        error_message = f"No etag cached value for {cache_url}"
        logger.error(error_message)
        self._clear_etag_from_cache(cache_url)
        raise Exception(error_message)

    def update_etag_from_response(
        self, url: str, response: Any, response_data: dict[str, Any], params: dict | None = None
    ) -> None:
        """Updates ETag from response headers and caches the response data"""
        cache_url = self._build_cache_url(url, params)
        new_etag = response.headers.get("ETag")
        old_etag = self._get_etag_from_cache(cache_url)

        if new_etag:
            logger.info(f"Updating ETag '{new_etag}' for {cache_url}")
            if old_etag and old_etag != new_etag:
                self._clear_cached_response_from_cache(cache_url)
            self._set_etag_to_cache(cache_url, new_etag)
            self._set_cached_response_to_cache(cache_url, response_data)
        else:
            if old_etag:
                logger.info(f"Clearing ETag and cached response for {cache_url}")
                self.clear_etag_and_cached_response(cache_url)

    def clear_etag_and_cached_response(self, url: str, params: dict | None = None) -> None:
        """Clears ETag and cached response for the given URL and parameters"""
        cache_url = self._build_cache_url(url, params)
        self._clear_etag_from_cache(cache_url)
        self._clear_cached_response_from_cache(cache_url)

    def _build_cache_url(self, url: str, params: dict | None) -> str:
        if not params:
            return url

        sorted_params = sorted(params.items())
        query_string = urlencode(sorted_params)
        return f"{url}?{query_string}"

    def _get_cached_response(self, cache_url: str) -> dict[str, Any] | None:
        response_key = f"response:{cache_url}"
        try:
            response_str = self.cache.get_raw_value(response_key)
        except Exception as e:
            logger.error(f"Error getting cached response for {cache_url}: {e}")
            raise
        if response_str:
            try:
                return json.loads(response_str)
            except json.JSONDecodeError:
                return None
        return None

    def _clear_etag_from_cache(self, cache_url: str) -> None:
        etag_key = f"etag:{cache_url}"
        self.cache.delete_raw_value(etag_key)

    def _get_etag_from_cache(self, cache_url: str) -> str | None:
        etag_key = f"etag:{cache_url}"
        try:
            return self.cache.get_raw_value(etag_key)
        except Exception as e:
            return None

    def _set_etag_to_cache(self, cache_url: str, etag: str) -> None:
        etag_key = f"etag:{cache_url}"
        self.cache.set_raw_value(etag_key, etag)

    def _clear_cached_response_from_cache(self, cache_url: str) -> None:
        response_key = f"response:{cache_url}"
        self.cache.delete_raw_value(response_key)

    def _set_cached_response_to_cache(self, cache_url: str, response_data: dict[str, Any]) -> None:
        response_key = f"response:{cache_url}"
        self.cache.set_raw_value(response_key, json.dumps(response_data, ensure_ascii=False))

    def _delete_from_cache(self, key: str) -> None:
        if hasattr(self.cache, "delete_raw_value"):
            self.cache.delete_raw_value(key)
        elif hasattr(self.cache, "redis_client"):
            self.cache.redis_client.delete(key)
