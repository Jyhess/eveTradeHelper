"""
Unit tests for RegionService search methods
"""

import pytest

from domain.region_data import RegionData
from domain.region_service import RegionService
from domain.repository import EveRepository


class MockRepository(EveRepository):
    """Mock repository for testing"""

    def __init__(self):
        self.regions = [10000001, 10000002]
        self.constellations_data = {
            20000001: {"name": "Kimotoro", "region_id": 10000001, "systems": [30000142, 30000143]},
            20000002: {
                "name": "Kimotoro II",
                "region_id": 10000001,
                "systems": [30000144],
            },
            20000003: {"name": "Other", "region_id": 10000002, "systems": [30000145]},
        }
        self.systems_data = {
            30000142: {
                "name": "Jita",
                "constellation_id": 20000001,
                "security_status": 0.9,
                "security_class": "B",
            },
            30000143: {
                "name": "Perimeter",
                "constellation_id": 20000001,
                "security_status": 0.9,
                "security_class": "B",
            },
            30000144: {
                "name": "Jita IV",
                "constellation_id": 20000002,
                "security_status": 0.8,
                "security_class": "B",
            },
            30000145: {
                "name": "Other System",
                "constellation_id": 20000003,
                "security_status": 0.7,
                "security_class": "C",
            },
        }
        self.regions_data = {
            10000001: {"constellations": [20000001, 20000002]},
            10000002: {"constellations": [20000003]},
        }

    async def get_regions_list(self):
        return self.regions

    async def get_region_details(self, region_id):
        return self.regions_data.get(region_id, {"constellations": []})

    async def get_constellation_details(self, constellation_id):
        return self.constellations_data.get(
            constellation_id, {"name": "Unknown", "region_id": None, "systems": []}
        )

    async def get_system_details(self, system_id):
        return self.systems_data.get(
            system_id,
            {
                "name": "Unknown",
                "constellation_id": None,
                "security_status": 0.0,
                "security_class": "",
            },
        )

    async def get_item_type(self, type_id):
        return {}

    async def get_stargate_details(self, stargate_id):
        return {}

    async def get_station_details(self, station_id):
        return {}

    async def get_market_groups_list(self):
        return []

    async def get_market_group_details(self, group_id):
        return {}

    async def get_market_orders(self, region_id, type_id=None):
        return []

    async def get_route(self, origin, destination):
        return []

    async def get_route_with_details(self, origin, destination):
        return []


@pytest.fixture
def mock_repository():
    return MockRepository()


@pytest.fixture
def region_service_with_mock(mock_repository):
    region_data = RegionData(mock_repository)
    return RegionService(mock_repository, region_data)


@pytest.mark.unit
class TestRegionServiceSearch:
    """Tests for RegionService search methods"""

    @pytest.mark.asyncio
    async def test_search_systems_with_name_filter(self, region_service_with_mock):
        """Test that search_systems filters systems by name"""
        result = await region_service_with_mock.search_systems(name_filter="Jita")

        assert len(result) == 2
        assert all("Jita" in system["name"] for system in result)
        assert all("system_id" in system for system in result)
        assert all("name" in system for system in result)
        assert all("constellation_id" in system for system in result)
        assert all("region_id" in system for system in result)

    @pytest.mark.asyncio
    async def test_search_systems_without_filter_returns_all(self, region_service_with_mock):
        """Test that search_systems returns all systems when no filter is provided"""
        result = await region_service_with_mock.search_systems()

        assert len(result) == 4
        assert all("system_id" in system for system in result)
        assert all("name" in system for system in result)

    @pytest.mark.asyncio
    async def test_search_systems_case_insensitive(self, region_service_with_mock):
        """Test that search_systems is case insensitive"""
        result_lower = await region_service_with_mock.search_systems(name_filter="jita")
        result_upper = await region_service_with_mock.search_systems(name_filter="JITA")

        assert len(result_lower) == len(result_upper)
        assert len(result_lower) == 2

    @pytest.mark.asyncio
    async def test_search_constellations_with_name_filter(self, region_service_with_mock):
        """Test that search_constellations filters constellations by name"""
        result = await region_service_with_mock.search_constellations(name_filter="Kimotoro")

        assert len(result) == 2
        assert all("Kimotoro" in constellation["name"] for constellation in result)
        assert all("constellation_id" in constellation for constellation in result)
        assert all("name" in constellation for constellation in result)
        assert all("region_id" in constellation for constellation in result)

    @pytest.mark.asyncio
    async def test_search_constellations_without_filter_returns_all(self, region_service_with_mock):
        """Test that search_constellations returns all constellations when no filter is provided"""
        result = await region_service_with_mock.search_constellations()

        assert len(result) == 3
        assert all("constellation_id" in constellation for constellation in result)
        assert all("name" in constellation for constellation in result)

    @pytest.mark.asyncio
    async def test_search_constellations_case_insensitive(self, region_service_with_mock):
        """Test that search_constellations is case insensitive"""
        result_lower = await region_service_with_mock.search_constellations(name_filter="kimotoro")
        result_upper = await region_service_with_mock.search_constellations(name_filter="KIMOTORO")

        assert len(result_lower) == len(result_upper)
        assert len(result_lower) == 2
