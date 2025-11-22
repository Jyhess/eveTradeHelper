import pytest

from domain.types import ItemType


@pytest.mark.asyncio
@pytest.mark.unit
class TestMarketServiceTypeSearch:
    async def test_search_item_types_by_name(self, market_service_with_type_search):
        results = await market_service_with_type_search.search_item_types("tri")

        assert len(results) == 2
        assert results[0].type_id == 34
        assert results[0].name == "Tritanium"

    async def test_search_item_types_by_id(
        self, market_service_with_type_search, mock_repository
    ):
        type_id = 987654

        async def fake_get_item_type(requested_id: int) -> ItemType:
            if requested_id == type_id:
                return ItemType.from_dict(
                    {"type_id": type_id, "name": "Custom Item", "volume": 0.0}
                )
            return ItemType.from_dict({"type_id": requested_id, "name": "Unknown", "volume": 0.0})

        mock_repository.get_item_type = fake_get_item_type

        results = await market_service_with_type_search.search_item_types(str(type_id))

        assert len(results) == 1
        assert results[0].type_id == type_id
        assert results[0].name == "Custom Item"

    async def test_search_item_types_empty_query(self, market_service_with_type_search):
        results = await market_service_with_type_search.search_item_types("  ")

        # Empty query should return all types (limited by default limit)
        assert isinstance(results, list)
        assert len(results) > 0

    async def test_search_item_types_no_query(self, market_service_with_type_search):
        results = await market_service_with_type_search.search_item_types(None)

        # No query should return all types (limited by default limit)
        assert isinstance(results, list)
        assert len(results) > 0

