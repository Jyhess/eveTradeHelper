"""
Client for Eve Online ESI (Eve Swagger Interface) API
Async version with httpx
"""

import asyncio
import functools
import logging
from typing import Any

import httpx

from domain.constants import (
    DEFAULT_API_MAX_RETRIES,
    DEFAULT_API_RETRY_DELAY_SECONDS,
    EVE_API_APP_NAME,
    EVE_API_APP_VERSION,
    EVE_API_CONTACT_EMAIL,
    EVE_API_SOURCE_URL,
)

from .etag_cache import EtagCache
from .exceptions import BadRequestError, ClientError, NotFoundError, ServerError
from .rate_limiter import RateLimiter

logger = logging.getLogger(__name__)


class EveAPIClient:
    """Client to interact with Eve Online ESI API (async)"""

    def __init__(
        self,
        rate_limiter: RateLimiter,
        etag_cache: EtagCache,
        base_url: str = "https://esi.evetech.net/latest",
        timeout: int = 10,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limiter = rate_limiter
        self.etag_cache = etag_cache

    async def close(self):
        """Closes the HTTP client"""
        if hasattr(self, "client"):
            await self.client.aclose()

    @functools.cached_property
    def client(self) -> httpx.AsyncClient:
        """Gets or creates an async HTTP client"""
        headers = {"User-Agent": self.user_agent}
        return httpx.AsyncClient(timeout=self.timeout, headers=headers)

    @functools.cached_property
    def user_agent(self) -> str:
        parts = [f"{EVE_API_APP_NAME}/{EVE_API_APP_VERSION}"]
        if EVE_API_CONTACT_EMAIL:
            parts.append(f"({EVE_API_CONTACT_EMAIL})")
        if EVE_API_SOURCE_URL:
            parts.append(f"(+{EVE_API_SOURCE_URL})")
        return " ".join(parts)

    async def get(
        self,
        endpoint: str,
        params: dict | None = None,
        max_retries: int = DEFAULT_API_MAX_RETRIES,
    ) -> dict[str, Any]:
        url = f"{self.base_url}{endpoint}"
        return await self._execute_request_with_retry(url, params, max_retries)

    async def _execute_request_with_retry(
        self, url: str, params: dict | None, max_retries: int
    ) -> dict[str, Any]:
        rate_limit_group: str | None = None

        for attempt in range(max_retries + 1):
            try:
                return await self._execute_request(url, params, rate_limit_group)

            except httpx.HTTPStatusError as e:
                retry_after_seconds = await self.rate_limiter.handle_429_retry_after(
                    e, url, attempt, max_retries
                )
                if retry_after_seconds is not None:
                    continue

                await self._handle_retry(e, url, attempt, max_retries)

            except (httpx.TimeoutException, httpx.RequestError) as e:
                await self._handle_retry(e, url, attempt, max_retries)

        raise Exception(f"Unexpected error calling {url}")

    async def _execute_request(
        self, url: str, params: dict | None, rate_limit_group: str | None
    ) -> dict[str, Any]:
        await self.rate_limiter.wait(rate_limit_group)

        headers = self.etag_cache.get_request_headers(url)
        response = await self.client.get(url, params=params, headers=headers)

        self.rate_limiter.extract_limit_info(response)

        if response.status_code == 304:
            logger.debug(f"304 Not Modified for {url}, using cached data")
            return self.etag_cache.get_cached_response_for_304(url)

        response.raise_for_status()
        result = response.json()

        if 200 <= response.status_code < 300:
            self.etag_cache.cache_response(url, response, result)

        return result

    async def _handle_retry(
        self, error: Exception, url: str, attempt: int, max_retries: int
    ) -> None:
        error_message = self._get_error_message(error, url)
        if self._should_retry_error(error) and attempt < max_retries:
            logger.warning(
                f"{error_message} (attempt {attempt + 1}/{max_retries + 1}). Retrying..."
            )
            await asyncio.sleep(DEFAULT_API_RETRY_DELAY_SECONDS)
        else:
            # Raise typed exceptions based on HTTP status code
            if isinstance(error, httpx.HTTPStatusError):
                status_code = error.response.status_code
                if status_code == 400:
                    raise BadRequestError(error_message, url) from None
                elif status_code == 404:
                    raise NotFoundError(error_message, url) from None
                elif 400 <= status_code < 500:
                    raise ClientError(error_message, status_code, url) from None
                elif 500 <= status_code < 600:
                    raise ServerError(error_message, status_code, url) from None
            raise Exception(error_message) from None

    def _should_retry_error(self, error: Exception) -> bool:
        # Always retry network errors (timeout, connection errors)
        if isinstance(error, (httpx.TimeoutException, httpx.RequestError)):
            return True

        # For HTTP status errors, check the status code
        if isinstance(error, httpx.HTTPStatusError):
            status_code = error.response.status_code
            # Retry rate limiting errors (420 is EVE Online specific, 429 is standard)
            if status_code in (420, 429):
                return True
            # Retry server errors (5xx) as they may be temporary
            if 500 <= status_code < 600:
                return True
            # Do not retry client errors (4xx) except rate limiting (420, 429)
            return False

        # Unknown error types, do not retry
        return False

    def _get_error_message(self, error: Exception, url: str) -> str:
        if isinstance(error, httpx.TimeoutException):
            return f"Timeout calling {url}: {error}"
        elif isinstance(error, httpx.HTTPStatusError):
            return f"HTTP error {error.response.status_code} calling {url}: {error}"
        elif isinstance(error, httpx.RequestError):
            return f"Connection error to {url}: {error}"
        else:
            return f"Unexpected error calling {url}: {error}"
