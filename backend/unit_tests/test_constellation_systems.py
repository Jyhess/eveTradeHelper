import pytest

from domain.region_service import RegionService
from domain.types import ConstellationDetails, RegionDetails, SystemDetails


@pytest.fixture
def region_service(eve_repository):
    from domain.region_data import RegionData

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


class TestConstellationSystems:
    @pytest.mark.asyncio
    async def test_get_constellation_systems_with_details(self, region_service):
        """Test retrieving systems for a constellation with proper structure"""
        region_id = 10000002
        constellations = await region_service.get_region_constellations_with_details(region_id)

        assert len(constellations) > 0, "Region must have at least one constellation"
        constellation_id = constellations[0].constellation_id

        result = await region_service.get_constellation_systems_with_details(constellation_id)

        assert isinstance(result, list), "Result must be a list"
        assert len(result) > 0, "Constellation must have at least one system"

        # Check structure and types of the first system
        first = result[0]
        assert hasattr(first, "system_id"), "System must have system_id attribute"
        assert hasattr(first, "name"), "System must have name attribute"
        assert hasattr(first, "security_status"), "System must have security_status attribute"
        assert isinstance(first.system_id, int), "system_id must be an int"
        assert isinstance(first.name, str), "name must be a str"
        assert isinstance(
            first.security_status, int | float
        ), "security_status must be an int or float"
        assert -1.0 <= first.security_status <= 1.0, "security_status must be between -1.0 and 1.0"

        # Verify all systems have required attributes
        for system in result:
            assert hasattr(system, "system_id"), "Each system must have a system_id"
            assert hasattr(system, "name"), "Each system must have a name"
            assert hasattr(system, "security_status"), "Each system must have a security_status"
