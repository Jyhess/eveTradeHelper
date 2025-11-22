"""Tests for _collect_types_for_deals method"""

import pytest


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceCollectTypesForDeals:
    """Tests for _collect_types_for_deals method"""

    async def test_collect_types_for_deals_with_top_level_groups(
        self, deals_service, mock_repository, local_data_repository
    ):
        """Test _collect_types_for_deals uses top-level groups when group_id is None using real static data"""
        # When group_id is None, should collect from all top-level groups in static data
        all_types = await deals_service._collect_types_for_deals(group_id=None)

        # Should include types from all top-level groups in static data
        assert len(all_types) > 0, "Should have types from all groups in static data"
        # Verify it uses static data by checking that we have types from known groups
        group_61_types = local_data_repository.get_types_for_group(61, include_children=True)
        group_5_types = local_data_repository.get_types_for_group(5, include_children=True)
        # At least some types from these groups should be included
        assert len(all_types.intersection(group_61_types)) > 0 or len(
            all_types.intersection(group_5_types)
        ) > 0, "Should include types from known market groups in static data"

    async def test_collect_types_for_deals_with_specific_group(
        self, deals_service, mock_repository, local_data_repository
    ):
        """Test _collect_types_for_deals with a specific group_id using real static data"""
        # Use real market group 5 (Standard Frigates) which has children
        group_id = 5
        # Get expected types from static data
        expected_types = local_data_repository.get_types_for_group(group_id, include_children=True)

        # When group_id is specified, should collect from that group and its children
        all_types = await deals_service._collect_types_for_deals(group_id=group_id)

        # Should include types from group and its children (via collect_all_types_from_group)
        assert isinstance(all_types, set)
        assert all_types == expected_types
        assert len(all_types) > 0, "Market group 5 should have types in static data"

