"""
Implémentation du repository Eve utilisant EveAPIClient (version asynchrone)
"""

from typing import List, Dict, Any
from domain.repository import EveRepository
from eve.api_client import EveAPIClient


class EveRepositoryImpl(EveRepository):
    """Implémentation concrète du repository Eve utilisant l'API client (asynchrone)"""

    def __init__(self, api_client: EveAPIClient):
        """
        Initialise le repository avec un client API

        Args:
            api_client: Instance de EveAPIClient
        """
        self.api_client = api_client

    async def get_regions_list(self) -> List[int]:
        """Récupère la liste des IDs de régions"""
        return await self.api_client.get_regions_list()

    async def get_region_details(self, region_id: int) -> Dict[str, Any]:
        """Récupère les détails d'une région"""
        return await self.api_client.get_region_details(region_id)

    async def get_constellation_details(self, constellation_id: int) -> Dict[str, Any]:
        """Récupère les détails d'une constellation"""
        return await self.api_client.get_constellation_details(constellation_id)

    async def get_system_details(self, system_id: int) -> Dict[str, Any]:
        """Récupère les détails d'un système solaire"""
        return await self.api_client.get_system_details(system_id)

    async def get_item_type(self, type_id: int) -> Dict[str, Any]:
        """Récupère les informations d'un type d'item"""
        return await self.api_client.get_item_type(type_id)

    async def get_stargate_details(self, stargate_id: int) -> Dict[str, Any]:
        """Récupère les détails d'une stargate"""
        return await self.api_client.get_stargate_details(stargate_id)

    async def get_station_details(self, station_id: int) -> Dict[str, Any]:
        """Récupère les détails d'une station"""
        return await self.api_client.get_station_details(station_id)

    async def get_market_groups_list(self) -> List[int]:
        """Récupère la liste des IDs de groupes de marché"""
        return await self.api_client.get_market_groups_list()

    async def get_market_group_details(self, group_id: int) -> Dict[str, Any]:
        """Récupère les détails d'un groupe de marché"""
        return await self.api_client.get_market_group_details(group_id)

    async def get_market_orders(
        self, region_id: int, type_id: int = None
    ) -> List[Dict[str, Any]]:
        """Récupère les ordres de marché pour une région, optionnellement filtrés par type"""
        return await self.api_client.get_market_orders(region_id, type_id)