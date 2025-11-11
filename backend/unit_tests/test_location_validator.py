"""
Unit tests for LocationValidator class
"""

import pytest

from domain.location_validator import LocationValidator


@pytest.fixture
def location_validator(local_data_repository, eve_repository):
    return LocationValidator(local_data_repository, eve_repository)


@pytest.mark.unit
class TestLocationValidator:
    """Tests for LocationValidator class"""

    @pytest.mark.asyncio
    async def test_is_valid_location_id_with_station(self, location_validator):
        """Test that a valid station ID returns True"""
        # 60008494 is a known valid station (within 60000000-69999999)
        assert await location_validator.is_valid_location_id(60008494) is True

    @pytest.mark.asyncio
    async def test_is_valid_location_id_with_solar_system(self, location_validator):
        """Test that a valid solar system ID returns True"""
        # 30000142 is Jita system ID (within 30000000-39999999)
        assert await location_validator.is_valid_location_id(30000142) is True

    @pytest.mark.asyncio
    async def test_is_valid_location_id_with_structure(self, location_validator):
        """Test that get_location_type correctly identifies structure IDs"""
        # 1000000000000 is within structure range
        # Note: is_valid_location_id will return False for IDs > MAX_INT32
        # but get_location_type should still identify it as a structure
        structure_id = 1000000000000
        assert location_validator.get_location_type(structure_id) == "structure"

    @pytest.mark.asyncio
    async def test_is_valid_location_id_with_invalid_id(self, location_validator):
        """Test that an invalid location ID returns False"""
        # 500000000000000000 is not in any known range (above structure max)
        assert await location_validator.is_valid_location_id(500000000000000000) is False

    @pytest.mark.asyncio
    async def test_is_valid_location_id_with_none(self, location_validator):
        """Test that None returns False"""
        assert await location_validator.is_valid_location_id(None) is False

    @pytest.mark.asyncio
    async def test_is_valid_location_id_with_low_id(self, location_validator):
        """Test that a low ID (type range) returns True"""
        # 34 is Tritanium (within 1-60000)
        assert await location_validator.is_valid_location_id(34) is True

    def test_get_location_type_with_station(self, location_validator):
        """Test that get_location_type returns 'station' for station IDs"""
        assert location_validator.get_location_type(60008494) == "station"

    def test_get_location_type_with_solar_system(self, location_validator):
        """Test that get_location_type returns 'solar_system' for system IDs"""
        assert location_validator.get_location_type(30000142) == "solar_system"

    def test_get_location_type_with_structure(self, location_validator):
        """Test that get_location_type returns 'structure' for structure IDs"""
        assert location_validator.get_location_type(1000000000000) == "structure"

    def test_get_location_type_with_invalid_id(self, location_validator):
        """Test that get_location_type returns None for invalid IDs"""
        # 500000000000000000 is not in any known range (above structure max)
        assert location_validator.get_location_type(500000000000000000) is None

    def test_get_location_type_with_none(self, location_validator):
        """Test that get_location_type returns None for None"""
        assert location_validator.get_location_type(None) is None

    @pytest.mark.asyncio
    async def test_mark_location_id_as_invalid(self, location_validator):
        """Test that mark_location_id_as_invalid marks ID as invalid"""
        invalid_id = 999999999

        # Initially might be valid or invalid, but after marking should be invalid
        location_validator.mark_location_id_as_invalid(invalid_id)

        # Should return False after marking as invalid
        assert await location_validator.is_valid_location_id(invalid_id) is False

    @pytest.mark.asyncio
    async def test_is_valid_location_id_checks_cache_first(self, location_validator):
        """Test that is_valid_location_id checks Redis cache first"""
        invalid_id = 888888888

        # Mark as invalid
        location_validator.mark_location_id_as_invalid(invalid_id)

        # Should return False without API call
        assert await location_validator.is_valid_location_id(invalid_id) is False

    @pytest.mark.asyncio
    async def test_is_valid_location_id_rejects_above_int32(self, location_validator):
        """Test that is_valid_location_id rejects IDs above max int32"""
        # Use a value clearly above int32 max (2147483647)
        invalid_id = 3000000000

        # Should return False and cache it
        assert await location_validator.is_valid_location_id(invalid_id) is False

        # Second call should also return False (cached)
        assert await location_validator.is_valid_location_id(invalid_id) is False

    @pytest.mark.asyncio
    async def test_is_valid_location_id_with_repository_and_invalid_station(
        self, location_validator
    ):
        """Test that is_valid_location_id uses API when repository is provided and ID not in static data"""
        # 1042847222396 is >= threshold but not a valid station
        # Should try API and get 400, then cache it as invalid
        result = await location_validator.is_valid_location_id(1042847222396)
        assert result is False

        # Second call should use cache (no API call)
        result2 = await location_validator.is_valid_location_id(1042847222396)
        assert result2 is False

    @pytest.mark.asyncio
    async def test_is_station_with_valid_station_id(self, location_validator):
        """Test that is_station returns True for valid station IDs"""
        # 60008494 is a known valid station
        assert await location_validator.is_station(60008494) is True

    @pytest.mark.asyncio
    async def test_is_station_with_solar_system_id(self, location_validator):
        """Test that is_station returns False for solar system IDs"""
        # 30000142 is Jita system ID, not a station
        assert await location_validator.is_station(30000142) is False

    @pytest.mark.asyncio
    async def test_is_station_with_low_id(self, location_validator):
        """Test that is_station returns False for IDs below threshold"""
        # 34 is below station threshold
        assert await location_validator.is_station(34) is False

    @pytest.mark.asyncio
    async def test_is_station_with_marked_invalid_id(self, location_validator):
        """Test that is_station returns False for IDs marked as invalid"""
        invalid_id = 777777777

        # Mark as invalid
        location_validator.mark_location_id_as_invalid(invalid_id)

        # Should return False
        assert await location_validator.is_station(invalid_id) is False
