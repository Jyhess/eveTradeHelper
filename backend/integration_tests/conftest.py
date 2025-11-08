"""
Test configuration and shared fixtures
"""

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from application import AppFactory
from domain import Services
from eve.eve_repository_factory import make_eve_repository
from utils.cache import CacheManager, create_cache

# Path to tests directory
TESTS_DIR = Path(__file__).parent
REFERENCE_DIR = TESTS_DIR / "reference"


# Shared Redis cache for session (initialized once)
_cache_instance = None


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
    - For unit tests: disables cache (avoids conflicts with mocks)
    """
    # Check if it's a unit test (marked with @pytest.mark.unit)
    # Marker can be on class or method
    is_unit_test = request.node.get_closest_marker("unit") is not None or (
        hasattr(request.node, "parent")
        and request.node.parent is not None
        and request.node.parent.get_closest_marker("unit") is not None
    )

    if is_unit_test:
        # For unit tests, disable cache
        # Save current instance if it exists
        original_cache = CacheManager._instance
        # Completely disable cache for this test
        CacheManager._instance = None

        try:
            yield None
        finally:
            # Always restore cache after test (for other tests)
            CacheManager._instance = original_cache
    else:
        # For integration tests, use shared Redis cache
        CacheManager.initialize(_shared_cache)
        yield _shared_cache
        # Don't reinitialize - cache is shared


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
    """Fixture to create an Eve repository with test cache"""
    yield make_eve_repository()


@pytest.fixture
def services(eve_repository):
    """Fixture to create services with test cache"""
    return Services(eve_repository)


@pytest.fixture
def test_app(services):
    """Fixture to create a test FastAPI application"""
    app = FastAPI()
    AppFactory.register_routers(app)
    AppFactory.set_services(app, services)
    return app


@pytest.fixture
def client(test_app):
    """Fixture to create a test client"""
    return TestClient(test_app)
