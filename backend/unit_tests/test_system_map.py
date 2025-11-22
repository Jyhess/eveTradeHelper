"""
Unit tests for system map functionality
"""

import pytest

from domain.constants import DEFAULT_MAX_JUMPS
from domain.region_service import RegionService


@pytest.fixture
def region_service(eve_repository):
    from domain.region_data import RegionData

    region_data = RegionData(eve_repository)
    return RegionService(eve_repository, region_data)


class TestSystemMap:
    @pytest.mark.asyncio
    async def test_get_systems_within_jumps_returns_source_system(self, region_service):
        """Test that the source system is included in the result"""
        system_id = 30000142  # Jita system
        max_jumps = DEFAULT_MAX_JUMPS

        result = await region_service.get_systems_within_jumps(system_id, max_jumps)

        assert hasattr(result, "systems"), "Result must contain 'systems' attribute"
        assert hasattr(result, "connections"), "Result must contain 'connections' attribute"

        systems = result.systems
        assert isinstance(systems, list), "Systems must be a list"
        assert len(systems) > 0, "Result must contain at least the source system"

        source_system = next((s for s in systems if s.system_id == system_id), None)
        assert source_system is not None, "Source system must be included in result"
        assert source_system.name is not None, "Source system must have a name"

    @pytest.mark.asyncio
    async def test_get_systems_within_jumps_includes_connected_systems(self, region_service):
        """Test that directly connected systems are included"""
        system_id = 30000142  # Jita system
        max_jumps = 1

        result = await region_service.get_systems_within_jumps(system_id, max_jumps)

        systems = result.systems
        connections = result.connections

        assert (
            len(systems) > 1
        ), "Result must contain source system and at least one connected system"
        assert len(connections) > 0, "Result must contain at least one connection"

        for connection in connections:
            assert hasattr(connection, "from_system_id"), "Connection must have 'from_system_id'"
            assert hasattr(connection, "to_system_id"), "Connection must have 'to_system_id'"
            assert connection.from_system_id in [
                s.system_id for s in systems
            ], "From system must be in systems list"
            assert connection.to_system_id in [
                s.system_id for s in systems
            ], "To system must be in systems list"

    @pytest.mark.asyncio
    async def test_get_systems_within_jumps_respects_max_jumps(self, region_service):
        """Test that max_jumps parameter is respected"""
        system_id = 30000142  # Jita system
        max_jumps = 2

        result = await region_service.get_systems_within_jumps(system_id, max_jumps)

        systems = result.systems

        assert len(systems) > 0, "Result must contain systems"

        for system in systems:
            assert hasattr(system, "system_id"), "System must have system_id"
            assert hasattr(system, "name"), "System must have name"
            assert hasattr(system, "jumps"), "System must have jumps count"
            assert isinstance(system.jumps, int), "Jumps must be an integer"
            assert (
                system.jumps <= max_jumps
            ), f"System jumps ({system.jumps}) must not exceed max_jumps ({max_jumps})"

    @pytest.mark.asyncio
    async def test_get_systems_within_jumps_default_max_jumps(self, region_service):
        """Test that default max_jumps is used when not specified"""
        system_id = 30000142  # Jita system

        result = await region_service.get_systems_within_jumps(system_id)

        systems = result.systems

        for system in systems:
            assert (
                system.jumps <= DEFAULT_MAX_JUMPS
            ), f"System jumps must not exceed default max_jumps ({DEFAULT_MAX_JUMPS})"

    @pytest.mark.asyncio
    async def test_get_systems_within_jumps_system_structure(self, region_service):
        """Test that each system has the required structure"""
        system_id = 30000142  # Jita system
        max_jumps = 1

        result = await region_service.get_systems_within_jumps(system_id, max_jumps)

        systems = result.systems

        for system in systems:
            assert hasattr(system, "system_id"), "System must have system_id"
            assert hasattr(system, "name"), "System must have name"
            assert hasattr(system, "security_status"), "System must have security_status"
            assert hasattr(system, "jumps"), "System must have jumps"
            assert isinstance(system.system_id, int), "system_id must be an integer"
            assert isinstance(system.name, str), "name must be a string"
            assert isinstance(
                system.security_status, int | float
            ), "security_status must be a number"
            assert isinstance(system.jumps, int), "jumps must be an integer"
