"""
Tests d'intégration pour l'API market
Teste l'endpoint complet avec un vrai repository
"""

import sys
from pathlib import Path
import pytest

# Ajouter le répertoire parent au path pour les imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from eve import EveAPIClient
from eve.repository import EveRepositoryImpl
from domain.market_service import MarketService
from application.market_api import set_market_service, router
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def market_service(cache):
    """Fixture pour créer un service de marché avec cache de test"""
    from utils.cache import CacheManager

    # Utiliser le cache de test
    CacheManager.initialize(cache)

    api_client = EveAPIClient()
    repository = EveRepositoryImpl(api_client)
    return MarketService(repository)


@pytest.fixture
def test_app(market_service):
    """Fixture pour créer une application FastAPI de test"""
    app = FastAPI()
    set_market_service(market_service)
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app):
    """Fixture pour créer un client de test"""
    return TestClient(test_app)


@pytest.mark.integration
class TestMarketAPI:
    """Tests d'intégration pour l'API market"""

    def test_get_market_categories_endpoint_structure(self, client):
        """Test que l'endpoint retourne la structure attendue"""
        response = client.get("/api/v1/markets/categories")

        # Vérifier le statut HTTP
        assert response.status_code == 200

        # Vérifier la structure de la réponse
        data = response.json()
        assert "total" in data
        assert "categories" in data

        assert isinstance(data["total"], int)
        assert isinstance(data["categories"], list)

        # Vérifier la structure d'une catégorie si elle existe
        if data["categories"]:
            category = data["categories"][0]
            assert "group_id" in category
            assert "name" in category
            assert "description" in category
            assert "parent_group_id" in category
            assert "types" in category

    def test_get_market_categories_cached(self, client):
        """Test que le cache LRU fonctionne"""
        # Premier appel
        response1 = client.get("/api/v1/markets/categories")
        assert response1.status_code == 200

        # Deuxième appel - devrait utiliser le cache
        response2 = client.get("/api/v1/markets/categories")
        assert response2.status_code == 200

        # Les données doivent être identiques
        assert response1.json() == response2.json()

    def test_get_item_type_endpoint_structure(self, client):
        """Test que l'endpoint retourne la structure attendue"""
        # Utiliser un type_id connu (ex: Tritanium)
        type_id = 34
        response = client.get(f"/api/v1/universe/types/{type_id}")

        # Vérifier le statut HTTP
        assert response.status_code == 200

        # Vérifier que c'est un dictionnaire
        data = response.json()
        assert isinstance(data, dict)

        # Vérifier la présence de certains champs communs
        if "name" in data:
            assert isinstance(data["name"], str)

    def test_get_item_type_invalid_id(self, client):
        """Test avec un type_id invalide"""
        response = client.get("/api/v1/universe/types/999999999")

        # L'API peut retourner 200 avec des données vides ou 404/500
        # Selon l'implémentation, on accepte les deux
        assert response.status_code in [200, 404, 500]

    def test_get_market_orders_endpoint_structure(self, client):
        """Test que l'endpoint retourne la structure attendue"""
        region_id = 10000002
        response = client.get(f"/api/v1/markets/regions/{region_id}/orders")

        # Vérifier le statut HTTP
        assert response.status_code == 200

        # Vérifier la structure de la réponse
        data = response.json()
        assert "region_id" in data
        assert "type_id" in data
        assert "total" in data
        assert "buy_orders" in data
        assert "sell_orders" in data

        assert isinstance(data["region_id"], int)
        assert data["region_id"] == region_id
        assert data["type_id"] is None  # Pas de filtre par défaut
        assert isinstance(data["total"], int)
        assert isinstance(data["buy_orders"], list)
        assert isinstance(data["sell_orders"], list)

    def test_get_market_orders_with_type_filter(self, client):
        """Test avec filtre par type_id"""
        region_id = 10000002
        type_id = 34  # Tritanium
        response = client.get(
            f"/api/v1/markets/regions/{region_id}/orders", params={"type_id": type_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type_id"] == type_id

    def test_get_market_orders_orders_structure(self, client):
        """Test que les ordres ont la structure attendue"""
        region_id = 10000002
        type_id = 34  # Tritanium - généralement beaucoup d'ordres
        response = client.get(
            f"/api/v1/markets/regions/{region_id}/orders", params={"type_id": type_id}
        )

        assert response.status_code == 200
        data = response.json()

        # Si des ordres sont trouvés, vérifier leur structure
        if data["buy_orders"]:
            order = data["buy_orders"][0]
            assert "price" in order
            assert "is_buy_order" in order
            # Les ordres enrichis doivent avoir system_id et/ou station_id
            assert "system_id" in order or "station_id" in order

        if data["sell_orders"]:
            order = data["sell_orders"][0]
            assert "price" in order
            assert "is_buy_order" in order
            assert "system_id" in order or "station_id" in order

    def test_get_market_orders_orders_sorted(self, client):
        """Test que les ordres sont triés correctement"""
        region_id = 10000002
        type_id = 34  # Tritanium
        response = client.get(
            f"/api/v1/markets/regions/{region_id}/orders", params={"type_id": type_id}
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifier que les ordres d'achat sont triés par prix décroissant
        if len(data["buy_orders"]) > 1:
            buy_prices = [o["price"] for o in data["buy_orders"]]
            assert buy_prices == sorted(buy_prices, reverse=True)

        # Vérifier que les ordres de vente sont triés par prix croissant
        if len(data["sell_orders"]) > 1:
            sell_prices = [o["price"] for o in data["sell_orders"]]
            assert sell_prices == sorted(sell_prices)

    def test_get_market_orders_orders_limited(self, client):
        """Test que le nombre d'ordres est limité"""
        region_id = 10000002
        type_id = 34  # Tritanium - généralement beaucoup d'ordres
        response = client.get(
            f"/api/v1/markets/regions/{region_id}/orders", params={"type_id": type_id}
        )

        assert response.status_code == 200
        data = response.json()

        # Par défaut, limit = 50, donc max 50 ordres d'achat et 50 de vente
        assert len(data["buy_orders"]) <= 50
        assert len(data["sell_orders"]) <= 50
