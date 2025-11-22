import pytest

from domain.deals_service import DealsService
from domain.location_validator import LocationValidator
from domain.orders_service import OrdersService
from .utils_function import MockRepository

@pytest.fixture
def mock_repository():
    """Fixture to create a mock repository"""
    return MockRepository()


@pytest.fixture
def deals_service(mock_repository, local_data_repository, cache):
    """Fixture to create a DealsService with a mock repository"""
    location_validator = LocationValidator(local_data_repository, mock_repository)
    orders_service = OrdersService(mock_repository, location_validator, cache)
    return DealsService(mock_repository, location_validator, orders_service, local_data_repository)

