"""
Tests unitaires pour MarketService
Teste la logique métier avec des mocks du repository
"""

import sys
from pathlib import Path
import pytest
from typing import Dict, Any, List

# Ajouter le répertoire parent au path pour les imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from domain.market_service import MarketService
from domain.repository import EveRepository


class MockRepository(EveRepository):
    """Mock repository pour les tests unitaires"""

    def __init__(self):
        self.market_groups_list = []
        self.market_groups_details = {}
        self.market_orders = {}
        self.station_details = {}
        self.system_details = {}

    async def get_market_groups_list(self) -> List[int]:
        return self.market_groups_list

    async def get_market_group_details(self, group_id: int) -> Dict[str, Any]:
        return self.market_groups_details.get(group_id, {})

    async def get_market_orders(
        self, region_id: int, type_id: int = None
    ) -> List[Dict[str, Any]]:
        key = (region_id, type_id)
        return self.market_orders.get(key, [])

    async def get_station_details(self, station_id: int) -> Dict[str, Any]:
        return self.station_details.get(station_id, {})

    async def get_system_details(self, system_id: int) -> Dict[str, Any]:
        return self.system_details.get(system_id, {})

    # Autres méthodes requises par l'interface mais non utilisées dans ces tests
    async def get_regions_list(self) -> List[int]:
        return []

    async def get_region_details(self, region_id: int) -> Dict[str, Any]:
        return {}

    async def get_constellation_details(self, constellation_id: int) -> Dict[str, Any]:
        return {}

    async def get_stargate_details(self, stargate_id: int) -> Dict[str, Any]:
        return {}

    async def get_item_type(self, type_id: int) -> Dict[str, Any]:
        return {}

    async def get_route(self, origin: int, destination: int) -> List[int]:
        return []

    async def get_route_with_details(
        self, origin: int, destination: int
    ) -> List[Dict[str, Any]]:
        return []


@pytest.fixture
def mock_repository():
    """Fixture pour créer un repository mock"""
    return MockRepository()


@pytest.fixture
def market_service(mock_repository):
    """Fixture pour créer un MarketService avec un repository mock"""
    return MarketService(mock_repository)


@pytest.mark.asyncio
@pytest.mark.unit
class TestMarketServiceCategories:
    """Tests pour la récupération des catégories de marché"""

    async def test_get_market_categories_empty(self, market_service, mock_repository):
        """Test avec une liste vide de groupes"""
        mock_repository.market_groups_list = []

        result = await market_service.get_market_categories()

        assert isinstance(result, list)
        assert len(result) == 0

    async def test_get_market_categories_single_group(
        self, market_service, mock_repository
    ):
        """Test avec un seul groupe"""
        mock_repository.market_groups_list = [1]
        mock_repository.market_groups_details = {
            1: {
                "name": "Test Group",
                "description": "A test group",
                "parent_group_id": None,
                "types": [101, 102, 103],
            }
        }

        result = await market_service.get_market_categories()

        assert len(result) == 1
        assert result[0]["group_id"] == 1
        assert result[0]["name"] == "Test Group"
        assert result[0]["description"] == "A test group"
        assert result[0]["parent_group_id"] is None
        assert result[0]["types"] == [101, 102, 103]

    async def test_get_market_categories_multiple_groups(
        self, market_service, mock_repository
    ):
        """Test avec plusieurs groupes, triés par nom"""
        mock_repository.market_groups_list = [1, 2, 3]
        mock_repository.market_groups_details = {
            1: {"name": "Zebra Group", "description": "", "parent_group_id": None, "types": []},
            2: {"name": "Alpha Group", "description": "", "parent_group_id": None, "types": []},
            3: {"name": "Beta Group", "description": "", "parent_group_id": None, "types": []},
        }

        result = await market_service.get_market_categories()

        assert len(result) == 3
        # Vérifier que les résultats sont triés par nom
        assert result[0]["name"] == "Alpha Group"
        assert result[1]["name"] == "Beta Group"
        assert result[2]["name"] == "Zebra Group"

    async def test_get_market_categories_filters_errors(
        self, market_service, mock_repository
    ):
        """Test que les erreurs lors de la récupération d'un groupe sont filtrées"""
        mock_repository.market_groups_list = [1, 2, 3]
        
        # Simuler une exception pour le groupe 2
        async def failing_get_market_group_details(group_id: int):
            if group_id == 2:
                raise Exception("API Error")
            return mock_repository.market_groups_details.get(group_id, {})
        
        mock_repository.market_groups_details = {
            1: {"name": "Valid Group", "description": "", "parent_group_id": None, "types": []},
            3: {"name": "Another Valid Group", "description": "", "parent_group_id": None, "types": []},
        }
        mock_repository.get_market_group_details = failing_get_market_group_details

        result = await market_service.get_market_categories()

        # Doit filtrer le groupe 2 (erreur) et retourner seulement 1 et 3
        assert len(result) == 2
        # Vérifier que les groupes retournés sont valides (triés par nom)
        group_names = [r["name"] for r in result]
        assert "Valid Group" in group_names
        assert "Another Valid Group" in group_names

    async def test_get_market_categories_with_parent(
        self, market_service, mock_repository
    ):
        """Test avec des groupes ayant un parent"""
        mock_repository.market_groups_list = [1, 2]
        mock_repository.market_groups_details = {
            1: {
                "name": "Parent Group",
                "description": "Parent",
                "parent_group_id": None,
                "types": [101],
            },
            2: {
                "name": "Child Group",
                "description": "Child",
                "parent_group_id": 1,
                "types": [201],
            },
        }

        result = await market_service.get_market_categories()

        assert len(result) == 2
        # Vérifier que les groupes sont triés par nom
        assert result[0]["name"] == "Child Group"
        assert result[0]["parent_group_id"] == 1
        assert result[1]["name"] == "Parent Group"
        assert result[1]["parent_group_id"] is None


@pytest.mark.asyncio
@pytest.mark.unit
class TestMarketServiceEnrichedOrders:
    """Tests pour la récupération des ordres enrichis"""

    async def test_get_enriched_market_orders_empty(
        self, market_service, mock_repository
    ):
        """Test avec une liste vide d'ordres"""
        region_id = 10000002
        mock_repository.market_orders = {(region_id, None): []}

        result = await market_service.get_enriched_market_orders(region_id)

        assert result["total"] == 0
        assert result["buy_orders"] == []
        assert result["sell_orders"] == []

    async def test_get_enriched_market_orders_separates_buy_sell(
        self, market_service, mock_repository
    ):
        """Test que les ordres d'achat et de vente sont séparés"""
        region_id = 10000002
        mock_repository.market_orders = {
            (region_id, None): [
                {"is_buy_order": True, "price": 100, "location_id": None},
                {"is_buy_order": False, "price": 90, "location_id": None},
                {"is_buy_order": True, "price": 110, "location_id": None},
            ]
        }

        result = await market_service.get_enriched_market_orders(region_id)

        assert result["total"] == 3
        assert len(result["buy_orders"]) == 2
        assert len(result["sell_orders"]) == 1
        assert all(o["is_buy_order"] for o in result["buy_orders"])
        assert all(not o["is_buy_order"] for o in result["sell_orders"])

    async def test_get_enriched_market_orders_sorted_by_price(
        self, market_service, mock_repository
    ):
        """Test que les ordres sont triés par prix"""
        region_id = 10000002
        mock_repository.market_orders = {
            (region_id, None): [
                {"is_buy_order": True, "price": 100, "location_id": None},
                {"is_buy_order": True, "price": 110, "location_id": None},
                {"is_buy_order": True, "price": 105, "location_id": None},
                {"is_buy_order": False, "price": 90, "location_id": None},
                {"is_buy_order": False, "price": 95, "location_id": None},
                {"is_buy_order": False, "price": 85, "location_id": None},
            ]
        }

        result = await market_service.get_enriched_market_orders(region_id)

        # Ordres d'achat triés par prix décroissant (meilleur prix en premier)
        buy_prices = [o["price"] for o in result["buy_orders"]]
        assert buy_prices == [110, 105, 100]

        # Ordres de vente triés par prix croissant (meilleur prix en premier)
        sell_prices = [o["price"] for o in result["sell_orders"]]
        assert sell_prices == [85, 90, 95]

    async def test_get_enriched_market_orders_respects_limit(
        self, market_service, mock_repository
    ):
        """Test que la limite est respectée"""
        region_id = 10000002
        # Créer 100 ordres d'achat et 100 de vente
        buy_orders = [
            {"is_buy_order": True, "price": 100 + i, "location_id": None}
            for i in range(100)
        ]
        sell_orders = [
            {"is_buy_order": False, "price": 50 + i, "location_id": None}
            for i in range(100)
        ]
        mock_repository.market_orders = {(region_id, None): buy_orders + sell_orders}

        result = await market_service.get_enriched_market_orders(region_id, limit=10)

        assert result["total"] == 200
        assert len(result["buy_orders"]) == 10  # Limité à 10
        assert len(result["sell_orders"]) == 10  # Limité à 10

    async def test_get_enriched_market_orders_enriches_system(
        self, market_service, mock_repository
    ):
        """Test que les ordres avec un système sont enrichis"""
        region_id = 10000002
        system_id = 30000142
        mock_repository.market_orders = {
            (region_id, None): [
                {
                    "is_buy_order": True,
                    "price": 100,
                    "location_id": system_id,
                }
            ]
        }
        mock_repository.system_details = {
            system_id: {"name": "Jita", "security_status": 0.9}
        }

        result = await market_service.get_enriched_market_orders(region_id)

        assert len(result["buy_orders"]) == 1
        enriched_order = result["buy_orders"][0]
        assert enriched_order["system_id"] == system_id
        assert enriched_order["system_name"] == "Jita"

    async def test_get_enriched_market_orders_enriches_station(
        self, market_service, mock_repository
    ):
        """Test que les ordres avec une station sont enrichis"""
        region_id = 10000002
        station_id = 60008494
        system_id = 30000142
        mock_repository.market_orders = {
            (region_id, None): [
                {
                    "is_buy_order": True,
                    "price": 100,
                    "location_id": station_id,
                }
            ]
        }
        mock_repository.station_details = {
            station_id: {"name": "Jita IV - Moon 4 - Caldari Navy Assembly Plant", "system_id": system_id}
        }
        mock_repository.system_details = {
            system_id: {"name": "Jita", "security_status": 0.9}
        }

        result = await market_service.get_enriched_market_orders(region_id)

        assert len(result["buy_orders"]) == 1
        enriched_order = result["buy_orders"][0]
        assert enriched_order["station_id"] == station_id
        assert enriched_order["station_name"] == "Jita IV - Moon 4 - Caldari Navy Assembly Plant"
        assert enriched_order["system_id"] == system_id
        assert enriched_order["system_name"] == "Jita"

    async def test_get_enriched_market_orders_handles_missing_location(
        self, market_service, mock_repository
    ):
        """Test que les ordres sans location_id sont gérés"""
        region_id = 10000002
        mock_repository.market_orders = {
            (region_id, None): [
                {"is_buy_order": True, "price": 100},  # Pas de location_id
            ]
        }

        result = await market_service.get_enriched_market_orders(region_id)

        assert len(result["buy_orders"]) == 1
        # L'ordre doit être retourné tel quel, sans enrichissement
        assert "location_id" not in result["buy_orders"][0]

    async def test_get_enriched_market_orders_handles_enrichment_error(
        self, market_service, mock_repository
    ):
        """Test que les erreurs d'enrichissement sont gérées gracieusement"""
        region_id = 10000002
        system_id = 99999999  # Système inexistant
        original_order = {
            "is_buy_order": True,
            "price": 100,
            "location_id": system_id,
        }
        mock_repository.market_orders = {
            (region_id, None): [original_order]
        }
        
        # Simuler une exception lors de la récupération du système
        async def failing_get_system_details(system_id_param: int):
            if system_id_param == system_id:
                raise Exception("System not found")
            return {}
        mock_repository.get_system_details = failing_get_system_details

        result = await market_service.get_enriched_market_orders(region_id)

        assert len(result["buy_orders"]) == 1
        # En cas d'erreur, l'ordre original est retourné (sans enrichissement)
        # car asyncio.gather avec return_exceptions=True retourne l'exception
        # et le code filtre en retournant l'ordre original
        enriched_order = result["buy_orders"][0]
        # L'ordre doit avoir ses champs originaux
        assert enriched_order["price"] == 100
        assert enriched_order["location_id"] == system_id

    async def test_get_enriched_market_orders_with_type_filter(
        self, market_service, mock_repository
    ):
        """Test avec filtre par type_id"""
        region_id = 10000002
        type_id = 123
        mock_repository.market_orders = {
            (region_id, None): [
                {"is_buy_order": True, "price": 100, "location_id": None},
            ],
            (region_id, type_id): [
                {"is_buy_order": True, "price": 200, "location_id": None},
            ],
        }

        result = await market_service.get_enriched_market_orders(region_id, type_id=type_id)

        # Doit retourner seulement les ordres filtrés par type_id
        assert result["total"] == 1
        assert len(result["buy_orders"]) == 1
        assert result["buy_orders"][0]["price"] == 200

