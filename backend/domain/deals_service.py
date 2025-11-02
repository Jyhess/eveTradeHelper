"""
Service de domaine pour la recherche de bonnes affaires
Contient la logique métier pure, indépendante de l'infrastructure (version asynchrone)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional, Set

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

    async def collect_all_types_from_group(self, group_id: int) -> Set[int]:
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
        def collect_all_types_recursive(
            gid: int, collected_types: Set[int]
        ) -> Set[int]:
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
        return collect_all_types_recursive(group_id, set())

    async def analyze_type_profitability(
        self,
        region_id: int,
        type_id: int,
        min_profit_isk: float,
        max_transport_volume: Optional[float] = None,
        max_buy_cost: Optional[float] = None,
        additional_regions: Optional[List[int]] = None,
    ) -> Optional[Dict[str, Any]]:
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

            # Récupérer les ordres de toutes les régions en parallèle
            all_orders_promises = [
                self.repository.get_market_orders(reg_id, type_id)
                for reg_id in all_regions
            ]
            all_orders_results = await asyncio.gather(
                *all_orders_promises, return_exceptions=True
            )

            # Collecter tous les ordres valides de toutes les régions
            # Stocker la région avec chaque ordre pour pouvoir la retrouver
            all_buy_orders = []  # Liste de tuples (order, region_id)
            all_sell_orders = []  # Liste de tuples (order, region_id)

            for i, orders_result in enumerate(all_orders_results):
                if isinstance(orders_result, list):
                    reg_id = all_regions[i]
                    for order in orders_result:
                        # Stocker l'ordre avec sa région d'origine
                        order_with_region = (order, reg_id)
                        if order.get("is_buy_order", False):
                            all_buy_orders.append(order_with_region)
                        else:
                            all_sell_orders.append(order_with_region)

            if not all_buy_orders or not all_sell_orders:
                return None

            # Dans Eve Online :
            # - buy_order (is_buy_order=True) = quelqu'un veut ACHETER → on peut VENDRE à ce prix
            # - sell_order (is_buy_order=False) = quelqu'un veut VENDRE → on peut ACHETER à ce prix

            # Meilleur prix pour VENDRE (le plus élevé parmi tous les buy_orders de toutes les régions)
            best_sell_order_tuple = max(
                all_buy_orders, key=lambda x: x[0].get("price", 0)
            )
            best_sell_order, sell_region_id = best_sell_order_tuple
            sell_price = best_sell_order.get("price", 0)  # Prix auquel on VEND
            sell_location_id = best_sell_order.get("location_id")
            sell_volume = min(
                best_sell_order.get("volume_remain", 0),
                best_sell_order.get("volume_total", 0),
            )

            # Meilleur prix pour ACHETER (le plus bas parmi tous les sell_orders de toutes les régions)
            best_buy_order_tuple = min(
                all_sell_orders, key=lambda x: x[0].get("price", float("inf"))
            )
            best_buy_order, buy_region_id = best_buy_order_tuple
            buy_price = best_buy_order.get(
                "price", float("inf")
            )  # Prix auquel on ACHÈTE
            buy_location_id = best_buy_order.get("location_id")
            buy_volume = min(
                best_buy_order.get("volume_remain", 0),
                best_buy_order.get("volume_total", 0),
            )

            if sell_price <= 0 or buy_price <= 0:
                return None

            # Calculer le volume échangeable (minimum entre les deux)
            tradable_volume = min(sell_volume, buy_volume)

            if tradable_volume <= 0:
                return None

            # Récupérer les détails du type pour le volume unitaire
            type_details = await self.repository.get_item_type(type_id)
            item_volume = type_details.get("volume", 0.0)  # Volume unitaire en m³

            # Vérifier la limite de volume de transport si spécifiée
            if max_transport_volume is not None and max_transport_volume > 0:
                # Limiter le volume échangeable pour respecter la limite de transport
                max_tradable_volume = (
                    int(max_transport_volume / item_volume)
                    if item_volume > 0
                    else tradable_volume
                )
                if max_tradable_volume <= 0:
                    return None
                tradable_volume = min(tradable_volume, max_tradable_volume)

            # Calculer le bénéfice en ISK (prix de vente - prix d'achat) * volume échangeable
            profit_isk = (sell_price - buy_price) * tradable_volume

            # Calculer les totaux
            total_buy_cost = buy_price * tradable_volume  # Coût total d'achat
            total_sell_revenue = sell_price * tradable_volume  # Revenu total de vente
            total_transport_volume = item_volume * tradable_volume  # Volume total en m³

            # Vérifier la limite de montant d'achat si spécifiée
            if max_buy_cost is not None and max_buy_cost > 0:
                if total_buy_cost > max_buy_cost:
                    # Réduire le volume échangeable pour respecter la limite de montant d'achat
                    max_tradable_volume_by_cost = (
                        int(max_buy_cost / buy_price)
                        if buy_price > 0
                        else tradable_volume
                    )
                    if max_tradable_volume_by_cost <= 0:
                        return None
                    tradable_volume = min(tradable_volume, max_tradable_volume_by_cost)
                    # Recalculer les valeurs avec le nouveau volume
                    profit_isk = (sell_price - buy_price) * tradable_volume
                    total_buy_cost = buy_price * tradable_volume
                    total_sell_revenue = sell_price * tradable_volume
                    total_transport_volume = item_volume * tradable_volume

            # Filtrer selon le seuil de bénéfice minimum en ISK
            if profit_isk < min_profit_isk:
                return None

            # Calculer le bénéfice en % (pour l'affichage)
            profit_percent = ((sell_price - buy_price) / buy_price) * 100

            # Calculer le nombre de sauts si on a des location_id valides
            jumps = None
            buy_system_id = None
            sell_system_id = None
            route_details = []

            if buy_location_id and sell_location_id:
                try:
                    # Les location_id >= 60000000 sont des stations, sinon ce sont des systèmes
                    buy_system_id = buy_location_id
                    sell_system_id = sell_location_id

                    # Si c'est une station, récupérer le système parent
                    if buy_location_id >= 60000000:
                        station_data = await self.repository.get_station_details(
                            buy_location_id
                        )
                        buy_system_id = station_data.get("system_id")

                    if sell_location_id >= 60000000:
                        station_data = await self.repository.get_station_details(
                            sell_location_id
                        )
                        sell_system_id = station_data.get("system_id")

                    # Calculer la route seulement si ce sont des systèmes valides
                    if (
                        buy_system_id
                        and sell_system_id
                        and buy_system_id != sell_system_id
                    ):
                        route_with_details = (
                            await self.repository.get_route_with_details(
                                buy_system_id, sell_system_id
                            )
                        )
                        # Le nombre de sauts = longueur de la route - 1 (car la route inclut origine et destination)
                        jumps = (
                            len(route_with_details) - 1 if route_with_details else None
                        )
                        route_details = route_with_details if route_with_details else []
                    elif buy_system_id == sell_system_id:
                        jumps = 0  # Même système
                        # Récupérer quand même les détails du système
                        system_data = await self.repository.get_system_details(
                            buy_system_id
                        )
                        route_details = [
                            {
                                "system_id": buy_system_id,
                                "name": system_data.get(
                                    "name", f"Système {buy_system_id}"
                                ),
                                "security_status": system_data.get(
                                    "security_status", 0.0
                                ),
                            }
                        ]
                    else:
                        route_details = []
                except Exception as e:
                    logger.warning(
                        f"Erreur lors du calcul de la route pour {type_id}: {e}"
                    )
                    jumps = None
                    route_details = []
            else:
                route_details = []
                jumps = None

            # Calculer le temps de transport estimé (1 minute par saut)
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
            }
        except Exception as e:
            logger.warning(f"Erreur lors de l'analyse du type {type_id}: {e}")
            return None

    async def find_market_deals(
        self,
        region_id: int,
        group_id: int,
        min_profit_isk: float = 100000.0,
        max_transport_volume: Optional[float] = None,
        max_buy_cost: Optional[float] = None,
        additional_regions: Optional[List[int]] = None,
        max_concurrent: int = 20,
    ) -> Dict[str, Any]:
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
        all_types = await self.collect_all_types_from_group(group_id)

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

        # Filtrer les résultats valides et None
        deals = [r for r in results if isinstance(r, dict) and r is not None]

        # Trier par bénéfice ISK décroissant (puis par bénéfice %)
        deals.sort(
            key=lambda x: (x.get("profit_isk", 0), x.get("profit_percent", 0)),
            reverse=True,
        )

        # Calculer le total du bénéfice ISK
        total_profit_isk = sum(deal.get("profit_isk", 0) for deal in deals)

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
