"""
Unit tests for EtagCache
"""

import json
from unittest.mock import AsyncMock

import pytest

from eve.etag_cache import EtagCache


@pytest.fixture
def etag_cache(cache):
    return EtagCache(cache=cache)


@pytest.mark.unit
class TestEtagCache:
    def test_initialization_requires_cache(self):
        with pytest.raises(ValueError, match="Cache instance is required"):
            EtagCache(cache=None)

    def test_get_etag_nonexistent(self, etag_cache):
        headers = etag_cache.get_request_headers("https://test.com/api")
        assert "If-None-Match" not in headers

    def test_get_cached_response_for_304_without_cache_raises_exception(self, etag_cache):
        with pytest.raises(Exception, match="No etag cached value"):
            etag_cache.get_cached_response_for_304("https://test.com/api")

    def test_get_request_headers_with_etag(self, etag_cache):
        mock_response = AsyncMock()
        mock_response.headers = {"ETag": '"abc123"'}
        etag_cache.update_etag_from_response("https://test.com/api", mock_response, {})
        headers = etag_cache.get_request_headers("https://test.com/api")

        assert headers == {"If-None-Match": '"abc123"'}

    def test_update_from_response(self, etag_cache):
        mock_response = AsyncMock()
        mock_response.headers = {"ETag": '"xyz789"'}

        etag_cache.update_etag_from_response("https://test.com/api", mock_response, {"foo": "bar"})

        headers = etag_cache.get_request_headers("https://test.com/api")
        assert headers["If-None-Match"] == '"xyz789"'
        assert etag_cache.get_cached_response_for_304("https://test.com/api") == {"foo": "bar"}

    def test_update_from_response_no_data(self, etag_cache):
        mock_response = AsyncMock()
        mock_response.headers = {"ETag": '"xyz789"'}

        etag_cache.update_etag_from_response("https://test.com/api", mock_response, {})

        headers = etag_cache.get_request_headers("https://test.com/api")
        assert headers["If-None-Match"] == '"xyz789"'
        assert etag_cache.get_cached_response_for_304("https://test.com/api") == {}

    def test_update_from_response_no_etag(self, etag_cache):
        # First set an ETag
        mock_response_with_etag = AsyncMock()
        mock_response_with_etag.headers = {"ETag": '"old_etag"'}
        etag_cache.update_etag_from_response("https://test.com/api", mock_response_with_etag, {})

        # Then update without ETag
        mock_response = AsyncMock()
        mock_response.headers = {}
        etag_cache.update_etag_from_response("https://test.com/api", mock_response, {})

        headers = etag_cache.get_request_headers("https://test.com/api")
        assert "If-None-Match" not in headers
        with pytest.raises(Exception, match="No etag cached value"):
            etag_cache.get_cached_response_for_304("https://test.com/api")

    def test_etag_cache_isolation(self, etag_cache):
        """Test that different URLs have isolated ETags"""
        mock_response1 = AsyncMock()
        mock_response1.headers = {"ETag": '"etag1"'}
        etag_cache.update_etag_from_response("https://test.com/api1", mock_response1, {})

        mock_response2 = AsyncMock()
        mock_response2.headers = {"ETag": '"etag2"'}
        etag_cache.update_etag_from_response("https://test.com/api2", mock_response2, {})

        headers1 = etag_cache.get_request_headers("https://test.com/api1")
        headers2 = etag_cache.get_request_headers("https://test.com/api2")
        assert headers1["If-None-Match"] == '"etag1"'
        assert headers2["If-None-Match"] == '"etag2"'

    def test_response_cache_isolation(self, etag_cache):
        """Test that different URLs have isolated response caches"""
        response1 = {"data": "response1"}
        response2 = {"data": "response2"}

        mock_response1 = AsyncMock()
        mock_response1.headers = {"ETag": '"etag1"'}
        etag_cache.update_etag_from_response("https://test.com/api1", mock_response1, response1)

        mock_response2 = AsyncMock()
        mock_response2.headers = {"ETag": '"etag2"'}
        etag_cache.update_etag_from_response("https://test.com/api2", mock_response2, response2)

        assert etag_cache.get_cached_response_for_304("https://test.com/api1") == response1
        assert etag_cache.get_cached_response_for_304("https://test.com/api2") == response2

    def test_json_serialization_in_cache(self, etag_cache, cache):
        """Test that JSON is properly serialized/deserialized in cache"""
        response_data = {"test": "data", "nested": {"key": "value"}, "list": [1, 2, 3]}
        mock_response = AsyncMock()
        mock_response.headers = {"ETag": '"etag123"'}
        etag_cache.update_etag_from_response("https://test.com/api", mock_response, response_data)
        result = etag_cache.get_cached_response_for_304("https://test.com/api")

        assert result == response_data
        # Verify it was stored as JSON in cache
        cached_json = cache.get_raw_value("response:https://test.com/api")
        assert cached_json is not None
        assert json.loads(cached_json) == response_data

    def test_clear_all(self, etag_cache):
        """Test clearing both ETag and cached response"""
        response_data = {"test": "data"}
        mock_response = AsyncMock()
        mock_response.headers = {"ETag": '"abc123"'}
        etag_cache.update_etag_from_response("https://test.com/api", mock_response, response_data)

        etag_cache.clear_etag_and_cached_response("https://test.com/api")

        headers = etag_cache.get_request_headers("https://test.com/api")
        assert "If-None-Match" not in headers
        with pytest.raises(Exception, match="No etag cached value"):
            etag_cache.get_cached_response_for_304("https://test.com/api")

    def test_update_from_response_clears_old_response_when_etag_changes(self, etag_cache):
        """Test that old cached response is cleared when ETag changes"""
        # Set initial ETag and cached response
        old_response = {"old": "data"}
        mock_response_old = AsyncMock()
        mock_response_old.headers = {"ETag": '"old_etag"'}
        etag_cache.update_etag_from_response(
            "https://test.com/api", mock_response_old, old_response
        )

        # Update with new ETag
        mock_response = AsyncMock()
        mock_response.headers = {"ETag": '"new_etag"'}
        etag_cache.update_etag_from_response("https://test.com/api", mock_response, {})

        # ETag should be updated
        headers = etag_cache.get_request_headers("https://test.com/api")
        assert headers["If-None-Match"] == '"new_etag"'
        # Old response is replaced by new response
        assert etag_cache.get_cached_response_for_304("https://test.com/api") == {}

    def test_update_from_response_keeps_response_when_etag_unchanged(self, etag_cache):
        """Test that cached response is kept when ETag doesn't change"""
        # Set initial ETag and cached response
        response_data = {"test": "data"}
        mock_response_initial = AsyncMock()
        mock_response_initial.headers = {"ETag": '"same_etag"'}
        etag_cache.update_etag_from_response(
            "https://test.com/api", mock_response_initial, response_data
        )

        # Update with same ETag and new response data
        new_response_data = {"test": "new_data"}
        mock_response = AsyncMock()
        mock_response.headers = {"ETag": '"same_etag"'}
        etag_cache.update_etag_from_response(
            "https://test.com/api", mock_response, new_response_data
        )

        # ETag should still be the same
        headers = etag_cache.get_request_headers("https://test.com/api")
        assert headers["If-None-Match"] == '"same_etag"'
        # New response should be cached
        assert etag_cache.get_cached_response_for_304("https://test.com/api") == new_response_data

    def test_update_from_response_clears_all_when_no_etag(self, etag_cache):
        """Test that ETag and cached response are cleared when response has no ETag"""
        # Set initial ETag and cached response
        response_data = {"test": "data"}
        mock_response_initial = AsyncMock()
        mock_response_initial.headers = {"ETag": '"old_etag"'}
        etag_cache.update_etag_from_response(
            "https://test.com/api", mock_response_initial, response_data
        )

        # Update with no ETag (resource no longer supports ETags)
        mock_response = AsyncMock()
        mock_response.headers = {}
        etag_cache.update_etag_from_response("https://test.com/api", mock_response, {})

        # Both should be cleared
        headers = etag_cache.get_request_headers("https://test.com/api")
        assert "If-None-Match" not in headers
        with pytest.raises(Exception, match="No etag cached value"):
            etag_cache.get_cached_response_for_304("https://test.com/api")
