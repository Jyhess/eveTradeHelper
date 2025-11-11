from repositories.local_data import LocalDataRepository

from .deals_service import DealsService
from .location_validator import LocationValidator
from .market_service import MarketService
from .orders_service import OrdersService
from .region_service import RegionService
from .repository import EveRepository


class Services:
    def __init__(self, eve_repository: EveRepository, local_data_repository: LocalDataRepository):
        location_validator = LocationValidator(local_data_repository, eve_repository)
        # Create shared OrdersService instance for cache sharing
        orders_service = OrdersService(eve_repository, location_validator)
        self.region_service = RegionService(eve_repository)
        self.deals_service = DealsService(eve_repository, location_validator, orders_service)
        self.market_service = MarketService(eve_repository, location_validator, orders_service)
