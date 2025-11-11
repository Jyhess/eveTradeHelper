import time
from typing import Any

import pytest

from domain.deals_service import DealsService
from domain.location_validator import LocationValidator
from domain.repository import EveRepository
from repositories.local_data import LocalDataRepository


class MockRepository(EveRepository):
    """Mock repository pour les tests unitaires"""

    def __init__(self):
        self.market_groups_list = []
        self.market_groups_details = {}
        self.market_orders = {}
        self.item_types = {}
        self.system_details = {}

    async def get_market_groups_list(self) -> list[int]:
        return self.market_groups_list

    async def get_market_group_details(self, group_id: int) -> dict[str, Any]:
        return self.market_groups_details.get(group_id, {})

    async def get_market_orders(
        self, region_id: int, type_id: int | None = None
    ) -> list[dict[str, Any]]:
        key = (region_id, type_id)
        return self.market_orders.get(key, [])

    async def get_item_type(self, type_id: int) -> dict[str, Any]:
        return self.item_types.get(type_id, {"name": f"Type {type_id}"})

    # Autres méthodes requises par l'interface mais non utilisées dans ces tests
    async def get_regions_list(self) -> list[int]:
        return []

    async def get_region_details(self, region_id: int) -> dict[str, Any]:
        return {}

    async def get_constellation_details(self, constellation_id: int) -> dict[str, Any]:
        return {}

    async def get_system_details(self, system_id: int) -> dict[str, Any]:
        return self.system_details.get(system_id, {})

    async def get_stargate_details(self, stargate_id: int) -> dict[str, Any]:
        return {}

    async def get_station_details(self, station_id: int) -> dict[str, Any]:
        return {}

    async def get_route(self, origin: int, destination: int) -> list[int]:
        return []

    async def get_route_with_details(self, origin: int, destination: int) -> list[dict[str, Any]]:
        return []


@pytest.fixture
def mock_repository():
    """Fixture pour créer un repository mock"""
    return MockRepository()


@pytest.fixture
def deals_service(mock_repository, local_data_repository):
    """Fixture pour créer un DealsService avec un repository mock"""
    location_validator = LocationValidator(local_data_repository, mock_repository)
    return DealsService(mock_repository, location_validator)


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceCollectTypes:
    """Tests pour la collecte de types d'un groupe"""

    async def test_collect_all_types_from_simple_group(self, deals_service, mock_repository):
        """Test avec un groupe simple sans sous-groupes"""
        # Configuration - utiliser des IDs uniques pour éviter les conflits de cache
        group_id = int(time.time() * 1000000) % 1000000 + 1000000
        mock_repository.market_groups_list = [group_id]
        mock_repository.market_groups_details = {
            group_id: {"types": [101, 102, 103], "parent_group_id": None}
        }

        # Exécution
        result = await deals_service.collect_all_types_from_group(group_id)

        # Vérification
        # Le décorateur @cached retourne une liste, on la convertit en Set pour la comparaison
        if isinstance(result, list):
            result = set(result)
        assert isinstance(result, set)
        assert result == {101, 102, 103}

    async def test_collect_all_types_from_group_with_children(self, deals_service, mock_repository):
        """Test avec un groupe ayant des sous-groupes"""
        # Configuration : groupe parent avec 2 sous-groupes - utiliser des IDs uniques
        base_id = int(time.time() * 1000000) % 1000000 + 2000000
        group_id_1 = base_id
        group_id_2 = base_id + 1
        group_id_3 = base_id + 2
        mock_repository.market_groups_list = [group_id_1, group_id_2, group_id_3]
        mock_repository.market_groups_details = {
            group_id_1: {"types": [101, 102], "parent_group_id": None},  # Parent
            group_id_2: {
                "types": [201, 202],
                "parent_group_id": group_id_1,
            },  # Enfant 1
            group_id_3: {"types": [301], "parent_group_id": group_id_1},  # Enfant 2
        }

        # Exécution
        result = await deals_service.collect_all_types_from_group(group_id_1)

        # Vérification : doit inclure les types du parent et des enfants
        # Le décorateur @cached retourne une liste, on la convertit en Set pour la comparaison
        if isinstance(result, list):
            result = set(result)
        assert isinstance(result, set)
        assert result == {101, 102, 201, 202, 301}

    async def test_collect_all_types_from_nested_groups(self, deals_service, mock_repository):
        """Test avec des groupes imbriqués sur plusieurs niveaux"""
        # Utiliser des IDs uniques pour éviter les conflits de cache
        base_id = int(time.time() * 1000000) % 1000000 + 3000000
        group_id_1 = base_id
        group_id_2 = base_id + 1
        group_id_3 = base_id + 2
        group_id_4 = base_id + 3
        mock_repository.market_groups_list = [
            group_id_1,
            group_id_2,
            group_id_3,
            group_id_4,
        ]
        mock_repository.market_groups_details = {
            group_id_1: {"types": [101], "parent_group_id": None},  # Niveau 1
            group_id_2: {"types": [201], "parent_group_id": group_id_1},  # Niveau 2
            group_id_3: {"types": [301], "parent_group_id": group_id_2},  # Niveau 3
            group_id_4: {
                "types": [401],
                "parent_group_id": group_id_2,
            },  # Niveau 3 (autre enfant)
        }

        # Exécution
        result = await deals_service.collect_all_types_from_group(group_id_1)

        # Vérification : doit inclure tous les types de tous les niveaux
        # Le décorateur @cached retourne une liste, on la convertit en Set pour la comparaison
        if isinstance(result, list):
            result = set(result)
        assert result == {101, 201, 301, 401}

    async def test_collect_all_types_from_unknown_group(self, deals_service, mock_repository):
        """Test avec un groupe inexistant"""
        # Utiliser un ID unique pour éviter les conflits de cache
        unknown_group_id = int(time.time() * 1000000) % 1000000 + 9999999
        mock_repository.market_groups_list = []
        mock_repository.market_groups_details = {}

        # Exécution
        result = await deals_service.collect_all_types_from_group(unknown_group_id)

        # Vérification : doit retourner un set vide
        # Le décorateur @cached retourne une liste, on la convertit en Set pour la comparaison
        if isinstance(result, list):
            result = set(result)
        assert isinstance(result, set)
        assert len(result) == 0

    async def test_collect_all_types_from_group_without_types(self, deals_service, mock_repository):
        """Test avec un groupe sans types (seulement des sous-groupes)"""
        # Utiliser des IDs uniques pour éviter les conflits de cache
        base_id = int(time.time() * 1000000) % 1000000 + 4000000
        group_id_1 = base_id
        group_id_2 = base_id + 1
        mock_repository.market_groups_list = [group_id_1, group_id_2]
        mock_repository.market_groups_details = {
            group_id_1: {"types": [], "parent_group_id": None},
            group_id_2: {"types": [201, 202], "parent_group_id": group_id_1},
        }

        # Exécution
        result = await deals_service.collect_all_types_from_group(group_id_1)

        # Vérification : doit inclure seulement les types des enfants
        # Le décorateur @cached retourne une liste, on la convertit en Set pour la comparaison
        if isinstance(result, list):
            result = set(result)
        assert result == {201, 202}


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceAnalyzeType:
    """Tests pour l'analyse de rentabilité d'un type"""

    async def test_analyze_type_profitability_profitable(self, deals_service, mock_repository):
        """Test avec un type profitable"""
        region_id = 10000002
        type_id = 123
        profit_threshold = 5.0

        # Configuration : ordres d'achat et de vente
        # buy_order = quelqu'un veut ACHETER → on peut VENDRE à ce prix
        # sell_order = quelqu'un veut VENDRE → on peut ACHETER à ce prix
        mock_repository.market_orders = {
            (region_id, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # Meilleur prix pour VENDRE
                {
                    "is_buy_order": True,
                    "price": 105,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 95,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # Meilleur prix pour ACHETER
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ]
        }
        mock_repository.item_types = {
            type_id: {"name": "Test Item", "description": "A test item", "volume": 1.0}
        }
        mock_repository.system_details = {
            30000142: {
                "system_id": 30000142,
                "name": "Test System",
                "security_status": 0.9,
            }
        }

        # Exécution
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=profit_threshold
        )

        # Vérification
        assert result is not None
        assert result["type_id"] == type_id
        assert result["type_name"] == "Test Item"
        assert (
            result["buy_price"] == 95
        )  # Prix auquel on ACHÈTE (le plus bas parmi les sell_orders)
        assert (
            result["sell_price"] == 110
        )  # Prix auquel on VEND (le plus élevé parmi les buy_orders)
        # Bénéfice = (110 - 95) * 10 = 150 ISK
        # Bénéfice % = (110 - 95) / 95 * 100 = 15.79%
        assert result["profit_percent"] == pytest.approx(15.79, rel=0.01)
        assert result["profit_isk"] == pytest.approx(150, rel=0.01)
        assert result["buy_order_count"] == 2
        assert result["sell_order_count"] == 2

    async def test_analyze_type_profitability_below_threshold(self, deals_service, mock_repository):
        """Test avec un type non rentable (bénéfice < seuil)"""
        region_id = 10000002
        type_id = 123
        profit_threshold = 10.0

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 105, "location_id": 30000142},  # Bénéfice = 5%
                {"is_buy_order": False, "price": 100, "location_id": 30000142},
            ]
        }

        # Exécution
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=profit_threshold
        )

        # Vérification : doit retourner None car bénéfice < seuil
        assert result is None

    async def test_analyze_type_profitability_no_buy_orders(self, deals_service, mock_repository):
        """Test avec seulement des ordres de vente"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": False, "price": 100, "location_id": 30000142},
            ]
        }

        # Exécution
        result = await deals_service.analyze_type_profitability(region_id, type_id, 5.0)

        # Vérification : doit retourner None
        assert result is None

    async def test_analyze_type_profitability_no_sell_orders(self, deals_service, mock_repository):
        """Test avec seulement des ordres d'achat"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 100, "location_id": 30000142},
            ]
        }

        # Exécution
        result = await deals_service.analyze_type_profitability(region_id, type_id, 5.0)

        # Vérification : doit retourner None
        assert result is None

    async def test_analyze_type_profitability_exact_threshold(self, deals_service, mock_repository):
        """Test avec un bénéfice exactement égal au seuil"""
        region_id = 10000002
        type_id = 123
        profit_threshold = 10.0

        mock_repository.market_orders = {
            (region_id, type_id): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # Bénéfice = 10%
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ]
        }
        mock_repository.item_types = {type_id: {"name": "Test Item", "volume": 1.0}}

        # Exécution
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, min_profit_isk=profit_threshold
        )

        # Vérification : doit retourner le résultat (>= seuil)
        assert result is not None
        assert result["profit_percent"] == 10.0

    async def test_analyze_type_profitability_handles_exception(
        self, deals_service, mock_repository
    ):
        """Test que les exceptions sont gérées"""
        region_id = 10000002
        type_id = 123

        # Simuler une exception lors de l'appel au repository
        async def failing_get_market_orders(*args, **kwargs):
            raise Exception("API Error")

        mock_repository.get_market_orders = failing_get_market_orders

        # Exécution
        result = await deals_service.analyze_type_profitability(region_id, type_id, 5.0)

        # Vérification : doit retourner None sans lever d'exception
        assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceFindDeals:
    """Tests pour la recherche complète de bonnes affaires"""

    async def test_find_market_deals_empty_group(self, deals_service, mock_repository):
        """Test avec un groupe vide"""
        # Utiliser un ID unique pour éviter les conflits de cache
        group_id = int(time.time() * 1000000) % 1000000 + 5000000
        mock_repository.market_groups_list = []
        mock_repository.market_groups_details = {}

        # Exécution
        result = await deals_service.find_market_deals(10000002, group_id, min_profit_isk=5.0)

        # Vérification
        assert result["region_id"] == 10000002
        assert result["group_id"] == group_id
        assert result["min_profit_isk"] == 5.0
        assert result["total_types"] == 0
        assert result["deals"] == []

    async def test_find_market_deals_with_profitable_items(self, deals_service, mock_repository):
        """Test avec des items rentables"""
        # Utiliser des IDs uniques pour éviter les conflits de cache
        base_id = int(time.time() * 1000000) % 1000000 + 6000000
        region_id = 10000002
        profit_threshold = 5.0

        # Configuration des groupes
        group_id_1 = base_id
        group_id_2 = base_id + 1
        mock_repository.market_groups_list = [group_id_1, group_id_2]
        mock_repository.market_groups_details = {
            group_id_1: {"types": [101, 102], "parent_group_id": None},
            group_id_2: {"types": [201], "parent_group_id": group_id_1},
        }

        # Configuration des ordres : 101 profitable, 102 non, 201 profitable
        # min_profit_isk = 5.0 ISK, donc avec volume=10: profit_isk = (prix_sell - prix_buy) * 10
        # Pour 101: (110-100)*10 = 100 ISK > 5.0 ✓
        # Pour 102: (102-100)*10 = 20 ISK > 5.0 ✓ (mais profit% = 2% < 5%)
        # Pour 201: (120-100)*10 = 200 ISK > 5.0 ✓
        mock_repository.market_orders = {
            (region_id, 101): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # 10% profit, 100 ISK
            ],
            (region_id, 102): [
                {
                    "is_buy_order": True,
                    "price": 102,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # 2% profit, 20 ISK
            ],
            (region_id, 201): [
                {
                    "is_buy_order": True,
                    "price": 120,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # 20% profit, 200 ISK
            ],
        }

        # Configuration des types
        mock_repository.item_types = {
            101: {"name": "Item 101", "volume": 1.0},
            102: {"name": "Item 102", "volume": 1.0},
            201: {"name": "Item 201", "volume": 1.0},
        }

        # Exécution
        result = await deals_service.find_market_deals(
            region_id, group_id_1, min_profit_isk=profit_threshold
        )

        # Vérification
        assert result["total_types"] == 3  # 101, 102, 201
        # Tous les 3 types ont profit_isk >= 5.0, donc 3 deals
        assert len(result["deals"]) == 3  # 101, 102, et 201 (tous > 5.0 ISK)
        assert result["deals"][0]["type_id"] == 201  # Trié par profit ISK décroissant
        assert result["deals"][0]["profit_percent"] == 20.0
        assert result["deals"][1]["type_id"] == 101  # 100 ISK
        assert result["deals"][1]["profit_percent"] == 10.0
        assert result["deals"][2]["type_id"] == 102  # 20 ISK (le plus faible mais > 5.0)
        assert result["deals"][2]["profit_percent"] == 2.0

    async def test_find_market_deals_sorted_by_profit(self, deals_service, mock_repository):
        """Test que les deals sont triés par profit décroissant"""
        region_id = 10000002
        group_id = 1

        mock_repository.market_groups_list = [1]
        mock_repository.market_groups_details = {
            1: {"types": [101, 102, 103], "parent_group_id": None}
        }

        # Configuration : profits différents
        # min_profit_isk = 5.0 ISK, donc avec volume=10: profit_isk = (prix_sell - prix_buy) * 10
        mock_repository.market_orders = {
            (region_id, 101): [
                {
                    "is_buy_order": True,
                    "price": 105,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # 5%, 50 ISK
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ],
            (region_id, 102): [
                {
                    "is_buy_order": True,
                    "price": 115,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # 15%, 150 ISK
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ],
            (region_id, 103): [
                {
                    "is_buy_order": True,
                    "price": 110,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },  # 10%, 100 ISK
                {
                    "is_buy_order": False,
                    "price": 100,
                    "volume_remain": 10,
                    "volume_total": 10,
                    "location_id": 30000142,
                },
            ],
        }

        mock_repository.item_types = {
            101: {"name": "Item 101", "volume": 1.0},
            102: {"name": "Item 102", "volume": 1.0},
            103: {"name": "Item 103", "volume": 1.0},
        }

        # Exécution
        result = await deals_service.find_market_deals(region_id, group_id, min_profit_isk=5.0)

        # Vérification : tri décroissant
        assert len(result["deals"]) == 3
        assert result["deals"][0]["profit_percent"] == 15.0  # 102
        assert result["deals"][1]["profit_percent"] == 10.0  # 103
        assert result["deals"][2]["profit_percent"] == 5.0  # 101
