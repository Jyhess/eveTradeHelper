"""
Rate limiter for EVE ESI API requests
Handles request throttling and ESI bucket tracking
"""

import asyncio
import contextlib
import logging
import time
from collections import defaultdict, deque
from typing import Any

import httpx

from domain.constants import (
    RATE_LIMIT_PER_SECOND,
    RATE_LIMIT_SLOWDOWN_DELAY_SECONDS,
    RATE_LIMIT_SLOWDOWN_THRESHOLD,
)

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API requests with ESI bucket tracking"""

    def __init__(self, rate_limit_per_second: int = RATE_LIMIT_PER_SECOND):
        """
        Initialize the rate limiter

        Args:
            rate_limit_per_second: Maximum number of requests per second
        """
        self.rate_limit_per_second = rate_limit_per_second

        # Rate limiting: keep timestamps of recent requests
        self._request_timestamps: deque = deque()
        self._rate_limit_lock: asyncio.Lock | None = None

        # Rate limit buckets tracking (per group)
        self._rate_limit_buckets: dict[str, dict[str, Any]] = defaultdict(
            lambda: {"remaining": None, "limit": None, "used": None}
        )

        # Error limit tracking
        self._error_limit_remain: int | None = None
        self._error_limit_reset: int | None = None
        self._error_limit_blocked_until: float | None = None

    def update_bucket_info(
        self, rate_limit_group: str, remaining: int | None, limit: str | None, used: int | None
    ) -> None:
        """
        Updates rate limit bucket information from response headers

        Args:
            rate_limit_group: Rate limit group identifier
            remaining: Remaining tokens
            limit: Rate limit string (e.g., "150/15m")
            used: Tokens used by the request
        """
        if not rate_limit_group:
            return

        bucket = self._rate_limit_buckets[rate_limit_group]
        if remaining is not None:
            bucket["remaining"] = remaining
        if limit is not None:
            bucket["limit"] = limit
        if used is not None:
            bucket["used"] = used

    def get_bucket_remaining(self, rate_limit_group: str | None) -> int | None:
        """
        Gets remaining tokens for a rate limit group

        Args:
            rate_limit_group: Rate limit group identifier

        Returns:
            Remaining tokens or None if not available
        """
        if not rate_limit_group:
            return None
        bucket = self._rate_limit_buckets.get(rate_limit_group)
        if bucket:
            return bucket.get("remaining")
        return None

    def _should_slowdown(self, rate_limit_group: str | None) -> bool:
        """
        Checks if we should slow down based on rate limit remaining

        Args:
            rate_limit_group: Rate limit group identifier

        Returns:
            True if we should slow down
        """
        if not rate_limit_group:
            return False
        bucket = self._rate_limit_buckets[rate_limit_group]
        remaining = bucket.get("remaining")
        if remaining is not None and remaining < RATE_LIMIT_SLOWDOWN_THRESHOLD:
            return True
        return False

    async def wait(self, rate_limit_group: str | None = None) -> None:
        """
        Waits if necessary to respect the rate limit
        Uses a 1-second sliding window
        Also blocks all requests if error limit is exceeded (error 420)

        Args:
            rate_limit_group: Optional rate limit group for ESI bucket tracking
        """
        # Initialize lock lazily (necessary because asyncio.Lock() cannot be created outside an event loop)
        if self._rate_limit_lock is None:
            self._rate_limit_lock = asyncio.Lock()

        async with self._rate_limit_lock:
            now = time.time()

            # Check if we're blocked due to error limit (420 error)
            if self._error_limit_blocked_until is not None:
                if now < self._error_limit_blocked_until:
                    wait_time = self._error_limit_blocked_until - now
                    logger.warning(
                        f"Blocked due to error limit, waiting {wait_time:.2f}s "
                        f"(until {self._error_limit_blocked_until:.2f})"
                    )
                    await asyncio.sleep(wait_time)
                    now = time.time()
                else:
                    # Blocking period expired, clear it
                    self._error_limit_blocked_until = None

            # Remove timestamps older than 1 second
            while self._request_timestamps and self._request_timestamps[0] < now - 1.0:
                self._request_timestamps.popleft()

            # If we've reached the limit, wait until a request exits the window
            if len(self._request_timestamps) >= self.rate_limit_per_second:
                oldest_timestamp = self._request_timestamps[0]
                wait_time = 1.0 - (now - oldest_timestamp)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Clean up again after waiting
                    now = time.time()
                    while self._request_timestamps and self._request_timestamps[0] < now - 1.0:
                        self._request_timestamps.popleft()

            # Add this request's timestamp
            self._request_timestamps.append(time.time())

            # Slow down if rate limit remaining is low (ESI best practice)
            if self._should_slowdown(rate_limit_group):
                await asyncio.sleep(RATE_LIMIT_SLOWDOWN_DELAY_SECONDS)

    def extract_limit_info(self, response: httpx.Response) -> None:
        """
        Extracts and stores rate limit and error limit information from response headers

        Args:
            response: HTTP response
        """
        # Extract rate limit info
        rate_limit_group = response.headers.get("X-Ratelimit-Group")
        if rate_limit_group:
            remaining = response.headers.get("X-Ratelimit-Remaining")
            limit = response.headers.get("X-Ratelimit-Limit")
            used = response.headers.get("X-Ratelimit-Used")

            remaining_int = None
            if remaining is not None:
                with contextlib.suppress(ValueError):
                    remaining_int = int(remaining)

            used_int = None
            if used is not None:
                with contextlib.suppress(ValueError):
                    used_int = int(used)

            self.update_bucket_info(rate_limit_group, remaining_int, limit, used_int)

        # Extract error limit info
        error_limit_remain = response.headers.get("X-ESI-Error-Limit-Remain")
        error_limit_reset = response.headers.get("X-ESI-Error-Limit-Reset")

        if error_limit_remain is not None:
            with contextlib.suppress(ValueError):
                self._error_limit_remain = int(error_limit_remain)
        if error_limit_reset is not None:
            with contextlib.suppress(ValueError):
                self._error_limit_reset = int(error_limit_reset)

    def get_error_limit_remain(self) -> int | None:
        """
        Gets remaining error limit

        Returns:
            Remaining error limit or None if not available
        """
        return self._error_limit_remain

    def get_error_limit_reset(self) -> int | None:
        """
        Gets error limit reset time

        Returns:
            Error limit reset time in seconds or None if not available
        """
        return self._error_limit_reset

    async def handle_429_retry_after(
        self, error: httpx.HTTPStatusError, url: str, attempt: int, max_retries: int
    ) -> int | None:
        """
        Handles 420 and 429 Rate Limited response with Retry-After header

        Args:
            error: HTTPStatusError with status 420 or 429
            url: Request URL for logging
            attempt: Current attempt number
            max_retries: Maximum number of retries

        Returns:
            Number of seconds to wait, or None if should not retry
        """
        status_code = error.response.status_code
        if status_code not in (420, 429):
            return None

        # Log detailed information for 420 errors
        if status_code == 420:
            self._log_error_response_details(error.response, url)

            # Block all requests for X-ESI-Error-Limit-Reset seconds
            error_limit_reset = error.response.headers.get("X-ESI-Error-Limit-Reset")
            if error_limit_reset is not None:
                try:
                    reset_seconds = int(error_limit_reset)
                    current_time = time.time()
                    self._error_limit_blocked_until = current_time + reset_seconds
                    logger.error(
                        f"Error 420 detected: blocking all requests for {reset_seconds}s "
                        f"(until {self._error_limit_blocked_until:.2f})"
                    )
                except ValueError:
                    logger.warning(
                        f"Error 420: invalid X-ESI-Error-Limit-Reset value: {error_limit_reset}"
                    )

        retry_after = error.response.headers.get("Retry-After")
        rate_limit_group = error.response.headers.get("X-Ratelimit-Group")

        # Extract limit info from error response if available
        if rate_limit_group:
            self.extract_limit_info(error.response)

        if retry_after and attempt < max_retries:
            try:
                retry_after_seconds = int(retry_after)
                status_name = "420" if status_code == 420 else "429"
                logger.warning(
                    f"Rate limited ({status_name}) for {url}, waiting {retry_after_seconds}s "
                    f"(attempt {attempt + 1}/{max_retries + 1})"
                )
                await asyncio.sleep(retry_after_seconds)
                return retry_after_seconds
            except ValueError:
                pass

        return None

    def _log_error_response_details(self, response: httpx.Response, url: str) -> None:
        """
        Logs detailed information about an error response (headers and body)

        Args:
            response: HTTP response
            url: Request URL for logging
        """
        try:
            # Log headers
            headers_dict = dict(response.headers)
            logger.error(f"Error 420 for {url} - Headers: {headers_dict}")

            # Log body
            try:
                # Try to read as text first (httpx automatically reads the body)
                body_text = response.text
                if body_text:
                    # Limit body length to avoid huge logs (first 2000 chars)
                    body_preview = body_text[:2000]
                    if len(body_text) > 2000:
                        body_preview += f"... (truncated, total length: {len(body_text)} chars)"
                    logger.error(f"Error 420 for {url} - Body: {body_preview}")
                else:
                    logger.error(f"Error 420 for {url} - Body: (empty)")
            except Exception:
                # If text reading fails, try to read as bytes
                try:
                    body_bytes = response.content
                    if body_bytes:
                        # Try to decode as UTF-8
                        try:
                            body_text = body_bytes.decode("utf-8")
                            body_preview = body_text[:2000]
                            if len(body_text) > 2000:
                                body_preview += (
                                    f"... (truncated, total length: {len(body_text)} chars)"
                                )
                            logger.error(f"Error 420 for {url} - Body: {body_preview}")
                        except UnicodeDecodeError:
                            # If decoding fails, log as bytes (limit to 2000 bytes)
                            body_preview = body_bytes[:2000]
                            if len(body_bytes) > 2000:
                                logger.error(
                                    f"Error 420 for {url} - Body (bytes, truncated): "
                                    f"{body_preview}... (truncated, total length: {len(body_bytes)} bytes)"
                                )
                            else:
                                logger.error(f"Error 420 for {url} - Body (bytes): {body_bytes}")
                    else:
                        logger.error(f"Error 420 for {url} - Body: (empty)")
                except Exception as e2:
                    logger.error(f"Error 420 for {url} - Could not read body: {e2}")

        except Exception as e:
            logger.error(f"Error 420 for {url} - Could not log response details: {e}")
