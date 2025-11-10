"""
Unit tests for RateLimiter
"""

import asyncio
import time
from unittest.mock import AsyncMock

import httpx
import pytest

from domain.constants import RATE_LIMIT_SLOWDOWN_DELAY_SECONDS, RATE_LIMIT_SLOWDOWN_THRESHOLD
from eve.rate_limiter import RateLimiter


@pytest.mark.unit
class TestRateLimiter:
    """Tests for RateLimiter class"""

    def test_initialization(self):
        """Test that RateLimiter initializes correctly"""
        limiter = RateLimiter(rate_limit_per_second=60)

        assert limiter.rate_limit_per_second == 60
        # Test that public methods work (indirect verification of initialization)
        assert limiter.get_bucket_remaining("test-group") is None
        assert limiter.get_error_limit_remain() is None
        assert limiter.get_error_limit_reset() is None

    def test_update_bucket_info(self):
        """Test updating bucket information"""
        limiter = RateLimiter()

        limiter.update_bucket_info("test-group", 100, "150/15m", 2)

        # Verify via public method
        assert limiter.get_bucket_remaining("test-group") == 100

    def test_update_bucket_info_partial(self):
        """Test updating bucket information with partial data"""
        limiter = RateLimiter()

        limiter.update_bucket_info("test-group", 50, None, None)

        # Verify via public method
        assert limiter.get_bucket_remaining("test-group") == 50

    def test_update_bucket_info_none_group(self):
        """Test that update_bucket_info does nothing with None group"""
        limiter = RateLimiter()

        limiter.update_bucket_info(None, 100, "150/15m", 2)

        # Verify via public method that no bucket was created
        assert limiter.get_bucket_remaining(None) is None
        assert limiter.get_bucket_remaining("any-group") is None

    def test_get_bucket_remaining(self):
        """Test getting remaining tokens from a bucket"""
        limiter = RateLimiter()

        limiter.update_bucket_info("test-group", 100, None, None)

        remaining = limiter.get_bucket_remaining("test-group")
        assert remaining == 100

    def test_get_bucket_remaining_none(self):
        """Test getting remaining tokens when bucket doesn't exist"""
        limiter = RateLimiter()

        remaining = limiter.get_bucket_remaining("unknown-group")
        assert remaining is None

    def test_get_bucket_remaining_none_group(self):
        """Test getting remaining tokens with None group"""
        limiter = RateLimiter()

        remaining = limiter.get_bucket_remaining(None)
        assert remaining is None

    @pytest.mark.asyncio
    async def test_slowdown_below_threshold(self):
        """Test that slowdown is triggered when remaining is below threshold"""
        limiter = RateLimiter()

        limiter.update_bucket_info("test-group", RATE_LIMIT_SLOWDOWN_THRESHOLD - 1, None, None)

        # Test via wait() method - should add slowdown delay
        start = time.time()
        await limiter.wait("test-group")
        duration = time.time() - start

        assert duration >= RATE_LIMIT_SLOWDOWN_DELAY_SECONDS - 0.01

    @pytest.mark.asyncio
    async def test_slowdown_at_threshold(self):
        """Test that slowdown is not triggered at threshold"""
        limiter = RateLimiter()

        limiter.update_bucket_info("test-group", RATE_LIMIT_SLOWDOWN_THRESHOLD, None, None)

        # Test via wait() method - should not add slowdown delay
        start = time.time()
        await limiter.wait("test-group")
        duration = time.time() - start

        assert duration < RATE_LIMIT_SLOWDOWN_DELAY_SECONDS

    @pytest.mark.asyncio
    async def test_slowdown_above_threshold(self):
        """Test that slowdown is not triggered above threshold"""
        limiter = RateLimiter()

        limiter.update_bucket_info("test-group", RATE_LIMIT_SLOWDOWN_THRESHOLD + 1, None, None)

        # Test via wait() method - should not add slowdown delay
        start = time.time()
        await limiter.wait("test-group")
        duration = time.time() - start

        assert duration < RATE_LIMIT_SLOWDOWN_DELAY_SECONDS

    @pytest.mark.asyncio
    async def test_slowdown_none_group(self):
        """Test that slowdown is not triggered with None group"""
        limiter = RateLimiter()

        # Test via wait() method - should not add slowdown delay
        start = time.time()
        await limiter.wait(None)
        duration = time.time() - start

        assert duration < RATE_LIMIT_SLOWDOWN_DELAY_SECONDS

    @pytest.mark.asyncio
    async def test_slowdown_none_remaining(self):
        """Test that slowdown is not triggered when remaining is None"""
        limiter = RateLimiter()

        limiter.update_bucket_info("test-group", None, None, None)

        # Test via wait() method - should not add slowdown delay
        start = time.time()
        await limiter.wait("test-group")
        duration = time.time() - start

        assert duration < RATE_LIMIT_SLOWDOWN_DELAY_SECONDS

    @pytest.mark.asyncio
    async def test_wait_respects_rate_limit(self):
        """Test that wait respects the rate limit per second"""
        limiter = RateLimiter(rate_limit_per_second=2)

        # First request should not wait
        start = time.time()
        await limiter.wait()
        first_duration = time.time() - start
        assert first_duration < 0.1  # Should be almost instant

        # Second request should not wait (within limit)
        start = time.time()
        await limiter.wait()
        second_duration = time.time() - start
        assert second_duration < 0.1  # Should be almost instant

        # Third request should wait (exceeds limit of 2 per second)
        start = time.time()
        await limiter.wait()
        third_duration = time.time() - start
        assert third_duration >= 0.1  # Should have waited

    @pytest.mark.asyncio
    async def test_wait_slows_down_when_remaining_low(self):
        """Test that wait slows down when remaining tokens are low"""
        limiter = RateLimiter()

        # Set up bucket with low remaining
        limiter.update_bucket_info("test-group", RATE_LIMIT_SLOWDOWN_THRESHOLD - 1, None, None)

        start = time.time()
        await limiter.wait("test-group")
        duration = time.time() - start

        # Should have added slowdown delay
        assert duration >= RATE_LIMIT_SLOWDOWN_DELAY_SECONDS - 0.01

    @pytest.mark.asyncio
    async def test_wait_no_slowdown_when_remaining_high(self):
        """Test that wait does not slow down when remaining tokens are high"""
        limiter = RateLimiter()

        # Set up bucket with high remaining
        limiter.update_bucket_info("test-group", RATE_LIMIT_SLOWDOWN_THRESHOLD + 10, None, None)

        start = time.time()
        await limiter.wait("test-group")
        duration = time.time() - start

        # Should not have added slowdown delay (only basic rate limiting)
        assert duration < RATE_LIMIT_SLOWDOWN_DELAY_SECONDS

    @pytest.mark.asyncio
    async def test_wait_cleans_old_timestamps(self):
        """Test that wait cleans up old timestamps"""
        limiter = RateLimiter(rate_limit_per_second=10)

        # Add many requests
        for _ in range(5):
            await limiter.wait()

        # Wait more than 1 second
        await asyncio.sleep(1.1)

        # Next request should not wait (old timestamps cleaned)
        start = time.time()
        await limiter.wait()
        duration = time.time() - start
        assert duration < 0.1  # Should be almost instant

    @pytest.mark.asyncio
    async def test_wait_thread_safe(self):
        """Test that wait is thread-safe with concurrent requests"""
        limiter = RateLimiter(rate_limit_per_second=5)

        # Make multiple concurrent requests
        async def make_request():
            await limiter.wait()

        start = time.time()
        await asyncio.gather(*[make_request() for _ in range(10)])
        duration = time.time() - start

        # Should have taken some time due to rate limiting
        assert duration > 0.1

    def test_extract_limit_info_complete(self):
        """Test extracting both rate limit and error limit info from response headers"""
        limiter = RateLimiter()

        mock_response = AsyncMock()
        mock_response.headers = {
            "X-Ratelimit-Group": "test-group",
            "X-Ratelimit-Remaining": "100",
            "X-Ratelimit-Limit": "150/15m",
            "X-Ratelimit-Used": "2",
            "X-ESI-Error-Limit-Remain": "10",
            "X-ESI-Error-Limit-Reset": "300",
        }

        limiter.extract_limit_info(mock_response)

        # Verify rate limit info via public method
        assert limiter.get_bucket_remaining("test-group") == 100

        # Verify error limit info via public methods
        assert limiter.get_error_limit_remain() == 10
        assert limiter.get_error_limit_reset() == 300

    def test_extract_limit_info_rate_limit_only(self):
        """Test extracting only rate limit info"""
        limiter = RateLimiter()

        mock_response = AsyncMock()
        mock_response.headers = {
            "X-Ratelimit-Group": "test-group",
            "X-Ratelimit-Remaining": "50",
        }

        limiter.extract_limit_info(mock_response)

        # Verify rate limit info via public method
        assert limiter.get_bucket_remaining("test-group") == 50

        # Error limit should remain None
        assert limiter.get_error_limit_remain() is None
        assert limiter.get_error_limit_reset() is None

    def test_extract_limit_info_error_limit_only(self):
        """Test extracting only error limit info"""
        limiter = RateLimiter()

        mock_response = AsyncMock()
        mock_response.headers = {
            "X-ESI-Error-Limit-Remain": "5",
        }

        limiter.extract_limit_info(mock_response)

        assert limiter.get_error_limit_remain() == 5
        assert limiter.get_error_limit_reset() is None

        # Rate limit buckets should remain empty (verify via public method)
        assert limiter.get_bucket_remaining("any-group") is None

    def test_extract_limit_info_no_group(self):
        """Test extracting limit info when no rate limit group header"""
        limiter = RateLimiter()

        mock_response = AsyncMock()
        mock_response.headers = {
            "X-Ratelimit-Remaining": "100",
            "X-ESI-Error-Limit-Remain": "10",
        }

        limiter.extract_limit_info(mock_response)

        # Rate limit buckets should remain empty (no group) - verify via public method
        assert limiter.get_bucket_remaining("any-group") is None

        # Error limit should be extracted
        assert limiter.get_error_limit_remain() == 10

    def test_extract_limit_info_invalid_values(self):
        """Test extracting limit info with invalid values"""
        limiter = RateLimiter()

        mock_response = AsyncMock()
        mock_response.headers = {
            "X-Ratelimit-Group": "test-group",
            "X-Ratelimit-Remaining": "invalid",
            "X-Ratelimit-Used": "also-invalid",
            "X-ESI-Error-Limit-Remain": "invalid",
            "X-ESI-Error-Limit-Reset": "also-invalid",
        }

        limiter.extract_limit_info(mock_response)

        # Verify via public method that invalid values are not stored
        assert limiter.get_bucket_remaining("test-group") is None

        assert limiter.get_error_limit_remain() is None
        assert limiter.get_error_limit_reset() is None

    def test_get_error_limit_remain(self):
        """Test getting error limit remain"""
        limiter = RateLimiter()

        assert limiter.get_error_limit_remain() is None

        # Set via extract_limit_info (public method)
        mock_response = AsyncMock()
        mock_response.headers = {"X-ESI-Error-Limit-Remain": "10"}
        limiter.extract_limit_info(mock_response)

        assert limiter.get_error_limit_remain() == 10

    def test_get_error_limit_reset(self):
        """Test getting error limit reset"""
        limiter = RateLimiter()

        assert limiter.get_error_limit_reset() is None

        # Set via extract_limit_info (public method)
        mock_response = AsyncMock()
        mock_response.headers = {"X-ESI-Error-Limit-Reset": "300"}
        limiter.extract_limit_info(mock_response)

        assert limiter.get_error_limit_reset() == 300

    @pytest.mark.asyncio
    async def test_handle_429_retry_after(self):
        """Test handling 429 with Retry-After header"""
        limiter = RateLimiter()

        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "5"}

        error = httpx.HTTPStatusError("Rate Limited", request=AsyncMock(), response=mock_response)

        retry_seconds = await limiter.handle_429_retry_after(error, "https://test.com", 0, 2)

        assert retry_seconds == 5

    @pytest.mark.asyncio
    async def test_handle_429_retry_after_with_rate_limit_group(self):
        """Test handling 429 with Retry-After and rate limit group"""
        limiter = RateLimiter()

        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.headers = {
            "Retry-After": "3",
            "X-Ratelimit-Group": "test-group",
            "X-Ratelimit-Remaining": "10",
        }

        error = httpx.HTTPStatusError("Rate Limited", request=AsyncMock(), response=mock_response)

        retry_seconds = await limiter.handle_429_retry_after(error, "https://test.com", 0, 2)

        assert retry_seconds == 3
        # Verify rate limit info was extracted via public method
        assert limiter.get_bucket_remaining("test-group") == 10

    @pytest.mark.asyncio
    async def test_handle_429_retry_after_no_retry_after_header(self):
        """Test handling 429 without Retry-After header"""
        limiter = RateLimiter()

        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.headers = {}

        error = httpx.HTTPStatusError("Rate Limited", request=AsyncMock(), response=mock_response)

        retry_seconds = await limiter.handle_429_retry_after(error, "https://test.com", 0, 2)

        assert retry_seconds is None

    @pytest.mark.asyncio
    async def test_handle_429_retry_after_max_retries_reached(self):
        """Test handling 429 when max retries reached"""
        limiter = RateLimiter()

        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "5"}

        error = httpx.HTTPStatusError("Rate Limited", request=AsyncMock(), response=mock_response)

        # attempt == max_retries (should not retry)
        retry_seconds = await limiter.handle_429_retry_after(error, "https://test.com", 2, 2)

        assert retry_seconds is None

    @pytest.mark.asyncio
    async def test_handle_429_retry_after_invalid_value(self):
        """Test handling 429 with invalid Retry-After value"""
        limiter = RateLimiter()

        mock_response = AsyncMock()
        mock_response.status_code = 429
        mock_response.headers = {"Retry-After": "invalid"}

        error = httpx.HTTPStatusError("Rate Limited", request=AsyncMock(), response=mock_response)

        retry_seconds = await limiter.handle_429_retry_after(error, "https://test.com", 0, 2)

        assert retry_seconds is None

    @pytest.mark.asyncio
    async def test_handle_429_retry_after_non_429_error(self):
        """Test that handle_429_retry_after returns None for non-429 errors"""
        limiter = RateLimiter()

        mock_response = AsyncMock()
        mock_response.status_code = 500

        error = httpx.HTTPStatusError("Server Error", request=AsyncMock(), response=mock_response)

        retry_seconds = await limiter.handle_429_retry_after(error, "https://test.com", 0, 2)

        assert retry_seconds is None

    @pytest.mark.asyncio
    async def test_error_420_blocks_all_requests_with_error_limit_reset(self):
        """Test that error 420 blocks all requests for X-ESI-Error-Limit-Reset seconds"""
        limiter = RateLimiter()
        error_limit_reset_seconds = 5

        mock_response = AsyncMock()
        mock_response.status_code = 420
        mock_response.headers = {"X-ESI-Error-Limit-Reset": str(error_limit_reset_seconds)}
        mock_response.text = "Error message"
        mock_response.content = b"Error message"

        error = httpx.HTTPStatusError(
            "Enhance Your Calm", request=AsyncMock(), response=mock_response
        )

        # Handle the 420 error
        await limiter.handle_429_retry_after(error, "https://test.com", 0, 2)

        # First wait should block for the error limit reset duration
        start = time.time()
        await limiter.wait()
        duration = time.time() - start

        # Should have waited approximately error_limit_reset_seconds
        assert duration >= error_limit_reset_seconds - 0.1
        assert duration < error_limit_reset_seconds + 0.5

    @pytest.mark.asyncio
    async def test_error_420_blocking_expires_after_reset_time(self):
        """Test that error 420 blocking expires after the reset time"""
        limiter = RateLimiter()
        error_limit_reset_seconds = 0.1  # Short duration for test

        mock_response = AsyncMock()
        mock_response.status_code = 420
        mock_response.headers = {"X-ESI-Error-Limit-Reset": str(error_limit_reset_seconds)}
        mock_response.text = "Error message"
        mock_response.content = b"Error message"

        error = httpx.HTTPStatusError(
            "Enhance Your Calm", request=AsyncMock(), response=mock_response
        )

        # Handle the 420 error
        await limiter.handle_429_retry_after(error, "https://test.com", 0, 2)

        # First wait should block
        start = time.time()
        await limiter.wait()
        first_duration = time.time() - start
        assert first_duration >= error_limit_reset_seconds - 0.1

        # Wait for the blocking to expire
        await asyncio.sleep(error_limit_reset_seconds + 0.1)

        # Second wait should not block (only normal rate limiting)
        start = time.time()
        await limiter.wait()
        second_duration = time.time() - start
        assert second_duration < 0.1  # Should be almost instant (only normal rate limiting)

    @pytest.mark.asyncio
    async def test_error_420_without_error_limit_reset_does_not_block(self):
        """Test that error 420 without X-ESI-Error-Limit-Reset does not block"""
        limiter = RateLimiter()

        mock_response = AsyncMock()
        mock_response.status_code = 420
        mock_response.headers = {}  # No X-ESI-Error-Limit-Reset header
        mock_response.text = "Error message"
        mock_response.content = b"Error message"

        error = httpx.HTTPStatusError(
            "Enhance Your Calm", request=AsyncMock(), response=mock_response
        )

        # Handle the 420 error
        await limiter.handle_429_retry_after(error, "https://test.com", 0, 2)

        # Wait should not block (only normal rate limiting)
        start = time.time()
        await limiter.wait()
        duration = time.time() - start

        # Should be almost instant (only normal rate limiting)
        assert duration < 0.1
