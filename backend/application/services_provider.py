from typing import Optional
from domain import Services, DealsService, MarketService, RegionService

from fastapi import HTTPException

class ServicesProvider:
    _services: Optional[Services] = None

    @classmethod
    def set_services(cls, services):
        cls._services = services

    @classmethod
    def get_deals_service(cls) -> DealsService:
        if cls._services is None or cls._services.deals_service is None:
            raise HTTPException(status_code=503, detail="DealsService non initialized")
        return cls._services.deals_service

    @classmethod
    def get_market_service(cls) -> MarketService:
        if cls._services is None or cls._services.market_service is None:
            raise HTTPException(status_code=503, detail="MarketService non initialized")
        return cls._services.market_service

    @classmethod
    def get_region_service(cls) -> RegionService:
        if cls._services is None or cls._services.region_service is None:
            raise HTTPException(status_code=503, detail="RegionService non initialized")
        return cls._services.region_service
