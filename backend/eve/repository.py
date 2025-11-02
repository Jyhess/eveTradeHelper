"""
Implémentation du repository Eve utilisant EveAPIClient
"""

from typing import List, Dict, Any
from domain.repository import EveRepository
from eve.api_client import EveAPIClient


class EveRepositoryImpl(EveRepository):
    """Implémentation concrète du repository Eve utilisant l'API client"""

    def __init__(self, api_client: EveAPIClient):
        """
        Initialise le repository avec un client API

        Args:
            api_client: Instance de EveAPIClient
        """
        self.api_client = api_client

    def get_regions_list(self) -> List[int]:
        """Récupère la liste des IDs de régions"""
        return self.api_client.get_regions_list()

    def get_region_details(self, region_id: int) -> Dict[str, Any]:
        """Récupère les détails d'une région"""
        return self.api_client.get_region_details(region_id)

    def get_constellation_details(self, constellation_id: int) -> Dict[str, Any]:
        """Récupère les détails d'une constellation"""
        return self.api_client.get_constellation_details(constellation_id)

    def get_system_details(self, system_id: int) -> Dict[str, Any]:
        """Récupère les détails d'un système solaire"""
        return self.api_client.get_system_details(system_id)

    def get_item_type(self, type_id: int) -> Dict[str, Any]:
        """Récupère les informations d'un type d'item"""
        return self.api_client.get_item_type(type_id)

    def get_stargate_details(self, stargate_id: int) -> Dict[str, Any]:
        """Récupère les détails d'une stargate"""
        return self.api_client.get_stargate_details(stargate_id)

