"""
Unit tests for RegionData class
"""

import pytest

from domain.region_data import RegionData
from domain.repository import EveRepository
from domain.types import ConstellationDetails, RegionDetails, SystemDetails


class MockRepository(EveRepository):
    """Mock repository for testing"""

    def __init__(self):
        self.regions = [10000001, 10000002]
        self.constellations_data = {
            20000001: {
                "constellation_id": 20000001,
                "name": "Kimotoro",
                "region_id": 10000001,
                "systems": [30000142, 30000143],
                "position": {},
            },
            20000002: {
                "constellation_id": 20000002,
                "name": "Kimotoro II",
                "region_id": 10000001,
                "systems": [30000144],
                "position": {},
            },
            20000003: {
                "constellation_id": 20000003,
                "name": "Other",
                "region_id": 10000002,
                "systems": [30000145],
                "position": {},
            },
        }
        self.systems_data = {
            30000142: {
                "system_id": 30000142,
                "name": "Jita",
                "constellation_id": 20000001,
                "security_status": 0.9,
                "security_class": "B",
                "position": {},
                "planets": [],
                "star_id": None,
            },
            30000143: {
                "system_id": 30000143,
                "name": "Perimeter",
                "constellation_id": 20000001,
                "security_status": 0.9,
                "security_class": "B",
                "position": {},
                "planets": [],
                "star_id": None,
            },
            30000144: {
                "system_id": 30000144,
                "name": "Jita IV",
                "constellation_id": 20000002,
                "security_status": 0.8,
                "security_class": "B",
                "position": {},
                "planets": [],
                "star_id": None,
            },
            30000145: {
                "system_id": 30000145,
                "name": "Other System",
                "constellation_id": 20000003,
                "security_status": 0.7,
                "security_class": "C",
                "position": {},
                "planets": [],
                "star_id": None,
            },
        }
        self.regions_data = {
            10000001: {
                "region_id": 10000001,
                "name": "The Forge",
                "description": "",
                "constellations": [20000001, 20000002],
            },
            10000002: {
                "region_id": 10000002,
                "name": "Other Region",
                "description": "",
                "constellations": [20000003],
            },
        }

    async def get_regions_list(self):
        return self.regions

    async def get_region_details(self, region_id):
        region_data = self.regions_data.get(
            region_id,
            {"region_id": region_id, "name": "Unknown", "description": "", "constellations": []},
        )
        if isinstance(region_data, dict):
            return RegionDetails.from_dict(region_data)
        return region_data

    async def get_constellation_details(self, constellation_id):
        constellation_data = self.constellations_data.get(
            constellation_id,
            {
                "constellation_id": constellation_id,
                "name": "Unknown",
                "region_id": None,
                "systems": [],
                "position": {},
            },
        )
        if isinstance(constellation_data, dict):
            return ConstellationDetails.from_dict(constellation_data)
        return constellation_data

    async def get_system_details(self, system_id):
        system_data = self.systems_data.get(
            system_id,
            {
                "system_id": system_id,
                "name": "Unknown",
                "constellation_id": None,
                "security_status": 0.0,
                "security_class": "",
                "position": {},
                "planets": [],
                "star_id": None,
            },
        )
        if isinstance(system_data, dict):
            return SystemDetails.from_dict(system_data)
        return system_data

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
def region_data(mock_repository):
    """Fixture to create a RegionData instance"""
    return RegionData(mock_repository)


@pytest.mark.unit
class TestRegionData:
    """Tests for RegionData class"""

    @pytest.mark.asyncio
    async def test_initialize_loads_all_data(self, mock_repository):
        """Test that initialize loads all regions, constellations, and systems"""
        region_data = RegionData(mock_repository)
        await region_data._ensure_initialized()

        assert len(region_data._regions_by_id) == 2
        assert len(region_data._constellations_by_id) == 3
        assert len(region_data._systems_by_id) == 4

    @pytest.mark.asyncio
    async def test_find_region_by_id(self, region_data):
        """Test finding a region by ID"""
        region = await region_data.find_region_by_id(10000001)

        assert region is not None
        assert region["region_id"] == 10000001
        assert region["name"] == "The Forge"

    @pytest.mark.asyncio
    async def test_find_region_by_id_not_found(self, region_data):
        """Test finding a region by ID that doesn't exist"""
        region = await region_data.find_region_by_id(99999999)

        assert region is None

    @pytest.mark.asyncio
    async def test_find_region_by_name(self, region_data):
        """Test finding a region by name"""
        regions = await region_data.find_region_by_name("The Forge")

        assert len(regions) == 1
        assert regions[0]["region_id"] == 10000001
        assert regions[0]["name"] == "The Forge"

    @pytest.mark.asyncio
    async def test_find_region_by_name_case_insensitive(self, region_data):
        """Test that finding region by name is case insensitive"""
        regions_lower = await region_data.find_region_by_name("the forge")
        regions_upper = await region_data.find_region_by_name("THE FORGE")

        assert len(regions_lower) == len(regions_upper) == 1
        assert regions_lower[0]["region_id"] == regions_upper[0]["region_id"]

    @pytest.mark.asyncio
    async def test_find_region_by_name_partial_match(self, region_data):
        """Test finding regions by partial name match"""
        regions = await region_data.find_region_by_name("Forge")

        assert len(regions) == 1
        assert "Forge" in regions[0]["name"]

    @pytest.mark.asyncio
    async def test_find_constellation_by_id(self, region_data):
        """Test finding a constellation by ID"""
        constellation = await region_data.find_constellation_by_id(20000001)

        assert constellation is not None
        assert constellation["constellation_id"] == 20000001
        assert constellation["name"] == "Kimotoro"

    @pytest.mark.asyncio
    async def test_find_constellation_by_id_not_found(self, region_data):
        """Test finding a constellation by ID that doesn't exist"""
        constellation = await region_data.find_constellation_by_id(99999999)

        assert constellation is None

    @pytest.mark.asyncio
    async def test_find_constellation_by_name(self, region_data):
        """Test finding a constellation by name"""
        constellations = await region_data.find_constellation_by_name("Kimotoro")

        assert len(constellations) == 2
        assert all("Kimotoro" in c["name"] for c in constellations)

    @pytest.mark.asyncio
    async def test_find_constellation_by_name_case_insensitive(self, region_data):
        """Test that finding constellation by name is case insensitive"""
        constellations_lower = await region_data.find_constellation_by_name("kimotoro")
        constellations_upper = await region_data.find_constellation_by_name("KIMOTORO")

        assert len(constellations_lower) == len(constellations_upper) == 2

    @pytest.mark.asyncio
    async def test_find_system_by_id(self, region_data):
        """Test finding a system by ID"""
        system = await region_data.find_system_by_id(30000142)

        assert system is not None
        assert system["system_id"] == 30000142
        assert system["name"] == "Jita"

    @pytest.mark.asyncio
    async def test_find_system_by_id_not_found(self, region_data):
        """Test finding a system by ID that doesn't exist"""
        system = await region_data.find_system_by_id(99999999)

        assert system is None

    @pytest.mark.asyncio
    async def test_find_system_by_name(self, region_data):
        """Test finding a system by name"""
        systems = await region_data.find_system_by_name("Jita")

        assert len(systems) == 2
        assert all("Jita" in s["name"] for s in systems)

    @pytest.mark.asyncio
    async def test_find_system_by_name_case_insensitive(self, region_data):
        """Test that finding system by name is case insensitive"""
        systems_lower = await region_data.find_system_by_name("jita")
        systems_upper = await region_data.find_system_by_name("JITA")

        assert len(systems_lower) == len(systems_upper) == 2

    @pytest.mark.asyncio
    async def test_find_system_by_name_partial_match(self, region_data):
        """Test finding systems by partial name match"""
        systems = await region_data.find_system_by_name("Peri")

        assert len(systems) == 1
        assert systems[0]["name"] == "Perimeter"
