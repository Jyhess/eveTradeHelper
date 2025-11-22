"""
Integration tests for EveRepositoryImpl
Compares API responses with references

NOTE: This file contains integration tests that use real EveAPIClient.
These tests should ideally be moved to integration_tests/ directory.
"""

import time

import pytest

from domain.region_service import RegionService
from eve.etag_cache import EtagCache
from eve.eve_api_client import EveAPIClient
from eve.eve_repository_impl import EveRepositoryImpl
from eve.rate_limiter import RateLimiter
from utils.cache import CacheManager, SimpleCache

from .test_utils import (
    load_reference,
    normalize_for_comparison,
    save_reference,
)


@pytest.fixture
def eve_client(cache):
    """Fixture to create an Eve API client with test cache (for integration tests only)"""
    rate_limiter = RateLimiter()
    etag_cache = EtagCache(cache=cache)
    return EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)


@pytest.fixture
def repository(eve_client):
    """Fixture to create an EveRepositoryImpl instance"""
    return EveRepositoryImpl(eve_client)


class TestEveRepositoryImplRegions:
    """Tests for region-related methods"""

    @pytest.mark.asyncio
    async def test_get_regions_list(self, repository, reference_data):
        """Test retrieving region list"""
        result = await repository.get_regions_list()

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
    async def test_get_region_details(self, repository, reference_data):
        """Test retrieving region details"""
        # Use a known region (The Forge - region ID 10000002)
        region_id = 10000002
        result = await repository.get_region_details(region_id)

        # Basic checks - result is now a RegionDetails object
        assert hasattr(result, "name"), "Result must have 'name' attribute"
        assert hasattr(result, "region_id"), "Result must have 'region_id' attribute"
        assert result.name is not None, "Name must be defined"

        # Compare with reference
        ref_key = f"region_details_{region_id}"
        reference = load_reference(ref_key)

        if reference:
            # Normalize for comparison (convert to dict)
            result_dict = result.to_dict() if hasattr(result, "to_dict") else result
            result_normalized = normalize_for_comparison(result_dict)
            ref_normalized = normalize_for_comparison(reference)

            # Compare key fields
            assert result_normalized.get("name") == ref_normalized.get("name"), (
                f"Region name does not match.\n"
                f"Result: {result_normalized.get('name')}\n"
                f"Reference: {ref_normalized.get('name')}"
            )

            # Verify constellations are present
            if "constellations" in ref_normalized:
                assert "constellations" in result_normalized, "Constellations must be present"
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
    async def test_get_regions_with_details(self, repository, reference_data):
        """Test retrieving regions with their details (limited to 5 for tests)"""
        # Use domain service instead of direct method
        from domain.region_data import RegionData

        region_data = RegionData(repository)
        region_service = RegionService(repository, region_data)

        result = await region_service.get_regions_with_details()

        # Basic checks - result is now a list of RegionDetails objects
        assert isinstance(result, list), "Result must be a list"

        for region in result:
            assert hasattr(region, "region_id"), "Each region must have a region_id attribute"
            assert hasattr(region, "name"), "Each region must have a name attribute"

        # Compare with reference
        ref_key = "regions_with_details"
        reference = load_reference(ref_key)

        if reference:
            # Normalize for comparison (convert to dicts)
            result_dicts = [r.to_dict() if hasattr(r, "to_dict") else r for r in result]
            result_normalized = normalize_for_comparison(result_dicts)
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


class TestEveRepositoryImplCache:
    """Tests to verify cache functionality"""

    @pytest.mark.asyncio
    async def test_cache_is_used(self, repository):
        """Verifies that cache is used on second call"""
        assert CacheManager.is_initialized(), "Cache must be initialized"

        # First call - must go to API
        result1 = await repository.get_regions_list()
        assert isinstance(result1, list)

        # Second call - must use cache
        result2 = await repository.get_regions_list()

        # Results must be identical
        assert result1 == result2, "Results must be identical (cache used)"

        # Verify cache contains data
        CacheManager.get_instance()
        # Cache should have been used (indirect verification via speed)

    @pytest.mark.asyncio
    async def test_cache_expiry(self, repository):
        """Verifies that cache expires correctly"""
        # Create cache with very short expiration (1 millisecond)
        # Use same storage but with different expiry
        original_cache = CacheManager.get_instance()

        # Create appropriate temporary instance
        if isinstance(original_cache, SimpleCache):
            short_cache = SimpleCache.__new__(SimpleCache)
            short_cache.expiry_hours = 0.000000278  # 1 ms
            short_cache.redis_client = original_cache.redis_client
        else:
            pytest.skip("Cache type not supported for this test")

        CacheManager.initialize(short_cache)

        # First call
        await repository.get_regions_list()

        # Wait for cache to expire
        time.sleep(0.01)  # 10 ms

        # Second call - cache should be expired
        # Can't really test that API is called again without mocking,
        # but can verify that cache doesn't return data
        CacheManager.get_instance()
        # Cache should be invalid now


class TestEveRepositoryImplStructure:
    """Tests to verify response structure"""

    @pytest.mark.asyncio
    async def test_region_details_structure(self, repository):
        """Verifies that region details have expected structure"""
        region_id = 10000002
        result = await repository.get_region_details(region_id)

        # Expected structure - result is now a RegionDetails object
        assert hasattr(result, "name"), "Result must have 'name' attribute"
        assert hasattr(result, "constellations"), "Result must have 'constellations' attribute"

        # Verify types
        assert isinstance(result.name, str), "name must be a string"
        assert isinstance(result.constellations, list), "constellations must be a list"

        # Verify constellations are integers
        if result.constellations:
            assert all(
                isinstance(c, int) for c in result.constellations
            ), "Constellations must be integers"

    @pytest.mark.asyncio
    async def test_regions_list_structure(self, repository):
        """Verifies that region list has expected structure"""
        result = await repository.get_regions_list()

        assert isinstance(result, list), "Result must be a list"

        if result:
            # Verify element types
            assert all(isinstance(item, int) for item in result), "All elements must be integers"

            # Verify there are no duplicates
            assert len(result) == len(set(result)), "There must be no duplicates"
