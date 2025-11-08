from .deals_service import DealsService
from .market_service import MarketService
from .region_service import RegionService
from .repository import EveRepository


class Services:
    def __init__(self, eve_repository: EveRepository):
        self.region_service = RegionService(eve_repository)
        self.deals_service = DealsService(eve_repository)
        self.market_service = MarketService(eve_repository)
