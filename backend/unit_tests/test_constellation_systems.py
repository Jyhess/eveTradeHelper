import pytest

from domain.region_service import RegionService


@pytest.fixture
def region_service(eve_repository):
    from domain.region_data import RegionData

    region_data = RegionData(eve_repository)
    return RegionService(eve_repository, region_data)


class TestConstellationSystems:
    @pytest.mark.asyncio
    async def test_get_constellation_systems_with_details(self, region_service):
        # Use a known constellation (first constellation of The Forge)
        # First retrieve the constellations of the region
        region_id = 10000002
        constellations = await region_service.get_region_constellations_with_details(region_id)

        assert len(constellations) > 0, "Region must have at least one constellation"
        constellation_id = constellations[0].constellation_id

        # Retrieve the systems of this constellation
        result = await region_service.get_constellation_systems_with_details(constellation_id)

        # Basic checks
        assert isinstance(result, list), "Result must be a list"
        assert len(result) > 0, "Constellation must have at least one system"

        for system in result:
            assert hasattr(system, "system_id"), "Each system must have a system_id"
            assert hasattr(system, "name"), "Each system must have a name"
            assert hasattr(
                system, "security_status"
            ), "Each system must have a security_status"

    @pytest.mark.asyncio
    async def test_get_constellation_systems_structure(self, region_service):
        # Retrieve a constellation for testing
        region_id = 10000002
        constellations = await region_service.get_region_constellations_with_details(region_id)

        if not constellations:
            pytest.skip("No constellation available for test")

        constellation_id = constellations[0].constellation_id
        result = await region_service.get_constellation_systems_with_details(constellation_id)

        assert len(result) > 0, "Constellation must have at least one system"

        # Check the structure of the first element
        first = result[0]
        assert hasattr(first, "system_id"), "System must have system_id attribute"
        assert hasattr(first, "name"), "System must have name attribute"
        assert hasattr(first, "security_status"), "System must have security_status attribute"
        assert isinstance(first.system_id, int), "system_id must be an int"
        assert isinstance(first.name, str), "name must be a str"
        assert isinstance(
            first.security_status, (int, float)
        ), "security_status must be an int or float"
        # security_status must be between -1.0 and 1.0
        assert -1.0 <= first.security_status <= 1.0, "security_status must be between -1.0 and 1.0"
