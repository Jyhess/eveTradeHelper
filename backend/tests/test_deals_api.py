"""
Tests d'intégration pour l'API deals
Teste l'endpoint complet avec un vrai repository
"""

import sys
from pathlib import Path
import pytest
from unittest.mock import AsyncMock, MagicMock

# Ajouter le répertoire parent au path pour les imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from eve import EveAPIClient
from eve.repository import EveRepositoryImpl
from domain.deals_service import DealsService
from application.deals_api import set_deals_service, router
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def deals_service(cache):
    """Fixture pour créer un service de deals avec cache de test"""
    api_client = EveAPIClient()
    repository = EveRepositoryImpl(api_client)
    return DealsService(repository)


@pytest.fixture
def test_app(deals_service):
    """Fixture pour créer une application FastAPI de test"""
    app = FastAPI()
    set_deals_service(deals_service)
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app):
    """Fixture pour créer un client de test"""
    return TestClient(test_app)


@pytest.fixture
def mocked_deals_service():
    """Fixture pour créer un DealsService mocké pour les tests rapides"""
    mock_service = MagicMock(spec=DealsService)

    # Mock de la méthode find_market_deals
    async def mock_find_market_deals(
        region_id: int,
        group_id: int,
        min_profit_isk: float = 100000.0,
        max_transport_volume: float = None,
        max_buy_cost: float = None,
        additional_regions: list = None,
        max_concurrent: int = 20,
    ):
        """Mock qui retourne une structure de réponse valide"""
        return {
            "region_id": region_id,
            "group_id": group_id,
            "min_profit_isk": min_profit_isk,
            "max_transport_volume": max_transport_volume,
            "max_buy_cost": max_buy_cost,
            "total_types": 5,
            "total_profit_isk": 1000.0,  # Somme des profits
            "deals": [
                {
                    "type_id": 123,
                    "type_name": "Test Item 1",
                    "buy_price": 100.0,
                    "sell_price": 110.0,
                    "profit_percent": 10.0,
                    "profit_isk": 1000.0,
                    "tradable_volume": 100,
                    "item_volume": 1.0,
                    "total_buy_cost": 10000.0,
                    "total_sell_revenue": 11000.0,
                    "total_transport_volume": 100.0,
                    "buy_order_count": 2,
                    "sell_order_count": 3,
                    "jumps": 5,
                    "estimated_time_minutes": 5,
                    "route_details": [],
                    "buy_system_id": 30000142,
                    "sell_system_id": 30000143,
                }
            ],
        }

    mock_service.find_market_deals = AsyncMock(side_effect=mock_find_market_deals)
    return mock_service


@pytest.fixture
def mocked_test_app(mocked_deals_service):
    """Fixture pour créer une application FastAPI avec un service mocké"""
    app = FastAPI()
    set_deals_service(mocked_deals_service)
    app.include_router(router)
    return app


@pytest.fixture
def mocked_client(mocked_test_app):
    """Fixture pour créer un client de test avec un service mocké"""
    return TestClient(mocked_test_app)


@pytest.mark.integration
class TestDealsAPI:
    """Tests d'intégration pour l'API deals"""

    def test_get_market_deals_endpoint_structure(self, mocked_client):
        """Test que l'endpoint retourne la structure attendue (utilise un mock pour être rapide)"""
        # Utiliser un mock pour éviter les appels API réels et être beaucoup plus rapide
        response = mocked_client.get(
            "/api/v1/markets/deals",
            params={"region_id": 10000002, "group_id": 1822, "min_profit_isk": 50.0},
        )

        # Vérifier le statut HTTP
        assert response.status_code == 200

        # Vérifier la structure de la réponse
        data = response.json()
        assert "region_id" in data
        assert "group_id" in data
        assert "min_profit_isk" in data  # Le service retourne min_profit_isk
        assert "total_types" in data
        assert "deals" in data

        assert isinstance(data["region_id"], int)
        assert isinstance(data["group_id"], int)
        assert isinstance(data["min_profit_isk"], float)
        assert isinstance(data["total_types"], int)
        assert isinstance(data["deals"], list)

        # Vérifier que les deals ont la structure attendue si présents
        if data["deals"]:
            deal = data["deals"][0]
            assert "type_id" in deal
            assert "type_name" in deal
            assert "profit_percent" in deal

    def test_get_market_deals_endpoint_params(self, mocked_client):
        """Test que les paramètres sont correctement passés (utilise un mock pour être rapide)"""
        region_id = 10000002
        group_id = 1822
        min_profit_isk = 30.0

        response = mocked_client.get(
            "/api/v1/markets/deals",
            params={
                "region_id": region_id,
                "group_id": group_id,
                "min_profit_isk": min_profit_isk,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["region_id"] == region_id
        assert data["group_id"] == group_id
        assert data["min_profit_isk"] == min_profit_isk

    def test_get_market_deals_endpoint_default_threshold(self, client):
        """Test que le seuil par défaut est utilisé"""
        response = client.get(
            "/api/v1/markets/deals",
            params={"region_id": 10000002, "group_id": 1822},
        )

        assert response.status_code == 200
        data = response.json()

        # Seuil par défaut est 100000.0 (min_profit_isk)
        assert data["min_profit_isk"] == 100000.0

    def test_get_market_deals_endpoint_deals_structure(self, client):
        """Test que les deals ont la structure attendue"""
        response = client.get(
            "/api/v1/markets/deals",
            params={
                "region_id": 10000002,
                "group_id": 1822,
                "min_profit_isk": 100.0,  # Seuil élevé pour peut-être avoir 0 deals
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Si des deals sont trouvés, vérifier leur structure
        if data["deals"]:
            deal = data["deals"][0]
            assert "type_id" in deal
            assert "type_name" in deal
            assert "buy_price" in deal
            assert "sell_price" in deal
            assert "profit_percent" in deal
            assert "profit_isk" in deal
            assert "buy_order_count" in deal
            assert "sell_order_count" in deal

            assert isinstance(deal["type_id"], int)
            assert isinstance(deal["type_name"], str)
            assert isinstance(deal["buy_price"], (int, float))
            assert isinstance(deal["sell_price"], (int, float))
            assert isinstance(deal["profit_percent"], (int, float))
            assert isinstance(deal["profit_isk"], (int, float))
            assert isinstance(deal["buy_order_count"], int)
            assert isinstance(deal["sell_order_count"], int)

    def test_get_market_deals_endpoint_deals_sorted(self, client):
        """Test que les deals sont triés par profit décroissant"""
        response = client.get(
            "/api/v1/markets/deals",
            params={
                "region_id": 10000002,
                "group_id": 1822,
                "min_profit_isk": 10.0,
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifier que les deals sont triés par profit décroissant
        if len(data["deals"]) > 1:
            for i in range(len(data["deals"]) - 1):
                assert (
                    data["deals"][i]["profit_percent"]
                    >= data["deals"][i + 1]["profit_percent"]
                )

    def test_get_market_deals_endpoint_missing_params(self, client):
        """Test que les paramètres requis sont validés"""
        # Test sans region_id
        response = client.get(
            "/api/v1/markets/deals",
            params={"group_id": 1822},
        )
        assert response.status_code == 422  # Validation error

        # Test sans group_id
        response = client.get(
            "/api/v1/markets/deals",
            params={"region_id": 10000002},
        )
        assert response.status_code == 422  # Validation error

    def test_get_market_deals_endpoint_invalid_group(self, client):
        """Test avec un groupe inexistant"""
        response = client.get(
            "/api/v1/markets/deals",
            params={
                "region_id": 10000002,
                "group_id": 999999,  # Groupe inexistant
                "min_profit_isk": 5.0,
            },
        )

        # L'endpoint devrait gérer gracieusement un groupe inexistant
        assert response.status_code in [
            200,
            500,
        ]  # Peut retourner 200 avec 0 deals ou 500 si erreur

    def test_get_market_deals_endpoint_invalid_threshold(self, client):
        """Test avec un seuil invalide"""
        # Seuil négatif
        response = client.get(
            "/api/v1/markets/deals",
            params={
                "region_id": 10000002,
                "group_id": 1822,
                "min_profit_isk": -5.0,
            },
        )
        # Le seuil négatif devrait être accepté mais ne donnera aucun résultat
        assert response.status_code == 200

    @pytest.mark.slow
    def test_get_market_deals_endpoint_real_data(self, client):
        """Test avec de vraies données (test plus long)"""
        # Utiliser un groupe réel connu pour avoir des résultats
        response = client.get(
            "/api/v1/markets/deals",
            params={
                "region_id": 10000002,  # The Forge
                "group_id": 1822,  # Materials & Parts
                "min_profit_isk": 5.0,
            },
            timeout=60,  # Timeout plus long pour ce test
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifier que total_types est cohérent
        if data["total_types"] > 0:
            # Si des types ont été analysés, il devrait y avoir potentiellement des deals
            assert isinstance(data["deals"], list)
            # Les deals devraient tous respecter le seuil (vérifier profit_isk car c'est le critère réel)
            for deal in data["deals"]:
                assert deal["profit_isk"] >= data["min_profit_isk"]
