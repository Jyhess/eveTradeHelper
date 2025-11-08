"""
Test configuration and shared fixtures
"""

import json
from pathlib import Path

import pytest

from eve.eve_api_client import EveAPIClient
from eve.eve_repository_factory import make_eve_repository
from utils.cache import CacheManager, create_cache
from utils.cache.fake_cache import FakeCache
from utils.cache.simple_cache import SimpleCache

# Path to tests directory
TESTS_DIR = Path(__file__).parent
REFERENCE_DIR = TESTS_DIR / "reference"


# Shared Redis cache for session (initialized once)
_cache_instance: SimpleCache | None = None


@pytest.fixture(scope="session")
def _shared_cache():
    """
    Shared Redis cache initialized once for the entire test session.
    Used only for integration tests.
    """
    global _cache_instance
    if _cache_instance is None:
        try:
            _cache_instance = create_cache()
        except Exception as e:
            pytest.skip(f"Redis is not available for tests: {e}")
    return _cache_instance


@pytest.fixture(scope="function")
def cache(request, _shared_cache):
    """
    Fixture to manage cache according to test type.
    - For integration tests: uses shared Redis cache
    - For unit tests (in unittests/): uses in-memory fake cache
    """
    # Check if it's a unit test
    # Either marked with @pytest.mark.unit, or in unittests directory
    is_unit_test = request.node.get_closest_marker("unit") is not None or (
        hasattr(request.node, "parent")
        and request.node.parent is not None
        and request.node.parent.get_closest_marker("unit") is not None
    )

    # If test is in unittests directory, use fake cache
    if not is_unit_test:
        test_file = getattr(request.node, "fspath", None)
        if test_file:
            test_path = Path(test_file)
            if "unittests" in test_path.parts:
                is_unit_test = True

    if is_unit_test:
        # For unit tests, use in-memory fake cache
        # Save current instance if it exists
        original_cache = CacheManager._instance
        # Create fake cache with same expiry duration as Redis cache
        fake_cache = FakeCache(expiry_hours=24 * 30)
        CacheManager.initialize(fake_cache)

        try:
            yield fake_cache
        finally:
            # Clear cache after each unit test
            fake_cache.clear()
            # Restore original cache after test
            CacheManager._instance = original_cache
    else:
        # For integration tests, use shared Redis cache
        CacheManager.initialize(_shared_cache)
        yield _shared_cache
        # Don't reinitialize - cache is shared


@pytest.fixture(scope="function")
def eve_client(cache):
    """Fixture to create an Eve API client with test cache"""
    return EveAPIClient()


@pytest.fixture(scope="session")
def reference_data():
    """Loads reference data for tests"""
    reference_data = {}

    if REFERENCE_DIR.exists():
        for ref_file in REFERENCE_DIR.glob("*.json"):
            key = ref_file.stem
            with open(ref_file, encoding="utf-8") as f:
                reference_data[key] = json.load(f)

    return reference_data


@pytest.fixture
def eve_repository(cache):
    yield make_eve_repository()
