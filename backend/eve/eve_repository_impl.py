"""
Implémentation du repository Eve utilisant EveAPIClient (version asynchrone)
"""

import logging
from typing import Any

from domain.repository import EveRepository

from .eve_api_client import EveAPIClient

logger = logging.getLogger(__name__)


class EveRepositoryImpl(EveRepository):
    """Implémentation concrète du repository Eve utilisant l'API client (asynchrone)"""

    def __init__(self, api_client: EveAPIClient):
        """
        Initialise le repository avec un client API

        Args:
            api_client: Instance de EveAPIClient
        """
        self.api_client = api_client

    async def close(self):
        await self.api_client.close()

    async def get_regions_list(self) -> list[int]:
        """Récupère la liste des IDs de régions"""
        return await self.api_client.get_regions_list()

    async def get_region_details(self, region_id: int) -> dict[str, Any]:
        """Récupère les détails d'une région"""
        return await self.api_client.get_region_details(region_id)

    async def get_constellation_details(self, constellation_id: int) -> dict[str, Any]:
        """Récupère les détails d'une constellation"""
        return await self.api_client.get_constellation_details(constellation_id)

    async def get_system_details(self, system_id: int) -> dict[str, Any]:
        """Récupère les détails d'un système solaire"""
        return await self.api_client.get_system_details(system_id)

    async def get_item_type(self, type_id: int) -> dict[str, Any]:
        """Récupère les informations d'un type d'item"""
        return await self.api_client.get_item_type(type_id)

    async def get_stargate_details(self, stargate_id: int) -> dict[str, Any]:
        """Récupère les détails d'une stargate"""
        return await self.api_client.get_stargate_details(stargate_id)

    async def get_station_details(self, station_id: int) -> dict[str, Any]:
        """Récupère les détails d'une station"""
        return await self.api_client.get_station_details(station_id)

    async def get_market_groups_list(self) -> list[int]:
        """Récupère la liste des IDs de groupes de marché"""
        return await self.api_client.get_market_groups_list()

    async def get_market_group_details(self, group_id: int) -> dict[str, Any]:
        """Récupère les détails d'un groupe de marché"""
        return await self.api_client.get_market_group_details(group_id)

    async def get_market_orders(
        self, region_id: int, type_id: int | None = None
    ) -> list[dict[str, Any]]:
        """Récupère les ordres de marché pour une région, optionnellement filtrés par type"""
        return await self.api_client.get_market_orders(region_id, type_id)

    async def get_route(self, origin: int, destination: int) -> list[int]:
        """Calcule la route entre deux systèmes"""
        return await self.api_client.get_route(origin, destination)

    async def get_route_with_details(self, origin: int, destination: int) -> list[dict[str, Any]]:
        """Calcule la route entre deux systèmes avec les détails de sécurité"""
        import asyncio

        # Obtenir la liste des IDs de systèmes de la route
        route_ids = await self.api_client.get_route(origin, destination)

        if not route_ids:
            return []

        # Récupérer les détails de chaque système en parallèle
        async def fetch_system_details(system_id: int) -> dict[str, Any]:
            try:
                system_data = await self.api_client.get_system_details(system_id)
                return {
                    "system_id": system_id,
                    "name": system_data.get("name", f"Système {system_id}"),
                    "security_status": system_data.get("security_status", 0.0),
                }
            except Exception as e:
                logger.warning(f"Erreur lors de la récupération du système {system_id}: {e}")
                return {
                    "system_id": system_id,
                    "name": f"Système {system_id}",
                    "security_status": 0.0,
                }

        # Récupérer tous les détails en parallèle
        results = await asyncio.gather(*[fetch_system_details(sid) for sid in route_ids])

        return results
