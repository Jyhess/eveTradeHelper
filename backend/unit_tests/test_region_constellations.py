"""
Tests pour les constellations d'une région
"""

import pytest

from domain.region_service import RegionService


@pytest.fixture
def region_service(eve_repository):
    """Fixture pour créer un service de région"""
    from domain.region_data import RegionData
    from domain.types import ConstellationDetails, RegionDetails, SystemDetails

    # Configure mock with test data for The Forge region (10000002)
    region_id = 10000002
    constellation_id = 20000020  # Example constellation in The Forge
    system_id = 30000142  # Jita system

    eve_repository.regions_list = [region_id]
    eve_repository.region_details[region_id] = RegionDetails(
        region_id=region_id,
        name="The Forge",
        description="Test region",
        constellations=[constellation_id],
    )
    eve_repository.constellation_details[constellation_id] = ConstellationDetails(
        constellation_id=constellation_id,
        name="Test Constellation",
        systems=[system_id],
        position={"x": 0, "y": 0, "z": 0},
        region_id=region_id,
    )
    eve_repository.system_details[system_id] = SystemDetails(
        system_id=system_id,
        name="Jita",
        security_status=0.9,
        security_class="B",
        position={"x": 0, "y": 0, "z": 0},
        constellation_id=constellation_id,
        planets=[],
        star_id=40000001,
    )

    region_data = RegionData(eve_repository)
    return RegionService(eve_repository, region_data)


class TestRegionConstellations:
    """Tests pour les constellations d'une région"""

    @pytest.mark.asyncio
    async def test_get_region_constellations_with_details(self, region_service):
        """Test retrieving constellations for a region with proper structure"""
        region_id = 10000002
        result = await region_service.get_region_constellations_with_details(region_id)

        assert isinstance(result, list), "Result must be a list"
        assert len(result) > 0, "List must not be empty"

        # Check structure and types of the first constellation
        first = result[0]
        assert hasattr(first, "constellation_id"), "Constellation must have constellation_id"
        assert hasattr(first, "name"), "Constellation must have name"
        assert hasattr(first, "systems"), "Constellation must have systems list"
        assert isinstance(first.constellation_id, int), "constellation_id must be an int"
        assert isinstance(first.name, str), "name must be a str"
        assert isinstance(first.systems, list), "systems must be a list"

        # Verify all constellations have required attributes
        for constellation in result:
            assert hasattr(
                constellation, "constellation_id"
            ), "Each constellation must have a constellation_id"
            assert hasattr(constellation, "name"), "Each constellation must have a name"
            assert hasattr(
                constellation, "systems"
            ), "Each constellation must have a systems list"
            assert isinstance(constellation.systems, list), "systems must be a list"
