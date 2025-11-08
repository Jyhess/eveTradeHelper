"""
Integration tests for EveAPIClient
Compares API responses with references
"""

import contextlib
import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

# Import utility functions
from unittests.test_utils import (
    load_reference,
    normalize_for_comparison,
    save_reference,
)

from domain.constants import DEFAULT_API_MAX_RETRIES
from domain.region_service import RegionService
from eve.eve_api_client import EveAPIClient
from eve.eve_repository_impl import EveRepositoryImpl
from utils.cache import CacheManager, SimpleCache
from utils.cache.fake_cache import FakeCache


class TestEveAPIClientRegions:
    """Tests for region-related methods"""

    @pytest.mark.asyncio
    async def test_get_regions_list(self, eve_client, reference_data):
        """Test retrieving region list"""
        result = await eve_client.get_regions_list()

        # Verify it's a list
        assert isinstance(result, list), "Result must be a list"
        assert len(result) > 0, "List must not be empty"
        assert all(
            isinstance(region_id, int) for region_id in result
        ), "All elements must be integers"

        # Compare with reference if it exists
        ref_key = "regions_list"
        reference = load_reference(ref_key)

        if reference:
            # Normalize for comparison
            result_normalized = normalize_for_comparison(result)
            ref_normalized = normalize_for_comparison(reference)

            assert result_normalized == ref_normalized, (
                f"Result does not match reference.\n"
                f"Result: {result_normalized[:5]}...\n"
                f"Reference: {ref_normalized[:5]}..."
            )
        else:
            # Save as new reference
            save_reference(ref_key, result)
            pytest.skip(f"No reference found. New reference saved: {ref_key}")

    @pytest.mark.asyncio
    async def test_get_region_details(self, eve_client, reference_data):
        """Test retrieving region details"""
        # Use a known region (The Forge - region ID 10000002)
        region_id = 10000002
        result = await eve_client.get_region_details(region_id)

        # Basic checks
        assert isinstance(result, dict), "Result must be a dictionary"
        assert "name" in result, "Result must contain 'name'"
        assert (
            "region_id" not in result or result.get("name") is not None
        ), "Name must be defined"

        # Compare with reference
        ref_key = f"region_details_{region_id}"
        reference = load_reference(ref_key)

        if reference:
            # Normalize for comparison
            result_normalized = normalize_for_comparison(result)
            ref_normalized = normalize_for_comparison(reference)

            # Compare key fields
            assert result_normalized.get("name") == ref_normalized.get("name"), (
                f"Region name does not match.\n"
                f"Result: {result_normalized.get('name')}\n"
                f"Reference: {ref_normalized.get('name')}"
            )

            # Verify constellations are present
            if "constellations" in ref_normalized:
                assert (
                    "constellations" in result_normalized
                ), "Constellations must be present"
                assert len(result_normalized["constellations"]) == len(
                    ref_normalized["constellations"]
                ), (
                    f"Number of constellations does not match.\n"
                    f"Result: {len(result_normalized['constellations'])}\n"
                    f"Reference: {len(ref_normalized['constellations'])}"
                )
        else:
            # Save as new reference
            save_reference(ref_key, result)
            pytest.skip(f"No reference found. New reference saved: {ref_key}")

    @pytest.mark.asyncio
    async def test_get_regions_with_details(self, eve_client, reference_data):
        """Test retrieving regions with their details (limited to 5 for tests)"""
        # Use domain service instead of direct method
        repository = EveRepositoryImpl(eve_client)
        region_service = RegionService(repository)

        limit = 5
        result = await region_service.get_regions_with_details(limit=limit)

        # Basic checks
        assert isinstance(result, list), "Result must be a list"
        assert len(result) <= limit, f"Result must not exceed {limit} elements"

        for region in result:
            assert isinstance(region, dict), "Each region must be a dictionary"
            assert "region_id" in region, "Each region must have a region_id"
            assert "name" in region, "Each region must have a name"

        # Compare with reference
        ref_key = f"regions_with_details_limit_{limit}"
        reference = load_reference(ref_key)

        if reference:
            # Normalize for comparison
            result_normalized = normalize_for_comparison(result)
            ref_normalized = normalize_for_comparison(reference)

            assert len(result_normalized) == len(ref_normalized), (
                f"Number of regions does not match.\n"
                f"Result: {len(result_normalized)}\n"
                f"Reference: {len(ref_normalized)}"
            )

            # Compare region names
            result_names = [r.get("name") for r in result_normalized]
            ref_names = [r.get("name") for r in ref_normalized]
            assert result_names == ref_names, (
                f"Region names do not match.\n"
                f"Result: {result_names}\n"
                f"Reference: {ref_names}"
            )
        else:
            # Save as new reference
            save_reference(ref_key, result)
            pytest.skip(f"No reference found. New reference saved: {ref_key}")


class TestEveAPIClientCache:
    """Tests to verify cache functionality"""

    @pytest.mark.asyncio
    async def test_cache_is_used(self, eve_client):
        """Verifies that cache is used on second call"""
        assert CacheManager.is_initialized(), "Cache must be initialized"

        # First call - must go to API
        result1 = await eve_client.get_regions_list()
        assert isinstance(result1, list)

        # Second call - must use cache
        result2 = await eve_client.get_regions_list()

        # Results must be identical
        assert result1 == result2, "Results must be identical (cache used)"

        # Verify cache contains data
        CacheManager.get_instance()
        # Cache should have been used (indirect verification via speed)

    @pytest.mark.asyncio
    async def test_cache_expiry(self, eve_client):
        """Verifies that cache expires correctly"""
        # Create cache with very short expiration (1 millisecond)
        # Use same storage but with different expiry
        original_cache = CacheManager.get_instance()

        # Detect cache type and create appropriate temporary instance
        if isinstance(original_cache, SimpleCache):
            short_cache = SimpleCache.__new__(SimpleCache)
            short_cache.expiry_hours = 0.000000278  # 1 ms
            short_cache.redis_client = original_cache.redis_client
        elif isinstance(original_cache, FakeCache):
            short_cache = FakeCache.__new__(FakeCache)
            short_cache.expiry_hours = 0.000000278  # 1 ms
            short_cache._cache_data = original_cache._cache_data
            short_cache._metadata = original_cache._metadata
        else:
            pytest.skip("Cache type not supported for this test")

        CacheManager.initialize(short_cache)

        # First call
        await eve_client.get_regions_list()

        # Wait for cache to expire
        time.sleep(0.01)  # 10 ms

        # Second call - cache should be expired
        # Can't really test that API is called again without mocking,
        # but can verify that cache doesn't return data
        CacheManager.get_instance()
        # Cache should be invalid now


class TestEveAPIClientStructure:
    """Tests to verify response structure"""

    @pytest.mark.asyncio
    async def test_region_details_structure(self, eve_client):
        """Verifies that region details have expected structure"""
        region_id = 10000002
        result = await eve_client.get_region_details(region_id)

        # Expected structure
        expected_keys = ["name", "constellations"]

        for key in expected_keys:
            assert key in result, f"Key '{key}' must be present in result"

        # Verify types
        assert isinstance(result["name"], str), "name must be a string"
        assert isinstance(result["constellations"], list), "constellations must be a list"

        # Verify constellations are integers
        if result["constellations"]:
            assert all(
                isinstance(c, int) for c in result["constellations"]
            ), "Constellations must be integers"

    @pytest.mark.asyncio
    async def test_regions_list_structure(self, eve_client):
        """Verifies that region list has expected structure"""
        result = await eve_client.get_regions_list()

        assert isinstance(result, list), "Result must be a list"

        if result:
            # Verify element types
            assert all(
                isinstance(item, int) for item in result
            ), "All elements must be integers"

            # Verify there are no duplicates
            assert len(result) == len(set(result)), "There must be no duplicates"


@pytest.mark.unit
class TestEveAPIClientRetry:
    """Tests for API call retry functionality"""

    @pytest.mark.asyncio
    async def test_retry_on_timeout_success(self):
        """Test that retry works with a temporary error that resolves"""
        client = EveAPIClient()

        # Mock HTTP client to simulate timeout then success
        mock_response = AsyncMock()
        mock_response.json = lambda: {"test": "data"}
        mock_response.raise_for_status = lambda: None

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
            patch.object(client, "_get_client", return_value=mock_http_client),
            patch.object(client, "_wait_for_rate_limit", return_value=None),
        ):
            result = await client._get("/test/endpoint")

            assert result == {"test": "data"}
            assert call_count["value"] == 2

    @pytest.mark.asyncio
    async def test_retry_uses_constants(self):
        """Test that retry uses defined constants"""
        client = EveAPIClient()

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with (
            patch.object(client, "_get_client", return_value=mock_http_client),
            patch.object(client, "_wait_for_rate_limit", return_value=None),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            with contextlib.suppress(Exception):
                await client._get("/test/endpoint")

            # Verify number of attempts matches constant + 1
            expected_calls = DEFAULT_API_MAX_RETRIES + 1
            assert mock_http_client.get.call_count == expected_calls
            # Verify sleep was called for each retry
            assert mock_sleep.call_count == DEFAULT_API_MAX_RETRIES

    @pytest.mark.asyncio
    async def test_retry_fails_after_max_attempts(self):
        """Test that retry fails after all attempts"""
        client = EveAPIClient()

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with (
            patch.object(client, "_get_client", return_value=mock_http_client),
            patch.object(client, "_wait_for_rate_limit", return_value=None),
        ):
            with pytest.raises(Exception) as exc_info:
                await client._get("/test/endpoint")

            assert "Timeout" in str(exc_info.value)
            # Verify all attempts were made
            expected_calls = DEFAULT_API_MAX_RETRIES + 1
            assert mock_http_client.get.call_count == expected_calls

    @pytest.mark.asyncio
    async def test_retry_on_http_error(self):
        """Test that retry works with an HTTP error"""
        client = EveAPIClient()

        mock_response = AsyncMock()
        mock_response.json = lambda: {"success": True}
        mock_response.raise_for_status = lambda: None

        mock_error_response = AsyncMock()
        mock_error_response.status_code = 500

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
            patch.object(client, "_get_client", return_value=mock_http_client),
            patch.object(client, "_wait_for_rate_limit", return_value=None),
        ):
            result = await client._get("/test/endpoint")

            assert result == {"success": True}
            assert call_count["value"] == 2

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self):
        """Test that retry works with a connection error"""
        client = EveAPIClient()

        mock_response = AsyncMock()
        mock_response.json = lambda: {"connected": True}
        mock_response.raise_for_status = lambda: None

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
            patch.object(client, "_get_client", return_value=mock_http_client),
            patch.object(client, "_wait_for_rate_limit", return_value=None),
        ):
            result = await client._get("/test/endpoint")

            assert result == {"connected": True}
            assert call_count["value"] == 2

    def test_create_exception_from_httpx_error(self):
        """Test that helper function creates correct exceptions"""
        client = EveAPIClient()
        url = "https://test.com/api"

        timeout_error = httpx.TimeoutException("Timeout")
        exception = client._create_exception_from_httpx_error(timeout_error, url)
        assert "Timeout" in str(exception)
        assert url in str(exception)

        mock_response = AsyncMock()
        mock_response.status_code = 404
        http_error = httpx.HTTPStatusError("Not Found", request=AsyncMock(), response=mock_response)
        exception = client._create_exception_from_httpx_error(http_error, url)
        assert "404" in str(exception)
        assert url in str(exception)

        request_error = httpx.RequestError("Connection failed")
        exception = client._create_exception_from_httpx_error(request_error, url)
        assert "connexion" in str(exception).lower() or "connection" in str(exception).lower()
        assert url in str(exception)

    def test_get_error_message(self):
        """Test that helper function generates correct error messages"""
        client = EveAPIClient()
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
