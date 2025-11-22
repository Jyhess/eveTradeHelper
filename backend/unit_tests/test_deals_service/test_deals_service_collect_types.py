"""Tests for collecting types from market groups"""

import pytest


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceCollectTypes:
    """Tests for collecting types from a group"""

    async def test_collect_all_types_from_simple_group(
        self, mock_repository, deals_service, local_data_repository
    ):
        """Test with a simple group without subgroups using real static data"""
        # Use real market group 61 (Caldari Frigates) which has types and no children
        group_id = 61
        # Get expected types from static data
        expected_types = local_data_repository.get_types_for_group(group_id, include_children=False)

        # Verify we have types in this group
        assert len(expected_types) > 0, "Market group 61 should have types in static data"

        # Execute
        result = deals_service.collect_all_types_from_group(group_id)

        # Verify
        # The @cached decorator returns a list, convert it to Set for comparison
        if isinstance(result, list):
            result = set(result)
        assert isinstance(result, set)
        assert result == expected_types

    async def test_collect_all_types_from_group_with_children(
        self, mock_repository, deals_service, local_data_repository
    ):
        """Test with a group having subgroups using real static data"""
        # Use real market group 5 (Standard Frigates) which has children (61, 64, 72, 77, etc.)
        group_id = 5
        # Get expected types from static data (including children)
        expected_types = local_data_repository.get_types_for_group(group_id, include_children=True)

        # Verify we have types in this group or its children
        assert len(expected_types) > 0, "Market group 5 should have types in static data"

        # Execute
        result = deals_service.collect_all_types_from_group(group_id)

        # Verify: should include types from parent and children
        # The @cached decorator returns a list, convert it to Set for comparison
        if isinstance(result, list):
            result = set(result)
        assert isinstance(result, set)
        assert result == expected_types

    async def test_collect_all_types_from_nested_groups(
        self, mock_repository, deals_service, local_data_repository
    ):
        """Test with nested groups on multiple levels using real static data"""
        # Use real market group 9 (Ship Equipment) which has nested children
        # Group 9 -> Group 10 (Turrets & Launchers), Group 14 (Hull & Armor), etc.
        group_id = 9
        # Get expected types from static data (including all nested children)
        expected_types = local_data_repository.get_types_for_group(group_id, include_children=True)

        # Verify we have types in this group or its nested children
        assert len(expected_types) > 0, "Market group 9 should have types in static data"

        # Execute
        result = deals_service.collect_all_types_from_group(group_id)

        # Verify: should include all types from all levels
        # The @cached decorator returns a list, convert it to Set for comparison
        if isinstance(result, list):
            result = set(result)
        assert isinstance(result, set)
        assert result == expected_types

    async def test_collect_all_types_from_unknown_group(
        self, mock_repository, deals_service
    ):
        """Test with a non-existent group"""
        # Use a very large ID that doesn't exist in static data
        unknown_group_id = 99999999

        # Execute
        result = deals_service.collect_all_types_from_group(unknown_group_id)

        # Verify: should return an empty set
        # The @cached decorator returns a list, convert it to Set for comparison
        if isinstance(result, list):
            result = set(result)
        assert isinstance(result, set)
        assert len(result) == 0

    async def test_collect_all_types_from_group_without_types(
        self, mock_repository, deals_service, local_data_repository
    ):
        """Test with a group without direct types (only subgroups) using real static data"""
        # Use real market group 5 (Standard Frigates) which has no direct types but has children
        group_id = 5
        # Get expected types from static data (should include types from children only)
        expected_types = local_data_repository.get_types_for_group(group_id, include_children=True)

        # Verify we have types from children
        assert len(expected_types) > 0, "Market group 5 should have types from children in static data"

        # Execute
        result = deals_service.collect_all_types_from_group(group_id)

        # Verify: should include only types from children
        # The @cached decorator returns a list, convert it to Set for comparison
        if isinstance(result, list):
            result = set(result)
        assert isinstance(result, set)
        assert result == expected_types

