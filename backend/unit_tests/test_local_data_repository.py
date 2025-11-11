import json
import tempfile
from pathlib import Path

import pytest

import repositories.local_data.local_data_repository as repo_module
from repositories.local_data.local_data_repository import (
    TYPES_FROM_ID_FILE,
    LocalDataRepository,
)
from utils.cache.fake_cache import FakeCache


@pytest.fixture
def local_data_repository(cache):
    return LocalDataRepository(cache)


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.mark.unit
class TestLocalDataRepository:
    def test_get_id_ranges_returns_id_ranges_instance(self, local_data_repository):
        id_ranges = local_data_repository.get_id_ranges()

        assert id_ranges is not None
        assert hasattr(id_ranges, "contains")
        assert hasattr(id_ranges, "get_type")

    def test_get_id_ranges_loads_from_file(self, local_data_repository):
        id_ranges = local_data_repository.get_id_ranges()

        assert id_ranges.contains(60008494) is True
        assert id_ranges.contains(30000142) is True

    def test_get_id_ranges_with_custom_file(self, cache, temp_dir):
        types_file = temp_dir / "typesFromId.json"
        test_data = {
            "id_map": [
                {
                    "type": "test_type",
                    "min": 1000,
                    "max": 2000,
                    "esi_check": "https://esi.evetech.net/latest/test/{id}/",
                    "comment": "Test type",
                }
            ]
        }
        with open(types_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)

        original_file = TYPES_FROM_ID_FILE
        try:
            repo_module.TYPES_FROM_ID_FILE = types_file

            repository = LocalDataRepository(cache)
            id_ranges = repository.get_id_ranges()

            assert id_ranges.contains(1500) is True
            assert id_ranges.contains(5000) is False
            assert id_ranges.get_type(1500) == "test_type"
        finally:
            repo_module.TYPES_FROM_ID_FILE = original_file

    def test_is_invalid_location_id_cached_returns_false_when_not_cached(
        self, local_data_repository
    ):
        assert local_data_repository.is_invalid_location_id_cached(999999999) is False

    def test_mark_location_id_as_invalid_and_check(self, local_data_repository):
        invalid_id = 888888888

        assert local_data_repository.is_invalid_location_id_cached(invalid_id) is False

        local_data_repository.mark_location_id_as_invalid(invalid_id)

        assert local_data_repository.is_invalid_location_id_cached(invalid_id) is True

    def test_mark_location_id_as_invalid_with_none_cache(self):
        fake_cache = FakeCache(expiry_hours=24)
        repository = LocalDataRepository(fake_cache)

        repository.mark_location_id_as_invalid(777777777)
        assert repository.is_invalid_location_id_cached(777777777) is False

    def test_get_max_int32(self, local_data_repository):
        assert local_data_repository.get_max_int32() == 2147483647

    def test_load_id_ranges_handles_missing_file(self, cache):
        original_file = TYPES_FROM_ID_FILE
        try:
            fake_path = Path("/nonexistent/path/typesFromId.json")
            repo_module.TYPES_FROM_ID_FILE = fake_path

            repository = LocalDataRepository(cache)
            id_ranges = repository.get_id_ranges()

            assert id_ranges.contains(1500) is False
        finally:
            repo_module.TYPES_FROM_ID_FILE = original_file

    def test_load_id_ranges_handles_invalid_json(self, cache, temp_dir):
        types_file = temp_dir / "typesFromId.json"
        with open(types_file, "w", encoding="utf-8") as f:
            f.write("invalid json content")

        original_file = TYPES_FROM_ID_FILE
        try:
            repo_module.TYPES_FROM_ID_FILE = types_file

            repository = LocalDataRepository(cache)
            id_ranges = repository.get_id_ranges()

            assert id_ranges.contains(1500) is False
        finally:
            repo_module.TYPES_FROM_ID_FILE = original_file
