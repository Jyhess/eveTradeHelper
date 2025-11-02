"""
Tests unitaires pour DealsService
Teste la logique métier avec des mocks du repository
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, List

# Ajouter le répertoire parent au path pour les imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from domain.deals_service import DealsService
from domain.repository import EveRepository


class MockRepository(EveRepository):
    """Mock repository pour les tests unitaires"""

    def __init__(self):
        self.market_groups_list = []
        self.market_groups_details = {}
        self.market_orders = {}
        self.item_types = {}

    async def get_market_groups_list(self) -> List[int]:
        return self.market_groups_list

    async def get_market_group_details(self, group_id: int) -> Dict[str, Any]:
        return self.market_groups_details.get(group_id, {})

    async def get_market_orders(
        self, region_id: int, type_id: int = None
    ) -> List[Dict[str, Any]]:
        key = (region_id, type_id)
        return self.market_orders.get(key, [])

    async def get_item_type(self, type_id: int) -> Dict[str, Any]:
        return self.item_types.get(type_id, {"name": f"Type {type_id}"})

    # Autres méthodes requises par l'interface mais non utilisées dans ces tests
    async def get_regions_list(self) -> List[int]:
        return []

    async def get_region_details(self, region_id: int) -> Dict[str, Any]:
        return {}

    async def get_constellation_details(
        self, constellation_id: int
    ) -> Dict[str, Any]:
        return {}

    async def get_system_details(self, system_id: int) -> Dict[str, Any]:
        return {}

    async def get_stargate_details(self, stargate_id: int) -> Dict[str, Any]:
        return {}

    async def get_station_details(self, station_id: int) -> Dict[str, Any]:
        return {}


@pytest.fixture
def mock_repository():
    """Fixture pour créer un repository mock"""
    return MockRepository()


@pytest.fixture
def deals_service(mock_repository):
    """Fixture pour créer un DealsService avec un repository mock"""
    return DealsService(mock_repository)


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceCollectTypes:
    """Tests pour la collecte de types d'un groupe"""

    async def test_collect_all_types_from_simple_group(self, deals_service, mock_repository):
        """Test avec un groupe simple sans sous-groupes"""
        # Configuration
        group_id = 1
        mock_repository.market_groups_list = [1]
        mock_repository.market_groups_details = {
            1: {"types": [101, 102, 103], "parent_group_id": None}
        }

        # Exécution
        result = await deals_service.collect_all_types_from_group(group_id)

        # Vérification
        assert isinstance(result, set)
        assert result == {101, 102, 103}

    async def test_collect_all_types_from_group_with_children(
        self, deals_service, mock_repository
    ):
        """Test avec un groupe ayant des sous-groupes"""
        # Configuration : groupe parent avec 2 sous-groupes
        mock_repository.market_groups_list = [1, 2, 3]
        mock_repository.market_groups_details = {
            1: {"types": [101, 102], "parent_group_id": None},  # Parent
            2: {"types": [201, 202], "parent_group_id": 1},  # Enfant 1
            3: {"types": [301], "parent_group_id": 1},  # Enfant 2
        }

        # Exécution
        result = await deals_service.collect_all_types_from_group(1)

        # Vérification : doit inclure les types du parent et des enfants
        assert isinstance(result, set)
        assert result == {101, 102, 201, 202, 301}

    async def test_collect_all_types_from_nested_groups(
        self, deals_service, mock_repository
    ):
        """Test avec des groupes imbriqués sur plusieurs niveaux"""
        mock_repository.market_groups_list = [1, 2, 3, 4]
        mock_repository.market_groups_details = {
            1: {"types": [101], "parent_group_id": None},  # Niveau 1
            2: {"types": [201], "parent_group_id": 1},  # Niveau 2
            3: {"types": [301], "parent_group_id": 2},  # Niveau 3
            4: {"types": [401], "parent_group_id": 2},  # Niveau 3 (autre enfant)
        }

        # Exécution
        result = await deals_service.collect_all_types_from_group(1)

        # Vérification : doit inclure tous les types de tous les niveaux
        assert result == {101, 201, 301, 401}

    async def test_collect_all_types_from_unknown_group(
        self, deals_service, mock_repository
    ):
        """Test avec un groupe inexistant"""
        mock_repository.market_groups_list = []
        mock_repository.market_groups_details = {}

        # Exécution
        result = await deals_service.collect_all_types_from_group(999)

        # Vérification : doit retourner un set vide
        assert isinstance(result, set)
        assert len(result) == 0

    async def test_collect_all_types_from_group_without_types(
        self, deals_service, mock_repository
    ):
        """Test avec un groupe sans types (seulement des sous-groupes)"""
        mock_repository.market_groups_list = [1, 2]
        mock_repository.market_groups_details = {
            1: {"types": [], "parent_group_id": None},
            2: {"types": [201, 202], "parent_group_id": 1},
        }

        # Exécution
        result = await deals_service.collect_all_types_from_group(1)

        # Vérification : doit inclure seulement les types des enfants
        assert result == {201, 202}


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceAnalyzeType:
    """Tests pour l'analyse de rentabilité d'un type"""

    async def test_analyze_type_profitability_profitable(
        self, deals_service, mock_repository
    ):
        """Test avec un type profitable"""
        region_id = 10000002
        type_id = 123
        profit_threshold = 5.0

        # Configuration : ordres d'achat et de vente
        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 110},  # Meilleur prix d'achat
                {"is_buy_order": True, "price": 105},
                {"is_buy_order": False, "price": 95},  # Meilleur prix de vente
                {"is_buy_order": False, "price": 100},
            ]
        }
        mock_repository.item_types = {
            type_id: {"name": "Test Item", "description": "A test item"}
        }

        # Exécution
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, profit_threshold
        )

        # Vérification
        assert result is not None
        assert result["type_id"] == type_id
        assert result["type_name"] == "Test Item"
        assert result["best_buy_price"] == 110
        assert result["best_sell_price"] == 95
        assert result["profit_percent"] == pytest.approx(15.79, rel=0.01)
        assert result["profit_isk"] == 15
        assert result["buy_order_count"] == 2
        assert result["sell_order_count"] == 2

    async def test_analyze_type_profitability_below_threshold(
        self, deals_service, mock_repository
    ):
        """Test avec un type non rentable (bénéfice < seuil)"""
        region_id = 10000002
        type_id = 123
        profit_threshold = 10.0

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 105},  # Bénéfice = 5%
                {"is_buy_order": False, "price": 100},
            ]
        }

        # Exécution
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, profit_threshold
        )

        # Vérification : doit retourner None car bénéfice < seuil
        assert result is None

    async def test_analyze_type_profitability_no_buy_orders(
        self, deals_service, mock_repository
    ):
        """Test avec seulement des ordres de vente"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": False, "price": 100},
            ]
        }

        # Exécution
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, 5.0
        )

        # Vérification : doit retourner None
        assert result is None

    async def test_analyze_type_profitability_no_sell_orders(
        self, deals_service, mock_repository
    ):
        """Test avec seulement des ordres d'achat"""
        region_id = 10000002
        type_id = 123

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 100},
            ]
        }

        # Exécution
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, 5.0
        )

        # Vérification : doit retourner None
        assert result is None

    async def test_analyze_type_profitability_exact_threshold(
        self, deals_service, mock_repository
    ):
        """Test avec un bénéfice exactement égal au seuil"""
        region_id = 10000002
        type_id = 123
        profit_threshold = 10.0

        mock_repository.market_orders = {
            (region_id, type_id): [
                {"is_buy_order": True, "price": 110},  # Bénéfice = 10%
                {"is_buy_order": False, "price": 100},
            ]
        }
        mock_repository.item_types = {type_id: {"name": "Test Item"}}

        # Exécution
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, profit_threshold
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
        result = await deals_service.analyze_type_profitability(
            region_id, type_id, 5.0
        )

        # Vérification : doit retourner None sans lever d'exception
        assert result is None


@pytest.mark.asyncio
@pytest.mark.unit
class TestDealsServiceFindDeals:
    """Tests pour la recherche complète de bonnes affaires"""

    async def test_find_market_deals_empty_group(
        self, deals_service, mock_repository
    ):
        """Test avec un groupe vide"""
        mock_repository.market_groups_list = []
        mock_repository.market_groups_details = {}

        # Exécution
        result = await deals_service.find_market_deals(10000002, 1, 5.0)

        # Vérification
        assert result["region_id"] == 10000002
        assert result["group_id"] == 1
        assert result["profit_threshold"] == 5.0
        assert result["total_types"] == 0
        assert result["deals"] == []

    async def test_find_market_deals_with_profitable_items(
        self, deals_service, mock_repository
    ):
        """Test avec des items rentables"""
        region_id = 10000002
        group_id = 1
        profit_threshold = 5.0

        # Configuration des groupes
        mock_repository.market_groups_list = [1, 2]
        mock_repository.market_groups_details = {
            1: {"types": [101, 102], "parent_group_id": None},
            2: {"types": [201], "parent_group_id": 1},
        }

        # Configuration des ordres : 101 profitable, 102 non, 201 profitable
        mock_repository.market_orders = {
            (region_id, 101): [
                {"is_buy_order": True, "price": 110},
                {"is_buy_order": False, "price": 100},  # 10% profit
            ],
            (region_id, 102): [
                {"is_buy_order": True, "price": 102},
                {"is_buy_order": False, "price": 100},  # 2% profit (< 5%)
            ],
            (region_id, 201): [
                {"is_buy_order": True, "price": 120},
                {"is_buy_order": False, "price": 100},  # 20% profit
            ],
        }

        # Configuration des types
        mock_repository.item_types = {
            101: {"name": "Item 101"},
            102: {"name": "Item 102"},
            201: {"name": "Item 201"},
        }

        # Exécution
        result = await deals_service.find_market_deals(
            region_id, group_id, profit_threshold
        )

        # Vérification
        assert result["total_types"] == 3  # 101, 102, 201
        assert len(result["deals"]) == 2  # 101 et 201
        assert result["deals"][0]["type_id"] == 201  # Trié par profit décroissant
        assert result["deals"][0]["profit_percent"] == 20.0
        assert result["deals"][1]["type_id"] == 101
        assert result["deals"][1]["profit_percent"] == 10.0

    async def test_find_market_deals_sorted_by_profit(
        self, deals_service, mock_repository
    ):
        """Test que les deals sont triés par profit décroissant"""
        region_id = 10000002
        group_id = 1

        mock_repository.market_groups_list = [1]
        mock_repository.market_groups_details = {
            1: {"types": [101, 102, 103], "parent_group_id": None}
        }

        # Configuration : profits différents
        mock_repository.market_orders = {
            (region_id, 101): [
                {"is_buy_order": True, "price": 105},  # 5%
                {"is_buy_order": False, "price": 100},
            ],
            (region_id, 102): [
                {"is_buy_order": True, "price": 115},  # 15%
                {"is_buy_order": False, "price": 100},
            ],
            (region_id, 103): [
                {"is_buy_order": True, "price": 110},  # 10%
                {"is_buy_order": False, "price": 100},
            ],
        }

        mock_repository.item_types = {
            101: {"name": "Item 101"},
            102: {"name": "Item 102"},
            103: {"name": "Item 103"},
        }

        # Exécution
        result = await deals_service.find_market_deals(region_id, group_id, 5.0)

        # Vérification : tri décroissant
        assert len(result["deals"]) == 3
        assert result["deals"][0]["profit_percent"] == 15.0  # 102
        assert result["deals"][1]["profit_percent"] == 10.0  # 103
        assert result["deals"][2]["profit_percent"] == 5.0  # 101

