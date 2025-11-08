"""
Service de domaine pour la gestion des marchés
Contient la logique métier pure, indépendante de l'infrastructure (version asynchrone)
"""

import asyncio
import logging
from typing import Any

from .constants import DEFAULT_MARKET_ORDERS_LIMIT
from .helpers import is_station
from .repository import EveRepository

logger = logging.getLogger(__name__)


class MarketService:
    """Service de domaine pour la gestion des marchés (asynchrone)"""

    def __init__(self, repository: EveRepository):
        """
        Initialise le service avec un repository

        Args:
            repository: Implémentation du repository Eve
        """
        self.repository = repository

    async def get_market_categories(self) -> list[dict[str, Any]]:
        """
        Récupère la liste des catégories du marché avec leurs détails
        Logique métier : orchestration des appels au repository (parallélisée)

        Returns:
            Liste des catégories formatées, triées par nom
        """
        # Récupérer la liste des groupes de marché
        group_ids = await self.repository.get_market_groups_list()

        # Récupérer les détails de chaque groupe en parallèle
        async def fetch_group(group_id: int) -> dict[str, Any] | None:
            try:
                group_data = await self.repository.get_market_group_details(group_id)
                return {
                    "group_id": group_id,
                    "name": group_data.get("name", "Unknown"),
                    "description": group_data.get("description", ""),
                    "parent_group_id": group_data.get("parent_group_id"),
                    "types": group_data.get("types", []),
                }
            except Exception as e:
                logger.warning(f"Erreur lors de la récupération du groupe {group_id}: {e}")
                return None

        results = await asyncio.gather(*[fetch_group(gid) for gid in group_ids])

        # Filtrer les résultats None et trier par nom
        categories = sorted([c for c in results if c is not None], key=lambda x: x.get("name", ""))

        return categories

    async def get_item_type(self, type_id: int) -> dict[str, Any]:
        return await self.repository.get_item_type(type_id)

    async def get_enriched_market_orders(
        self,
        region_id: int,
        type_id: int | None = None,
        limit: int = DEFAULT_MARKET_ORDERS_LIMIT,
    ) -> dict[str, Any]:
        """
        Récupère les ordres de marché enrichis pour une région
        Logique métier : tri, limitation et enrichissement des ordres

        Args:
            region_id: ID de la région
            type_id: Optionnel, ID du type d'item pour filtrer les ordres
            limit: Nombre maximum d'ordres par type (achat/vente) à retourner

        Returns:
            Dictionnaire contenant les ordres d'achat et de vente enrichis
        """
        # Récupérer les ordres depuis le repository
        orders = await self.repository.get_market_orders(region_id, type_id)

        # Séparer les ordres d'achat et de vente
        buy_orders = [o for o in orders if o.get("is_buy_order", False)]
        sell_orders = [o for o in orders if not o.get("is_buy_order", False)]

        # Trier par prix (meilleur prix en premier)
        buy_orders.sort(key=lambda x: x.get("price", 0), reverse=True)
        sell_orders.sort(key=lambda x: x.get("price", 0))

        # Limiter à N meilleurs ordres pour éviter trop d'appels API
        buy_orders = buy_orders[:limit]
        sell_orders = sell_orders[:limit]

        # Enrichir les ordres avec les noms des systèmes et stations
        async def enrich_order(order: dict[str, Any]) -> dict[str, Any]:
            """Enrichit un ordre avec les noms du système et de la station"""
            location_id = order.get("location_id")
            if not location_id:
                return order

            enriched_order = order.copy()

            # Les IDs >= STATION_ID_THRESHOLD sont des stations, sinon ce sont des systèmes
            if is_station(location_id):
                # C'est une station
                try:
                    station_data = await self.repository.get_station_details(location_id)
                    enriched_order["station_name"] = station_data.get("name", "Unknown Station")
                    enriched_order["station_id"] = location_id

                    # Récupérer aussi le système de la station
                    system_id = station_data.get("system_id")
                    if system_id:
                        system_data = await self.repository.get_system_details(system_id)
                        enriched_order["system_name"] = system_data.get("name", "Unknown System")
                        enriched_order["system_id"] = system_id
                except Exception as e:
                    logger.warning(
                        f"Erreur lors de la récupération de la station {location_id}: {e}"
                    )
                    enriched_order["station_name"] = f"Station {location_id}"
                    enriched_order["station_id"] = location_id
            else:
                # C'est un système
                try:
                    system_data = await self.repository.get_system_details(location_id)
                    enriched_order["system_name"] = system_data.get("name", "Unknown System")
                    enriched_order["system_id"] = location_id
                except Exception as e:
                    logger.warning(f"Erreur lors de la récupération du système {location_id}: {e}")
                    enriched_order["system_name"] = f"Système {location_id}"
                    enriched_order["system_id"] = location_id

            return enriched_order

        # Enrichir tous les ordres en parallèle
        buy_orders_enriched = await asyncio.gather(
            *[enrich_order(order) for order in buy_orders], return_exceptions=True
        )
        sell_orders_enriched = await asyncio.gather(
            *[enrich_order(order) for order in sell_orders], return_exceptions=True
        )

        # Filtrer les erreurs (garder les ordres même si l'enrichissement a échoué)
        buy_orders_final = [
            order if not isinstance(order, Exception) else buy_orders[i]
            for i, order in enumerate(buy_orders_enriched)
        ]
        sell_orders_final = [
            order if not isinstance(order, Exception) else sell_orders[i]
            for i, order in enumerate(sell_orders_enriched)
        ]

        return {
            "total": len(orders),
            "buy_orders": buy_orders_final,
            "sell_orders": sell_orders_final,
        }
