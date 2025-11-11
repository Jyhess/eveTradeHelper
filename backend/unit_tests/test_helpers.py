"""
Unit tests for domain helpers
"""

import pytest

from domain.location_validator import LocationValidator


@pytest.fixture
def location_validator(local_data_repository, eve_repository):
    return LocationValidator(local_data_repository, eve_repository)


@pytest.mark.unit
class TestHelpers:
    """Tests for domain helpers"""

    @pytest.mark.asyncio
    async def test_is_station_with_valid_station(self, location_validator):
        """Test that a valid station ID returns True"""
        # 60008494 is a known valid station
        assert await location_validator.is_station(60008494) is True

    @pytest.mark.asyncio
    async def test_is_station_with_invalid_station(self, location_validator):
        """Test that an invalid station ID (>= threshold but not in static data) returns False"""
        # 1042847222396 is >= threshold but not a valid station
        assert await location_validator.is_station(1042847222396) is False

    @pytest.mark.asyncio
    async def test_is_station_with_system_id(self, location_validator):
        """Test that a system ID returns False"""
        # 30000142 is Jita system ID (not a station)
        assert await location_validator.is_station(30000142) is False

    @pytest.mark.asyncio
    async def test_is_station_with_low_id(self, location_validator):
        """Test that a low ID returns False"""
        assert await location_validator.is_station(1000) is False

    @pytest.mark.asyncio
    async def test_is_station_with_repository_and_invalid_station(self, location_validator):
        """Test that is_station uses API when repository is provided and ID not in static data"""
        # 1042847222396 is >= threshold but not a valid station
        # Should try API and get 400, then cache it as invalid
        result = await location_validator.is_station(1042847222396)
        assert result is False

        # Second call should use cache (no API call)
        result2 = await location_validator.is_station(1042847222396)
        assert result2 is False
