"""
Domain types package
Concrete types to replace dictionaries in method parameters and return values
"""

from .adjacent_region import AdjacentRegion
from .constellation_details import ConstellationDetails
from .constellation_search_result import ConstellationSearchResult
from .contraband_system import ContrabandSystem
from .deal import Deal
from .enriched_market_orders import EnrichedMarketOrders
from .enriched_order import EnrichedOrder
from .item_type import ItemType
from .item_type_search_result import ItemTypeSearchResult
from .market_category import MarketCategory
from .market_deals_result import MarketDealsResult
from .market_group_details import MarketGroupDetails
from .order import Order
from .region_details import RegionDetails
from .route_detail import RouteDetail
from .stargate_details import StargateDetails
from .station_details import StationDetails
from .system_connection import SystemConnection
from .system_details import SystemDetails
from .system_map_connection import SystemMapConnection
from .system_map_system import SystemMapSystem
from .system_search_result import SystemSearchResult
from .system_to_system_deals_result import SystemToSystemDealsResult
from .systems_within_jumps_result import SystemsWithinJumpsResult
from .type_price_by_region import TypePriceByRegion

__all__ = [
    "AdjacentRegion",
    "ConstellationDetails",
    "ConstellationSearchResult",
    "ContrabandSystem",
    "Deal",
    "EnrichedMarketOrders",
    "EnrichedOrder",
    "ItemType",
    "ItemTypeSearchResult",
    "MarketCategory",
    "MarketDealsResult",
    "MarketGroupDetails",
    "Order",
    "RegionDetails",
    "RouteDetail",
    "StargateDetails",
    "StationDetails",
    "SystemConnection",
    "SystemDetails",
    "SystemMapConnection",
    "SystemMapSystem",
    "SystemSearchResult",
    "SystemToSystemDealsResult",
    "SystemsWithinJumpsResult",
    "TypePriceByRegion",
]
