"""
Unit tests for EtagCache
"""

import json
from unittest.mock import AsyncMock

import pytest

from eve.etag_cache import EtagCache


@pytest.mark.unit
class TestEtagCache:
    """Tests for EtagCache class"""

    def test_initialization_requires_cache(self):
        """Test that EtagCache requires a cache instance"""
        with pytest.raises(ValueError, match="Cache instance is required"):
            EtagCache(cache=None)

    def test_initialization_with_cache(self, cache):
        """Test that EtagCache initializes with cache"""
        etag_cache = EtagCache(cache=cache)

        assert etag_cache.cache == cache

    def test_get_etag_nonexistent(self, cache):
        """Test getting ETag that doesn't exist"""
        etag_cache = EtagCache(cache=cache)

        result = etag_cache.get_etag("https://test.com/api")
        assert result is None

    def test_set_and_get_etag_with_cache(self, cache):
        """Test setting and getting ETag with cache"""
        etag_cache = EtagCache(cache=cache)

        etag_cache.set_etag("https://test.com/api", '"abc123"')
        result = etag_cache.get_etag("https://test.com/api")

        assert result == '"abc123"'

    def test_get_cached_response_nonexistent(self, cache):
        """Test getting cached response that doesn't exist"""
        etag_cache = EtagCache(cache=cache)

        result = etag_cache.get_cached_response("https://test.com/api")
        assert result is None

    def test_set_and_get_cached_response_with_cache(self, cache):
        """Test setting and getting cached response with cache"""
        etag_cache = EtagCache(cache=cache)

        response_data = {"test": "data", "number": 42}
        etag_cache.set_cached_response("https://test.com/api", response_data)
        result = etag_cache.get_cached_response("https://test.com/api")

        assert result == response_data

    def test_get_request_headers_no_etag(self, cache):
        """Test getting request headers when no ETag is cached"""
        etag_cache = EtagCache(cache=cache)

        headers = etag_cache.get_request_headers("https://test.com/api")

        assert headers == {}

    def test_get_request_headers_with_etag(self, cache):
        """Test getting request headers when ETag is cached"""
        etag_cache = EtagCache(cache=cache)

        etag_cache.set_etag("https://test.com/api", '"abc123"')
        headers = etag_cache.get_request_headers("https://test.com/api")

        assert headers == {"If-None-Match": '"abc123"'}

    def test_update_from_response(self, cache):
        """Test updating ETag from response headers"""
        etag_cache = EtagCache(cache=cache)

        mock_response = AsyncMock()
        mock_response.headers = {"ETag": '"xyz789"'}

        etag_cache.update_from_response("https://test.com/api", mock_response)

        assert etag_cache.get_etag("https://test.com/api") == '"xyz789"'

    def test_update_from_response_no_etag(self, cache):
        """Test updating from response without ETag header"""
        etag_cache = EtagCache(cache=cache)

        mock_response = AsyncMock()
        mock_response.headers = {}

        etag_cache.update_from_response("https://test.com/api", mock_response)

        assert etag_cache.get_etag("https://test.com/api") is None

    def test_etag_cache_isolation(self, cache):
        """Test that different URLs have isolated ETags"""
        etag_cache = EtagCache(cache=cache)

        etag_cache.set_etag("https://test.com/api1", '"etag1"')
        etag_cache.set_etag("https://test.com/api2", '"etag2"')

        assert etag_cache.get_etag("https://test.com/api1") == '"etag1"'
        assert etag_cache.get_etag("https://test.com/api2") == '"etag2"'

    def test_response_cache_isolation(self, cache):
        """Test that different URLs have isolated response caches"""
        etag_cache = EtagCache(cache=cache)

        response1 = {"data": "response1"}
        response2 = {"data": "response2"}

        etag_cache.set_cached_response("https://test.com/api1", response1)
        etag_cache.set_cached_response("https://test.com/api2", response2)

        assert etag_cache.get_cached_response("https://test.com/api1") == response1
        assert etag_cache.get_cached_response("https://test.com/api2") == response2

    def test_json_serialization_in_cache(self, cache):
        """Test that JSON is properly serialized/deserialized in cache"""
        etag_cache = EtagCache(cache=cache)

        response_data = {"test": "data", "nested": {"key": "value"}, "list": [1, 2, 3]}
        etag_cache.set_cached_response("https://test.com/api", response_data)
        result = etag_cache.get_cached_response("https://test.com/api")

        assert result == response_data
        # Verify it was stored as JSON in cache
        cached_json = cache.get_raw_value("response:https://test.com/api")
        assert cached_json is not None
        assert json.loads(cached_json) == response_data

    def test_clear_etag(self, cache):
        """Test clearing ETag"""
        etag_cache = EtagCache(cache=cache)

        etag_cache.set_etag("https://test.com/api", '"abc123"')
        assert etag_cache.get_etag("https://test.com/api") == '"abc123"'

        etag_cache.clear_etag("https://test.com/api")
        assert etag_cache.get_etag("https://test.com/api") is None

    def test_clear_cached_response(self, cache):
        """Test clearing cached response"""
        etag_cache = EtagCache(cache=cache)

        response_data = {"test": "data"}
        etag_cache.set_cached_response("https://test.com/api", response_data)
        assert etag_cache.get_cached_response("https://test.com/api") == response_data

        etag_cache.clear_cached_response("https://test.com/api")
        assert etag_cache.get_cached_response("https://test.com/api") is None

    def test_clear_all(self, cache):
        """Test clearing both ETag and cached response"""
        etag_cache = EtagCache(cache=cache)

        etag_cache.set_etag("https://test.com/api", '"abc123"')
        response_data = {"test": "data"}
        etag_cache.set_cached_response("https://test.com/api", response_data)

        etag_cache.clear_all("https://test.com/api")

        assert etag_cache.get_etag("https://test.com/api") is None
        assert etag_cache.get_cached_response("https://test.com/api") is None

    def test_update_from_response_clears_old_response_when_etag_changes(self, cache):
        """Test that old cached response is cleared when ETag changes"""
        etag_cache = EtagCache(cache=cache)

        # Set initial ETag and cached response
        etag_cache.set_etag("https://test.com/api", '"old_etag"')
        old_response = {"old": "data"}
        etag_cache.set_cached_response("https://test.com/api", old_response)

        # Update with new ETag
        mock_response = AsyncMock()
        mock_response.headers = {"ETag": '"new_etag"'}
        etag_cache.update_from_response("https://test.com/api", mock_response)

        # ETag should be updated
        assert etag_cache.get_etag("https://test.com/api") == '"new_etag"'
        # Old cached response should be cleared
        assert etag_cache.get_cached_response("https://test.com/api") is None

    def test_update_from_response_keeps_response_when_etag_unchanged(self, cache):
        """Test that cached response is kept when ETag doesn't change"""
        etag_cache = EtagCache(cache=cache)

        # Set initial ETag and cached response
        etag_cache.set_etag("https://test.com/api", '"same_etag"')
        response_data = {"test": "data"}
        etag_cache.set_cached_response("https://test.com/api", response_data)

        # Update with same ETag
        mock_response = AsyncMock()
        mock_response.headers = {"ETag": '"same_etag"'}
        etag_cache.update_from_response("https://test.com/api", mock_response)

        # ETag should still be the same
        assert etag_cache.get_etag("https://test.com/api") == '"same_etag"'
        # Cached response should still be there
        assert etag_cache.get_cached_response("https://test.com/api") == response_data

    def test_update_from_response_clears_all_when_no_etag(self, cache):
        """Test that ETag and cached response are cleared when response has no ETag"""
        etag_cache = EtagCache(cache=cache)

        # Set initial ETag and cached response
        etag_cache.set_etag("https://test.com/api", '"old_etag"')
        response_data = {"test": "data"}
        etag_cache.set_cached_response("https://test.com/api", response_data)

        # Update with no ETag (resource no longer supports ETags)
        mock_response = AsyncMock()
        mock_response.headers = {}
        etag_cache.update_from_response("https://test.com/api", mock_response)

        # Both should be cleared
        assert etag_cache.get_etag("https://test.com/api") is None
        assert etag_cache.get_cached_response("https://test.com/api") is None

    def test_clear_etag_with_cache(self, cache):
        """Test clearing ETag with cache"""
        etag_cache = EtagCache(cache=cache)

        etag_cache.set_etag("https://test.com/api", '"abc123"')
        assert etag_cache.get_etag("https://test.com/api") == '"abc123"'
        assert cache.get_raw_value("etag:https://test.com/api") == '"abc123"'

        etag_cache.clear_etag("https://test.com/api")
        assert etag_cache.get_etag("https://test.com/api") is None
        assert cache.get_raw_value("etag:https://test.com/api") is None

    def test_clear_cached_response_with_cache(self, cache):
        """Test clearing cached response with cache"""
        etag_cache = EtagCache(cache=cache)

        response_data = {"test": "data"}
        etag_cache.set_cached_response("https://test.com/api", response_data)
        assert etag_cache.get_cached_response("https://test.com/api") == response_data
        assert cache.get_raw_value("response:https://test.com/api") is not None

        etag_cache.clear_cached_response("https://test.com/api")
        assert etag_cache.get_cached_response("https://test.com/api") is None
        assert cache.get_raw_value("response:https://test.com/api") is None

    def test_get_cached_response_for_304_with_cache(self, cache):
        """Test get_cached_response_for_304 returns cached response when available"""
        etag_cache = EtagCache(cache=cache)

        response_data = {"test": "data"}
        etag_cache.set_cached_response("https://test.com/api", response_data)

        result = etag_cache.get_cached_response_for_304("https://test.com/api")
        assert result == response_data

    def test_get_cached_response_for_304_without_cache_raises_exception(self, cache):
        """Test get_cached_response_for_304 raises exception when no cache available"""
        etag_cache = EtagCache(cache=cache)

        # Set ETag but no cached response (inconsistent state)
        etag_cache.set_etag("https://test.com/api", '"abc123"')

        with pytest.raises(Exception, match="304 Not Modified.*no cached response"):
            etag_cache.get_cached_response_for_304("https://test.com/api")

        # ETag should be cleared
        assert etag_cache.get_etag("https://test.com/api") is None

    def test_cache_response_updates_etag_and_caches_data(self, cache):
        """Test cache_response updates ETag and caches response data"""
        etag_cache = EtagCache(cache=cache)

        mock_response = AsyncMock()
        mock_response.headers = {"ETag": '"new_etag"'}
        response_data = {"test": "data"}

        etag_cache.cache_response("https://test.com/api", mock_response, response_data)

        # ETag should be updated
        assert etag_cache.get_etag("https://test.com/api") == '"new_etag"'
        # Response should be cached
        assert etag_cache.get_cached_response("https://test.com/api") == response_data

    def test_cache_response_clears_old_response_when_etag_changes(self, cache):
        """Test cache_response clears old cached response when ETag changes"""
        etag_cache = EtagCache(cache=cache)

        # Set initial ETag and cached response
        etag_cache.set_etag("https://test.com/api", '"old_etag"')
        old_response = {"old": "data"}
        etag_cache.set_cached_response("https://test.com/api", old_response)

        # Cache new response with new ETag
        mock_response = AsyncMock()
        mock_response.headers = {"ETag": '"new_etag"'}
        new_response = {"new": "data"}
        etag_cache.cache_response("https://test.com/api", mock_response, new_response)

        # ETag should be updated
        assert etag_cache.get_etag("https://test.com/api") == '"new_etag"'
        # New response should be cached
        assert etag_cache.get_cached_response("https://test.com/api") == new_response
