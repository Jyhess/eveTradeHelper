"""
Service de domaine pour la recherche de bonnes affaires
Contient la logique métier pure, indépendante de l'infrastructure (version asynchrone)
"""

import asyncio
import logging
from typing import Any

from utils.cache import cached

from .constants import (
    DEFAULT_MAX_CONCURRENT_ANALYSES,
    DEFAULT_MIN_PROFIT_ISK,
)
from .helpers import (
    apply_buy_cost_limit,
    calculate_tradable_volume,
    get_system_id_from_location,
)
from .repository import EveRepository

logger = logging.getLogger(__name__)


class DealsService:
    """Service de domaine pour la recherche de bonnes affaires (asynchrone)"""

    def __init__(self, repository: EveRepository):
        """
        Initialise le service avec un repository

        Args:
            repository: Implémentation du repository Eve
        """
        self.repository = repository

    async def _collect_orders_from_regions(
        self, region_ids: list[int], type_id: int
    ) -> tuple[list[tuple[dict[str, Any], int]], list[tuple[dict[str, Any], int]]]:
        # Récupérer les ordres de toutes les régions en parallèle
        all_orders_promises = [
            self.repository.get_market_orders(reg_id, type_id) for reg_id in region_ids
        ]
        all_orders_results = await asyncio.gather(*all_orders_promises, return_exceptions=True)

        # Collecter tous les ordres valides de toutes les régions
        all_buy_orders = []
        all_sell_orders = []

        for i, orders_result in enumerate(all_orders_results):
            if isinstance(orders_result, list):
                reg_id = region_ids[i]
                for order in orders_result:
                    order_with_region = (order, reg_id)
                    if order.get("is_buy_order", False):
                        all_buy_orders.append(order_with_region)
                    else:
                        all_sell_orders.append(order_with_region)

        return all_buy_orders, all_sell_orders

    async def _calculate_route_details(
        self, buy_location_id: int, sell_location_id: int, type_id: int
    ) -> tuple[int | None, int | None, int | None, list[dict[str, Any]]]:
        if not buy_location_id or not sell_location_id:
            return None, None, None, []

        try:
            buy_system_id = await get_system_id_from_location(self.repository, buy_location_id)
            sell_system_id = await get_system_id_from_location(self.repository, sell_location_id)

            if not buy_system_id or not sell_system_id:
                return buy_system_id, sell_system_id, None, []

            # Même système
            if buy_system_id == sell_system_id:
                system_data = await self.repository.get_system_details(buy_system_id)
                route_details = [
                    {
                        "system_id": buy_system_id,
                        "name": system_data.get("name", f"Système {buy_system_id}"),
                        "security_status": system_data.get("security_status", 0.0),
                    }
                ]
                return buy_system_id, sell_system_id, 0, route_details

            # Systèmes différents, calculer la route
            route_with_details = await self.repository.get_route_with_details(
                buy_system_id, sell_system_id
            )
            jumps = len(route_with_details) - 1 if route_with_details else None
            return buy_system_id, sell_system_id, jumps, route_with_details or []

        except Exception as e:
            logger.warning(f"Erreur lors du calcul de la route pour {type_id}: {e}")
            return None, None, None, []

    def _filter_valid_deals(self, results: list[Any]) -> list[dict[str, Any]]:
        return [r for r in results if isinstance(r, dict) and r is not None]

    def _sort_deals_by_profit(self, deals: list[dict[str, Any]]) -> list[dict[str, Any]]:
        deals.sort(
            key=lambda x: (x.get("profit_isk", 0), x.get("profit_percent", 0)),
            reverse=True,
        )
        return deals

    def _calculate_total_profit(self, deals: list[dict[str, Any]]) -> float:
        return sum(deal.get("profit_isk", 0) for deal in deals)

    @cached(cache_key_prefix="collect_all_types_from_group2")
    async def collect_all_types_from_group(self, group_id: int) -> set[int]:
        """
        Collecte récursivement tous les types d'items d'un groupe de marché
        et de ses sous-groupes

        Args:
            group_id: ID du groupe de marché

        Returns:
            Ensemble des IDs de types d'items dans le groupe et ses sous-groupes
        """
        # Récupérer tous les groupes pour construire l'arbre de parenté
        all_group_ids = await self.repository.get_market_groups_list()
        all_groups_data = await asyncio.gather(
            *[self.repository.get_market_group_details(gid) for gid in all_group_ids],
            return_exceptions=True,
        )

        # Construire un map des groupes avec leur parent_group_id
        groups_map = {}
        for i, group_data in enumerate(all_groups_data):
            if isinstance(group_data, dict):
                gid = all_group_ids[i]
                groups_map[gid] = {
                    "data": group_data,
                    "types": group_data.get("types", []),
                    "parent_id": group_data.get("parent_group_id"),
                    "children": [],
                }

        # Construire l'arbre des enfants
        for gid, group_info in groups_map.items():
            parent_id = group_info["parent_id"]
            if parent_id and parent_id in groups_map:
                groups_map[parent_id]["children"].append(gid)

        # Fonction récursive pour collecter tous les types
        def collect_all_types_recursive(gid: int, collected_types: set[int]) -> set[int]:
            """Collecte récursivement tous les types d'un groupe de marché"""
            if gid not in groups_map:
                return collected_types

            group_info = groups_map[gid]
            collected_types.update(group_info["types"])

            # Parcourir récursivement les sous-groupes
            for child_id in group_info["children"]:
                collect_all_types_recursive(child_id, collected_types)

            return collected_types

        # Collecter tous les types du groupe (et sous-groupes)
        result_set = collect_all_types_recursive(group_id, set())
        # Le décorateur @cached normalise en liste, mais on retourne un set
        # Le décorateur le reconvertira automatiquement en Set si nécessaire via le typage
        return result_set

    async def analyze_type_profitability(
        self,
        region_id: int,
        type_id: int,
        min_profit_isk: float,
        max_transport_volume: float | None = None,
        max_buy_cost: float | None = None,
        additional_regions: list[int] | None = None,
    ) -> dict[str, Any] | None:
        """
        Analyse un type d'item pour trouver les opportunités de profit
        Cherche dans la région principale et les régions supplémentaires pour trouver le meilleur bénéfice

        Args:
            region_id: ID de la région principale
            type_id: ID du type d'item
            min_profit_isk: Seuil de bénéfice minimum en ISK
            max_transport_volume: Volume de transport maximum autorisé en m³ (None = illimité)
            max_buy_cost: Montant d'achat maximum en ISK (None = illimité)
            additional_regions: Liste d'IDs de régions supplémentaires à rechercher (None = aucune)

        Returns:
            Dictionnaire avec les détails de l'opportunité si le bénéfice >= seuil, volume <= limite et coût <= limite,
            None sinon
        """
        try:
            # Construire la liste complète des régions à rechercher
            all_regions = [region_id]
            if additional_regions:
                all_regions.extend(additional_regions)

            # Collecter les ordres de toutes les régions
            all_buy_orders, all_sell_orders = await self._collect_orders_from_regions(
                all_regions, type_id
            )

            if not all_buy_orders or not all_sell_orders:
                return None

            # Dans Eve Online :
            # - buy_order (is_buy_order=True) = quelqu'un veut ACHETER → on peut VENDRE à ce prix
            # - sell_order (is_buy_order=False) = quelqu'un veut VENDRE → on peut ACHETER à ce prix

            # Meilleur prix pour VENDRE (le plus élevé parmi tous les buy_orders)
            best_sell_order_tuple = max(all_buy_orders, key=lambda x: x[0].get("price", 0))
            best_sell_order, sell_region_id = best_sell_order_tuple
            sell_price = best_sell_order.get("price", 0)
            sell_location_id: int | None = best_sell_order.get("location_id")
            sell_volume = min(
                best_sell_order.get("volume_remain", 0),
                best_sell_order.get("volume_total", 0),
            )

            # Meilleur prix pour ACHETER (le plus bas parmi tous les sell_orders)
            best_buy_order_tuple = min(
                all_sell_orders, key=lambda x: x[0].get("price", float("inf"))
            )
            best_buy_order, buy_region_id = best_buy_order_tuple
            buy_price = best_buy_order.get("price", float("inf"))
            buy_location_id: int | None = best_buy_order.get("location_id")
            buy_volume = min(
                best_buy_order.get("volume_remain", 0),
                best_buy_order.get("volume_total", 0),
            )

            if sell_price <= 0 or buy_price <= 0:
                return None

            # Récupérer les détails du type pour le volume unitaire
            type_details = await self.repository.get_item_type(type_id)
            item_volume = type_details.get("volume", 0.0)

            # Calculer le volume échangeable en tenant compte des limites
            tradable_volume = calculate_tradable_volume(
                buy_volume, sell_volume, item_volume, max_transport_volume
            )
            if tradable_volume is None:
                return None

            # Appliquer la limite de coût d'achat si nécessaire
            tradable_volume = apply_buy_cost_limit(tradable_volume, buy_price, max_buy_cost)
            if tradable_volume is None:
                return None

            # Calculer les valeurs financières
            profit_isk = (sell_price - buy_price) * tradable_volume
            total_buy_cost = buy_price * tradable_volume
            total_sell_revenue = sell_price * tradable_volume
            total_transport_volume = item_volume * tradable_volume

            # Filtrer selon le seuil de bénéfice minimum
            if profit_isk < min_profit_isk:
                return None

            # Calculer le bénéfice en pourcentage
            profit_percent = ((sell_price - buy_price) / buy_price) * 100

            # Calculer les détails de la route
            if buy_location_id is None or sell_location_id is None:
                buy_system_id = None
                sell_system_id = None
                jumps = None
                route_details: list[dict[str, Any]] = []
            else:
                (
                    buy_system_id,
                    sell_system_id,
                    jumps,
                    route_details,
                ) = await self._calculate_route_details(buy_location_id, sell_location_id, type_id)
            estimated_time_minutes = jumps if jumps is not None else None

            # Compter les ordres dans toutes les régions
            total_buy_order_count = len(all_buy_orders)
            total_sell_order_count = len(all_sell_orders)

            return {
                "type_id": type_id,
                "type_name": type_details.get("name", f"Type {type_id}"),
                "buy_price": buy_price,  # Prix auquel on ACHÈTE
                "sell_price": sell_price,  # Prix auquel on VEND
                "profit_percent": round(profit_percent, 2),
                "profit_isk": round(profit_isk, 2),
                "tradable_volume": tradable_volume,
                "item_volume": item_volume,  # Volume unitaire en m³
                "total_buy_cost": round(total_buy_cost, 2),
                "total_sell_revenue": round(total_sell_revenue, 2),
                "total_transport_volume": round(total_transport_volume, 2),
                "buy_order_count": total_buy_order_count,
                "sell_order_count": total_sell_order_count,
                "jumps": jumps,
                "estimated_time_minutes": estimated_time_minutes,
                "route_details": route_details,
                "buy_system_id": buy_system_id if buy_location_id else None,
                "sell_system_id": sell_system_id if sell_location_id else None,
                "buy_region_id": buy_region_id,
                "sell_region_id": sell_region_id,
            }
        except Exception as e:
            logger.warning(f"Erreur lors de l'analyse du type {type_id}: {e}")
            return None

    async def find_market_deals(
        self,
        region_id: int,
        group_id: int,
        min_profit_isk: float = DEFAULT_MIN_PROFIT_ISK,
        max_transport_volume: float | None = None,
        max_buy_cost: float | None = None,
        additional_regions: list[int] | None = None,
        max_concurrent: int = DEFAULT_MAX_CONCURRENT_ANALYSES,
    ) -> dict[str, Any]:
        """
        Trouve les bonnes affaires dans un groupe de marché pour une région
        Parcourt tous les types d'items du groupe (y compris les sous-groupes) et calcule
        le bénéfice potentiel entre les meilleurs ordres d'achat et de vente dans toutes les régions spécifiées

        Args:
            region_id: ID de la région principale
            group_id: ID du groupe de marché
            min_profit_isk: Seuil de bénéfice minimum en ISK (défaut: 100000.0)
            max_transport_volume: Volume de transport maximum autorisé en m³ (None = illimité)
            max_buy_cost: Montant d'achat maximum en ISK (None = illimité)
            additional_regions: Liste d'IDs de régions supplémentaires à rechercher (None = aucune)
            max_concurrent: Nombre maximum d'analyses simultanées (défaut: 20)

        Returns:
            Dictionnaire contenant les résultats de la recherche
        """
        regions_str = str(region_id)
        if additional_regions:
            regions_str += f" + {len(additional_regions)} autre(s)"

        logger.info(
            f"Recherche de bonnes affaires pour le groupe {group_id} "
            f"dans les régions: {regions_str} (seuil: {min_profit_isk} ISK"
            f"{f', volume max: {max_transport_volume} m³' if max_transport_volume else ''}"
            f"{f', montant achat max: {max_buy_cost} ISK' if max_buy_cost else ''})"
        )

        # Collecter tous les types du groupe (et sous-groupes)
        # Le décorateur @cached retourne une liste, on la convertit en Set
        all_types_list = await self.collect_all_types_from_group(group_id)
        all_types = set(all_types_list) if isinstance(all_types_list, list) else all_types_list

        if not all_types:
            return {
                "region_id": region_id,
                "group_id": group_id,
                "min_profit_isk": min_profit_isk,
                "max_transport_volume": max_transport_volume,
                "max_buy_cost": max_buy_cost,
                "total_types": 0,
                "deals": [],
            }

        logger.info(f"Trouvé {len(all_types)} types d'items dans le groupe {group_id}")

        # Analyser tous les types en parallèle (limité pour éviter la surcharge)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_limit(type_id: int):
            async with semaphore:
                return await self.analyze_type_profitability(
                    region_id,
                    type_id,
                    min_profit_isk,
                    max_transport_volume,
                    max_buy_cost,
                    additional_regions,
                )

        results = await asyncio.gather(
            *[analyze_with_limit(type_id) for type_id in all_types],
            return_exceptions=True,
        )

        deals = self._filter_valid_deals(results)
        deals = self._sort_deals_by_profit(deals)
        total_profit_isk = self._calculate_total_profit(deals)

        logger.info(
            f"Trouvé {len(deals)} bonnes affaires avec bénéfice >= {min_profit_isk} ISK"
            f"{f', volume <= {max_transport_volume} m³' if max_transport_volume else ''}"
            f"{f', montant achat <= {max_buy_cost} ISK' if max_buy_cost else ''}"
        )

        return {
            "region_id": region_id,
            "group_id": group_id,
            "min_profit_isk": min_profit_isk,
            "max_transport_volume": max_transport_volume,
            "max_buy_cost": max_buy_cost,
            "total_types": len(all_types),
            "total_profit_isk": round(total_profit_isk, 2),
            "deals": deals,
        }
