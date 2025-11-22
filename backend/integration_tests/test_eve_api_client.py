"""
Integration tests for EveAPIClient
Tests the HTTP client functionality and best practices
"""

import contextlib
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from domain.constants import DEFAULT_API_MAX_RETRIES
from domain.exceptions import BadRequestError, NotFoundError
from eve.etag_cache import EtagCache
from eve.eve_api_client import EveAPIClient
from eve.rate_limiter import RateLimiter


@pytest.mark.integration
class TestEveAPIClientRetry:
    """Tests for API call retry functionality"""

    @pytest.mark.asyncio
    async def test_retry_on_timeout_success(self, cache):
        """Test that retry works with a temporary error that resolves"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        # Mock HTTP client to simulate timeout then success
        mock_response = AsyncMock()
        mock_response.json = lambda: {"test": "data"}
        mock_response.raise_for_status = lambda: None
        mock_response.headers = {}
        mock_response.status_code = 200

        mock_http_client = AsyncMock()
        call_count = {"value": 0}

        # First call fails (timeout), second succeeds
        async def mock_get(*args, **kwargs):
            if call_count["value"] == 0:
                call_count["value"] += 1
                raise httpx.TimeoutException("Timeout")
            else:
                call_count["value"] += 1
                return mock_response

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            result = await client.get("/test/endpoint")

            assert result == {"test": "data"}
            assert call_count["value"] == 2

    @pytest.mark.asyncio
    async def test_retry_uses_constants(self, cache):
        """Test that retry uses defined constants"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            with contextlib.suppress(Exception):
                await client.get("/test/endpoint")

            # Verify number of attempts matches constant + 1
            expected_calls = DEFAULT_API_MAX_RETRIES + 1
            assert mock_http_client.get.call_count == expected_calls
            # Verify sleep was called for each retry
            assert mock_sleep.call_count == DEFAULT_API_MAX_RETRIES

    @pytest.mark.asyncio
    async def test_retry_fails_after_max_attempts(self, cache):
        """Test that retry fails after all attempts"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            with pytest.raises(Exception) as exc_info:
                await client.get("/test/endpoint")

            assert "Timeout" in str(exc_info.value)
            # Verify all attempts were made
            expected_calls = DEFAULT_API_MAX_RETRIES + 1
            assert mock_http_client.get.call_count == expected_calls

    @pytest.mark.asyncio
    async def test_retry_on_http_error(self, cache):
        """Test that retry works with an HTTP error"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        mock_response = AsyncMock()
        mock_response.json = lambda: {"success": True}
        mock_response.raise_for_status = lambda: None
        mock_response.headers = {}
        mock_response.status_code = 200

        mock_error_response = AsyncMock()
        mock_error_response.status_code = 500
        mock_error_response.headers = {}

        mock_http_client = AsyncMock()
        call_count = {"value": 0}

        async def mock_get(*args, **kwargs):
            if call_count["value"] == 0:
                call_count["value"] += 1
                raise httpx.HTTPStatusError(
                    "Server Error", request=AsyncMock(), response=mock_error_response
                )
            else:
                call_count["value"] += 1
                return mock_response

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            result = await client.get("/test/endpoint")

            assert result == {"success": True}
            assert call_count["value"] == 2

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self, cache):
        """Test that retry works with a connection error"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        mock_response = AsyncMock()
        mock_response.json = lambda: {"connected": True}
        mock_response.raise_for_status = lambda: None
        mock_response.headers = {}
        mock_response.status_code = 200

        mock_http_client = AsyncMock()
        call_count = {"value": 0}

        async def mock_get(*args, **kwargs):
            if call_count["value"] == 0:
                call_count["value"] += 1
                raise httpx.RequestError("Connection failed")
            else:
                call_count["value"] += 1
                return mock_response

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            result = await client.get("/test/endpoint")

            assert result == {"connected": True}
            assert call_count["value"] == 2

    def test_get_error_message(self, cache):
        """Test that helper function generates correct error messages"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)
        url = "https://test.com/api"

        timeout_error = httpx.TimeoutException("Timeout")
        message = client._get_error_message(timeout_error, url)
        assert "Timeout" in message
        assert url in message

        mock_response = AsyncMock()
        mock_response.status_code = 500
        http_error = httpx.HTTPStatusError(
            "Server Error", request=AsyncMock(), response=mock_response
        )
        message = client._get_error_message(http_error, url)
        assert "500" in message
        assert url in message

        request_error = httpx.RequestError("Connection failed")
        message = client._get_error_message(request_error, url)
        assert "connexion" in message.lower() or "connection" in message.lower()
        assert url in message

    @pytest.mark.asyncio
    async def test_no_retry_on_400_bad_request(self, cache):
        """Test that 400 Bad Request errors are not retried"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        mock_error_response = AsyncMock()
        mock_error_response.status_code = 400
        mock_error_response.headers = {}

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Bad Request", request=AsyncMock(), response=mock_error_response
            )
        )

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            with pytest.raises(BadRequestError) as exc_info:
                await client.get("/test/endpoint")

            assert exc_info.value.status_code == 400
            # Verify only one attempt was made (no retry)
            assert mock_http_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_on_420_enhance_your_calm(self, cache):
        """Test that 420 Enhance Your Calm errors are retried like 429"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        mock_response = AsyncMock()
        mock_response.json = lambda: {"success": True}
        mock_response.raise_for_status = lambda: None
        mock_response.headers = {}
        mock_response.status_code = 200

        mock_420_response = AsyncMock()
        mock_420_response.status_code = 420
        mock_420_response.headers = {}

        mock_http_client = AsyncMock()
        call_count = {"value": 0}

        async def mock_get(*args, **kwargs):
            if call_count["value"] == 0:
                call_count["value"] += 1
                raise httpx.HTTPStatusError(
                    "Enhance Your Calm", request=AsyncMock(), response=mock_420_response
                )
            else:
                call_count["value"] += 1
                return mock_response

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            result = await client.get("/test/endpoint")

            assert result == {"success": True}
            assert call_count["value"] == 2

    @pytest.mark.asyncio
    async def test_no_retry_on_404_not_found(self, cache):
        """Test that 404 Not Found errors are not retried"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        mock_error_response = AsyncMock()
        mock_error_response.status_code = 404
        mock_error_response.headers = {}

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "Not Found", request=AsyncMock(), response=mock_error_response
            )
        )

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            with pytest.raises(NotFoundError) as exc_info:
                await client.get("/test/endpoint")

            assert exc_info.value.status_code == 404
            # Verify only one attempt was made (no retry)
            assert mock_http_client.get.call_count == 1


@pytest.mark.integration
class TestEveAPIClientBestPractices:
    """Tests for EVE ESI API best practices implementation"""

    @pytest.mark.asyncio
    async def test_user_agent_header_is_set(self, cache):
        """Test that User-Agent header is set according to best practices"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        # Verify User-Agent string is built correctly
        user_agent = client.user_agent
        assert "EveTradeHelper" in user_agent
        assert "1.0.0" in user_agent

        # Verify client is created with User-Agent header
        actual_client = client.client
        assert hasattr(actual_client, "headers")
        assert "User-Agent" in actual_client.headers
        assert actual_client.headers["User-Agent"] == user_agent

        await client.close()

    @pytest.mark.asyncio
    async def test_rate_limit_headers_are_tracked(self, cache):
        """Test that rate limit headers are tracked and used"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)
        mock_response = AsyncMock()
        mock_response.json = lambda: {"test": "data"}
        mock_response.raise_for_status = lambda: None
        mock_response.headers = {
            "X-Ratelimit-Group": "test-group",
            "X-Ratelimit-Limit": "150/15m",
            "X-Ratelimit-Remaining": "100",
            "X-Ratelimit-Used": "2",
        }
        mock_response.status_code = 200

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            await client.get("/test/endpoint")

            # Verify rate limit tracking exists
            assert hasattr(client, "rate_limiter")
            assert "test-group" in client.rate_limiter._rate_limit_buckets

    @pytest.mark.asyncio
    async def test_retry_after_on_429(self, cache):
        """Test that Retry-After header is respected on 429 response"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)
        retry_after_value = 5

        mock_429_response = AsyncMock()
        mock_429_response.status_code = 429
        mock_429_response.headers = {"Retry-After": str(retry_after_value)}
        mock_429_response.raise_for_status = lambda: None

        mock_success_response = AsyncMock()
        mock_success_response.json = lambda: {"test": "data"}
        mock_success_response.raise_for_status = lambda: None
        mock_success_response.headers = {}
        mock_success_response.status_code = 200

        mock_http_client = AsyncMock()
        call_count = {"value": 0}

        async def mock_get(*args, **kwargs):
            if call_count["value"] == 0:
                call_count["value"] += 1
                raise httpx.HTTPStatusError(
                    "Rate Limited", request=AsyncMock(), response=mock_429_response
                )
            else:
                call_count["value"] += 1
                return mock_success_response

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            result = await client.get("/test/endpoint")

            assert result == {"test": "data"}
            # Verify that sleep was called with Retry-After value
            assert mock_sleep.call_count >= 1
            # Check that one of the sleep calls used the retry-after value
            sleep_calls = [call[0][0] for call in mock_sleep.call_args_list]
            assert any(
                abs(call - retry_after_value) < 0.1 for call in sleep_calls
            ), f"Expected sleep with {retry_after_value}, got {sleep_calls}"

    @pytest.mark.asyncio
    async def test_error_limit_headers_are_tracked(self, cache):
        """Test that error limit headers are tracked"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)
        mock_response = AsyncMock()
        mock_response.json = lambda: {"test": "data"}
        mock_response.raise_for_status = lambda: None
        mock_response.headers = {
            "X-ESI-Error-Limit-Remain": "10",
            "X-ESI-Error-Limit-Reset": "300",
        }
        mock_response.status_code = 200

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=mock_response)

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            await client.get("/test/endpoint")

            # Verify error limit tracking exists
            assert hasattr(client.rate_limiter, "_error_limit_remain")
            assert hasattr(client.rate_limiter, "_error_limit_reset")
            assert client.rate_limiter.get_error_limit_remain() == 10
            assert client.rate_limiter.get_error_limit_reset() == 300

    @pytest.mark.asyncio
    async def test_etag_caching(self, cache):
        """Test that ETag and If-None-Match headers are used for caching"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        # First response with ETag
        first_response = AsyncMock()
        first_response.json = lambda: {"test": "data"}
        first_response.raise_for_status = lambda: None
        first_response.headers = {"ETag": '"abc123"'}
        first_response.status_code = 200

        # Second response with 304 (Not Modified)
        second_response = AsyncMock()
        second_response.json = lambda: {"test": "data"}
        second_response.raise_for_status = lambda: None
        second_response.headers = {}
        second_response.status_code = 304

        mock_http_client = AsyncMock()
        call_count = {"value": 0}

        async def mock_get(*args, **kwargs):
            call_count["value"] += 1
            if call_count["value"] == 1:
                return first_response
            else:
                return second_response

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            # First call
            result1 = await client.get("/test/endpoint")
            assert result1 == {"test": "data"}

            # Second call should use If-None-Match and return cached data
            result2 = await client.get("/test/endpoint")
            assert result2 == {"test": "data"}

            # Verify If-None-Match header was sent
            call_args = mock_http_client.get.call_args_list
            if len(call_args) > 1:
                headers = call_args[1].kwargs.get("headers", {})
                assert "If-None-Match" in headers
                assert headers["If-None-Match"] == '"abc123"'

    @pytest.mark.asyncio
    async def test_304_without_cached_response_invalidates_etag_and_raises_exception(self, cache):
        """Test that 304 response without cached response invalidates ETag and raises exception"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        # Set an ETag but no cached response (inconsistent state)
        # The URL will be constructed as base_url + endpoint = "https://esi.evetech.net/test/endpoint"
        url = "https://esi.evetech.net/test/endpoint"
        client.etag_cache._set_etag_to_cache(url, '"abc123"')

        # Response with 304 (Not Modified) but no cached response available
        response_304 = AsyncMock()
        response_304.headers = {}
        response_304.status_code = 304

        # First response to set ETag and cache
        first_response = AsyncMock()
        first_response.json = lambda: {"data": "test"}
        first_response.raise_for_status = lambda: None
        first_response.headers = {"ETag": '"abc123"'}
        first_response.status_code = 200

        mock_http_client = AsyncMock()
        call_count = {"value": 0}

        async def mock_get(*args, **kwargs):
            call_count["value"] += 1
            if call_count["value"] == 1:
                return first_response
            else:
                return response_304

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            # First call sets ETag and response
            await client.get("/test/endpoint")

            # Clear only the cached response but keep ETag (inconsistent state)
            # The client constructs URL as base_url + endpoint = "https://esi.evetech.net/test/endpoint"
            url = "https://esi.evetech.net/test/endpoint"
            # Clear only the cached response, not the ETag, using the private method
            client.etag_cache._clear_cached_response_from_cache(url)

            # Second call should receive 304 but have no cached response, so it should raise an exception
            with pytest.raises(Exception, match="No etag cached value"):
                await client.get("/test/endpoint")

            # ETag should be cleared after the exception
            etag = client.etag_cache._get_etag_from_cache(url)
            assert etag is None

    @pytest.mark.asyncio
    async def test_slowdown_when_rate_limit_low(self, cache):
        """Test that requests slow down when rate limit remaining is low"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        # Test rate limiter directly
        # Set up rate limit bucket with low remaining
        client.rate_limiter.update_bucket_info("test-group", 5, None, None)

        # Should slow down when remaining is below threshold
        # Access the private method through the rate limiter
        assert client.rate_limiter._should_slowdown("test-group") is True

        # Should not slow down when remaining is above threshold
        client.rate_limiter.update_bucket_info("test-group", 20, None, None)
        assert client.rate_limiter._should_slowdown("test-group") is False

        # Should not slow down when group is None
        assert client.rate_limiter._should_slowdown(None) is False

    @pytest.mark.asyncio
    async def test_etag_caching_with_different_params_uses_different_cache_keys(self, cache):
        """Test that requests with different parameters use different cache keys"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        # First response with type_id parameter
        response_with_type = AsyncMock()
        response_with_type.json = lambda: {"orders": [{"type_id": 123, "price": 100}]}
        response_with_type.raise_for_status = lambda: None
        response_with_type.headers = {"ETag": '"etag_with_type"'}
        response_with_type.status_code = 200

        # Second response without type_id parameter
        response_without_type = AsyncMock()
        response_without_type.json = lambda: {"orders": [{"type_id": 456, "price": 200}]}
        response_without_type.raise_for_status = lambda: None
        response_without_type.headers = {"ETag": '"etag_without_type"'}
        response_without_type.status_code = 200

        mock_http_client = AsyncMock()
        call_count = {"value": 0}

        async def mock_get(*args, **kwargs):
            call_count["value"] += 1
            if call_count["value"] == 1:
                return response_with_type
            elif call_count["value"] == 2:
                return response_without_type
            else:
                return response_with_type

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            # First call with type_id
            result1 = await client.get("/markets/10000002/orders/", params={"type_id": 123})
            assert result1 == {"orders": [{"type_id": 123, "price": 100}]}

            # Second call without type_id
            result2 = await client.get("/markets/10000002/orders/", params=None)
            assert result2 == {"orders": [{"type_id": 456, "price": 200}]}

            # Verify different ETags are cached for different parameters
            # The client constructs URL as base_url + endpoint = "https://esi.evetech.net/markets/10000002/orders/"
            headers_with_type = client.etag_cache.get_request_headers(
                "https://esi.evetech.net/markets/10000002/orders/", {"type_id": 123}
            )
            headers_without_type = client.etag_cache.get_request_headers(
                "https://esi.evetech.net/markets/10000002/orders/", None
            )

            assert headers_with_type["If-None-Match"] == '"etag_with_type"'
            assert headers_without_type["If-None-Match"] == '"etag_without_type"'
            assert headers_with_type["If-None-Match"] != headers_without_type["If-None-Match"]

            # Verify different responses are cached
            # The client constructs URL as base_url + endpoint = "https://esi.evetech.net/markets/10000002/orders/"
            cached_with_type = client.etag_cache.get_cached_response_for_304(
                "https://esi.evetech.net/markets/10000002/orders/", {"type_id": 123}
            )
            cached_without_type = client.etag_cache.get_cached_response_for_304(
                "https://esi.evetech.net/markets/10000002/orders/", None
            )

            assert cached_with_type == {"orders": [{"type_id": 123, "price": 100}]}
            assert cached_without_type == {"orders": [{"type_id": 456, "price": 200}]}

    @pytest.mark.asyncio
    async def test_etag_caching_with_params_304_uses_correct_cache(self, cache):
        """Test that 304 responses use the correct cached response for each parameter combination"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        # First response with type_id parameter
        first_response_with_type = AsyncMock()
        first_response_with_type.json = lambda: {"orders": [{"type_id": 123, "price": 100}]}
        first_response_with_type.raise_for_status = lambda: None
        first_response_with_type.headers = {"ETag": '"etag_type_123"'}
        first_response_with_type.status_code = 200

        # 304 response for type_id request
        response_304_with_type = AsyncMock()
        response_304_with_type.headers = {}
        response_304_with_type.status_code = 304

        # First response without type_id parameter
        first_response_without_type = AsyncMock()
        first_response_without_type.json = lambda: {"orders": [{"type_id": 456, "price": 200}]}
        first_response_without_type.raise_for_status = lambda: None
        first_response_without_type.headers = {"ETag": '"etag_no_type"'}
        first_response_without_type.status_code = 200

        # 304 response for no type_id request
        response_304_without_type = AsyncMock()
        response_304_without_type.headers = {}
        response_304_without_type.status_code = 304

        mock_http_client = AsyncMock()
        call_count = {"value": 0}

        async def mock_get(*args, **kwargs):
            call_count["value"] += 1
            params = kwargs.get("params", {})
            if call_count["value"] == 1:
                # First call with type_id
                return first_response_with_type
            elif call_count["value"] == 2:
                # Second call without type_id
                return first_response_without_type
            elif call_count["value"] == 3:
                # Third call with type_id - should return 304
                if params and params.get("type_id") == 123:
                    return response_304_with_type
                return first_response_with_type
            else:
                # Fourth call without type_id - should return 304
                if not params or "type_id" not in params:
                    return response_304_without_type
                return first_response_without_type

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            # First call with type_id
            result1 = await client.get("/markets/10000002/orders/", params={"type_id": 123})
            assert result1 == {"orders": [{"type_id": 123, "price": 100}]}

            # Second call without type_id
            result2 = await client.get("/markets/10000002/orders/", params=None)
            assert result2 == {"orders": [{"type_id": 456, "price": 200}]}

            # Third call with type_id - should use cached response (304)
            result3 = await client.get("/markets/10000002/orders/", params={"type_id": 123})
            assert result3 == {"orders": [{"type_id": 123, "price": 100}]}

            # Fourth call without type_id - should use cached response (304)
            result4 = await client.get("/markets/10000002/orders/", params=None)
            assert result4 == {"orders": [{"type_id": 456, "price": 200}]}

    @pytest.mark.asyncio
    async def test_etag_caching_params_normalized_sorted(self, cache):
        """Test that parameters are normalized (sorted) for consistent cache keys"""
        rate_limiter = RateLimiter()
        etag_cache = EtagCache(cache=cache)
        client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)

        # Response with multiple parameters
        response = AsyncMock()
        response.json = lambda: {"test": "data"}
        response.raise_for_status = lambda: None
        response.headers = {"ETag": '"etag_multiple_params"'}
        response.status_code = 200

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(return_value=response)

        with (
            patch.object(client, "client", mock_http_client),
            patch.object(client.rate_limiter, "wait", return_value=None),
        ):
            # Call with params in one order
            await client.get("/test/endpoint", params={"type_id": 123, "page": 1})

            # Verify cache key uses sorted parameters
            headers = client.etag_cache.get_request_headers(
                "https://esi.evetech.net/latest/test/endpoint", {"type_id": 123, "page": 1}
            )
            assert headers["If-None-Match"] == '"etag_multiple_params"'

            # Call with params in different order should use same cache key
            await client.get("/test/endpoint", params={"page": 1, "type_id": 123})

            # Should still use the same cache key (sorted)
            headers2 = client.etag_cache.get_request_headers(
                "https://esi.evetech.net/latest/test/endpoint", {"page": 1, "type_id": 123}
            )
            assert headers2["If-None-Match"] == '"etag_multiple_params"'
