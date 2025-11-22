"""
Conftest for market service tests
Defines fixtures for market service tests
"""

import pytest

from domain.location_validator import LocationValidator
from domain.market_service import MarketService
from domain.orders_service import OrdersService
from unit_tests.test_market_service.test_market_service_fixtures import (
    FakeLocalDataRepository,
    MockRepository,
)


@pytest.fixture
def mock_repository():
    """Fixture to create a mock repository"""
    return MockRepository()


@pytest.fixture
def market_service(mock_repository, local_data_repository):
    """Fixture to create a MarketService with a mock repository"""
    location_validator = LocationValidator(local_data_repository, mock_repository)
    orders_service = OrdersService(mock_repository, location_validator)
    return MarketService(
        mock_repository,
        location_validator,
        orders_service,
        local_data_repository,
    )


@pytest.fixture
def fake_local_data_repository():
    """Fixture to create a fake local data repository for type search tests"""
    return FakeLocalDataRepository()


@pytest.fixture
def market_service_with_type_search(
    mock_repository, local_data_repository, fake_local_data_repository
):
    """Fixture to create a MarketService with fake type search data"""
    location_validator = LocationValidator(local_data_repository, mock_repository)
    orders_service = OrdersService(mock_repository, location_validator)
    return MarketService(
        mock_repository,
        location_validator,
        orders_service,
        fake_local_data_repository,
    )
