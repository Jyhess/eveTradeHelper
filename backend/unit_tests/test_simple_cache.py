"""
Unit tests for SimpleCache and FakeCache
"""

import pytest


@pytest.mark.unit
class TestSimpleCacheRawValues:
    """Tests for SimpleCache raw value methods"""

    def test_get_raw_value_nonexistent(self, cache):
        """Test getting a raw value that doesn't exist"""
        result = cache.get_raw_value("nonexistent_key")
        assert result is None

    def test_set_and_get_raw_value(self, cache):
        """Test setting and getting a raw value"""
        cache.set_raw_value("test_key", "test_value")
        result = cache.get_raw_value("test_key")
        assert result == "test_value"

    def test_set_raw_value_overwrite(self, cache):
        """Test that set_raw_value overwrites existing value"""
        cache.set_raw_value("test_key", "old_value")
        cache.set_raw_value("test_key", "new_value")
        result = cache.get_raw_value("test_key")
        assert result == "new_value"

    def test_get_raw_value_different_keys(self, cache):
        """Test that different keys return different values"""
        cache.set_raw_value("key1", "value1")
        cache.set_raw_value("key2", "value2")

        assert cache.get_raw_value("key1") == "value1"
        assert cache.get_raw_value("key2") == "value2"

    def test_get_raw_value_after_clear(self, cache):
        """Test that get_raw_value returns None after clear"""
        cache.set_raw_value("test_key", "test_value")
        cache.clear("test_key")
        result = cache.get_raw_value("test_key")
        assert result is None

    def test_get_raw_value_etag_format(self, cache):
        """Test storing and retrieving ETag format"""
        etag = '"abc123"'
        cache.set_raw_value("etag:https://test.com/api", etag)
        result = cache.get_raw_value("etag:https://test.com/api")
        assert result == etag

    def test_get_raw_value_json_format(self, cache):
        """Test storing and retrieving JSON format"""
        import json

        json_data = {"test": "data", "number": 42}
        json_str = json.dumps(json_data)
        cache.set_raw_value("response:https://test.com/api", json_str)
        result = cache.get_raw_value("response:https://test.com/api")
        assert result == json_str
        # Verify it can be parsed back
        parsed = json.loads(result)
        assert parsed == json_data
