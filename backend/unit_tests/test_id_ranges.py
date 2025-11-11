import pytest

from repositories.local_data.id_ranges import IdRanges


@pytest.mark.unit
class TestIdRanges:
    def test_contains_with_id_in_range(self):
        ranges = [{"min": 1000, "max": 2000, "type": "test_type"}]
        id_ranges = IdRanges(ranges)

        assert id_ranges.contains(1500) is True
        assert id_ranges.contains(1000) is True
        assert id_ranges.contains(2000) is True

    def test_contains_with_id_outside_range(self):
        ranges = [{"min": 1000, "max": 2000, "type": "test_type"}]
        id_ranges = IdRanges(ranges)

        assert id_ranges.contains(500) is False
        assert id_ranges.contains(2500) is False

    def test_contains_with_multiple_ranges(self):
        ranges = [
            {"min": 1000, "max": 2000, "type": "type1"},
            {"min": 3000, "max": 4000, "type": "type2"},
        ]
        id_ranges = IdRanges(ranges)

        assert id_ranges.contains(1500) is True
        assert id_ranges.contains(3500) is True
        assert id_ranges.contains(2500) is False

    def test_contains_with_none_values(self):
        ranges = [{"min": None, "max": 2000, "type": "test_type"}]
        id_ranges = IdRanges(ranges)

        assert id_ranges.contains(1500) is False

        ranges = [{"min": 1000, "max": None, "type": "test_type"}]
        id_ranges = IdRanges(ranges)

        assert id_ranges.contains(1500) is False

    def test_get_type_with_id_in_range(self):
        ranges = [{"min": 1000, "max": 2000, "type": "test_type"}]
        id_ranges = IdRanges(ranges)

        assert id_ranges.get_type(1500) == "test_type"
        assert id_ranges.get_type(1000) == "test_type"
        assert id_ranges.get_type(2000) == "test_type"

    def test_get_type_with_id_outside_range(self):
        ranges = [{"min": 1000, "max": 2000, "type": "test_type"}]
        id_ranges = IdRanges(ranges)

        assert id_ranges.get_type(500) is None
        assert id_ranges.get_type(2500) is None

    def test_get_type_with_multiple_ranges(self):
        ranges = [
            {"min": 1000, "max": 2000, "type": "type1"},
            {"min": 3000, "max": 4000, "type": "type2"},
        ]
        id_ranges = IdRanges(ranges)

        assert id_ranges.get_type(1500) == "type1"
        assert id_ranges.get_type(3500) == "type2"
        assert id_ranges.get_type(2500) is None

    def test_get_type_with_missing_type(self):
        ranges = [{"min": 1000, "max": 2000}]
        id_ranges = IdRanges(ranges)

        assert id_ranges.get_type(1500) is None

    def test_get_type_with_none_values(self):
        ranges = [{"min": None, "max": 2000, "type": "test_type"}]
        id_ranges = IdRanges(ranges)

        assert id_ranges.get_type(1500) is None

        ranges = [{"min": 1000, "max": None, "type": "test_type"}]
        id_ranges = IdRanges(ranges)

        assert id_ranges.get_type(1500) is None

    def test_empty_ranges(self):
        id_ranges = IdRanges([])

        assert id_ranges.contains(1500) is False
        assert id_ranges.get_type(1500) is None
