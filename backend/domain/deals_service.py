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
        self, region_id: int, type_id: int, profit_threshold: float
    ) -> Optional[Dict[str, Any]]:
        """
        Analyse un type d'item pour trouver les opportunités de profit

        Args:
            region_id: ID de la région
            type_id: ID du type d'item
            profit_threshold: Seuil de bénéfice minimum en %

        Returns:
            Dictionnaire avec les détails de l'opportunité si le bénéfice >= seuil,
            None sinon
        """
        try:
            orders = await self.repository.get_market_orders(region_id, type_id)

            buy_orders = [o for o in orders if o.get("is_buy_order", False)]
            sell_orders = [o for o in orders if not o.get("is_buy_order", False)]

            if not buy_orders or not sell_orders:
                return None

            # Meilleur prix d'achat (le plus élevé)
            best_buy_price = max(buy_orders, key=lambda x: x.get("price", 0)).get(
                "price", 0
            )
            # Meilleur prix de vente (le plus bas)
            best_sell_price = min(
                sell_orders, key=lambda x: x.get("price", float("inf"))
            ).get("price", float("inf"))

            if best_buy_price <= 0 or best_sell_price <= 0:
                return None

            # Calculer le bénéfice en %
            profit_percent = (
                (best_buy_price - best_sell_price) / best_sell_price
            ) * 100

            # Filtrer selon le seuil
            if profit_percent < profit_threshold:
                return None

            # Récupérer les détails du type
            type_details = await self.repository.get_item_type(type_id)

            return {
                "type_id": type_id,
                "type_name": type_details.get("name", f"Type {type_id}"),
                "best_buy_price": best_buy_price,
                "best_sell_price": best_sell_price,
                "profit_percent": round(profit_percent, 2),
                "profit_isk": round(best_buy_price - best_sell_price, 2),
                "buy_order_count": len(buy_orders),
                "sell_order_count": len(sell_orders),
            }
        except Exception as e:
            logger.warning(f"Erreur lors de l'analyse du type {type_id}: {e}")
            return None

    async def find_market_deals(
        self,
        region_id: int,
        group_id: int,
        profit_threshold: float = 5.0,
        max_concurrent: int = 20,
    ) -> Dict[str, Any]:
        """
        Trouve les bonnes affaires dans un groupe de marché pour une région
        Parcourt tous les types d'items du groupe (y compris les sous-groupes) et calcule
        le bénéfice potentiel entre les meilleurs ordres d'achat et de vente

        Args:
            region_id: ID de la région
            group_id: ID du groupe de marché
            profit_threshold: Seuil de bénéfice minimum en % (défaut: 5.0)
            max_concurrent: Nombre maximum d'analyses simultanées (défaut: 20)

        Returns:
            Dictionnaire contenant les résultats de la recherche
        """
        logger.info(
            f"Recherche de bonnes affaires pour le groupe {group_id} "
            f"dans la région {region_id} (seuil: {profit_threshold}%)"
        )

        # Collecter tous les types du groupe (et sous-groupes)
        all_types = await self.collect_all_types_from_group(group_id)

        if not all_types:
            return {
                "region_id": region_id,
                "group_id": group_id,
                "profit_threshold": profit_threshold,
                "total_types": 0,
                "deals": [],
            }

        logger.info(f"Trouvé {len(all_types)} types d'items dans le groupe {group_id}")

        # Analyser tous les types en parallèle (limité pour éviter la surcharge)
        semaphore = asyncio.Semaphore(max_concurrent)

        async def analyze_with_limit(type_id: int):
            async with semaphore:
                return await self.analyze_type_profitability(
                    region_id, type_id, profit_threshold
                )

        results = await asyncio.gather(
            *[analyze_with_limit(type_id) for type_id in all_types],
            return_exceptions=True,
        )

        # Filtrer les résultats valides et None
        deals = [r for r in results if isinstance(r, dict) and r is not None]

        # Trier par bénéfice décroissant
        deals.sort(key=lambda x: x.get("profit_percent", 0), reverse=True)

        logger.info(
            f"Trouvé {len(deals)} bonnes affaires avec bénéfice >= {profit_threshold}%"
        )

        return {
            "region_id": region_id,
            "group_id": group_id,
            "profit_threshold": profit_threshold,
            "total_types": len(all_types),
            "deals": deals,
        }
