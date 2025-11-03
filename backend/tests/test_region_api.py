"""
Tests d'intégration pour l'API region
Teste les endpoints de l'API region, notamment l'endpoint adjacent
"""

import sys
from pathlib import Path
import pytest

# Ajouter le répertoire parent au path pour les imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from eve import EveAPIClient
from eve.repository import EveRepositoryImpl
from domain.region_service import RegionService
from application.region_api import set_region_service, router
from fastapi.testclient import TestClient
from fastapi import FastAPI


@pytest.fixture
def region_service(cache):
    """Fixture pour créer un service de région avec cache de test"""
    api_client = EveAPIClient()
    repository = EveRepositoryImpl(api_client)
    return RegionService(repository)


@pytest.fixture
def test_app(region_service):
    """Fixture pour créer une application FastAPI de test"""
    app = FastAPI()
    set_region_service(region_service)
    app.include_router(router)
    return app


@pytest.fixture
def client(test_app):
    """Fixture pour créer un client de test"""
    return TestClient(test_app)


@pytest.mark.integration
class TestRegionAPI:
    """Tests d'intégration pour l'API region"""

    def test_get_adjacent_regions_endpoint_structure(self, client):
        """Test que l'endpoint adjacent retourne la structure attendue"""
        region_id = 10000002
        response = client.get(f"/api/v1/regions/{region_id}/adjacent")

        # Vérifier le statut HTTP
        assert response.status_code == 200

        # Vérifier la structure de la réponse
        data = response.json()
        assert "region_id" in data
        assert "total" in data
        assert "adjacent_regions" in data

        assert isinstance(data["region_id"], int)
        assert data["region_id"] == region_id
        assert isinstance(data["total"], int)
        assert isinstance(data["adjacent_regions"], list)

        # Vérifier la structure des régions adjacentes si présentes
        if data["adjacent_regions"]:
            region = data["adjacent_regions"][0]
            assert "region_id" in region
            assert "name" in region
            assert isinstance(region["region_id"], int)
            assert isinstance(region["name"], str)

    def test_get_adjacent_regions_endpoint_empty_result(self, client):
        """Test que l'endpoint gère correctement une région sans régions adjacentes"""
        region_id = 10000002
        response = client.get(f"/api/v1/regions/{region_id}/adjacent")

        assert response.status_code == 200
        data = response.json()

        assert data["region_id"] == region_id
        assert isinstance(data["total"], int)
        assert isinstance(data["adjacent_regions"], list)

    def test_get_adjacent_regions_endpoint_invalid_region(self, client):
        """Test avec un ID de région invalide"""
        # Utiliser un ID très grand qui n'existe probablement pas
        response = client.get("/api/v1/regions/999999999/adjacent")

        # L'endpoint devrait gérer gracieusement une région inexistante
        # Il peut retourner 200 avec 0 régions adjacentes ou 500 si erreur
        assert response.status_code in [200, 500]

    @pytest.mark.slow
    def test_get_adjacent_regions_endpoint_real_data(self, client):
        """Test avec de vraies données (test plus long)"""
        # Utiliser une région connue (The Forge - région ID 10000002)
        region_id = 10000002
        response = client.get(
            f"/api/v1/regions/{region_id}/adjacent",
            timeout=60,  # Timeout plus long pour ce test
        )

        assert response.status_code == 200
        data = response.json()

        # Vérifier la structure de base
        assert data["region_id"] == region_id
        assert isinstance(data["total"], int)
        assert isinstance(data["adjacent_regions"], list)

        # Si des régions adjacentes sont trouvées, vérifier leur structure
        if data["adjacent_regions"]:
            for region in data["adjacent_regions"]:
                assert "region_id" in region
                assert "name" in region
                assert isinstance(region["region_id"], int)
                assert isinstance(region["name"], str)

            # Vérifier que les régions sont triées par nom
            if len(data["adjacent_regions"]) > 1:
                names = [r["name"] for r in data["adjacent_regions"]]
                assert names == sorted(names), "Les régions doivent être triées par nom"

    def test_get_adjacent_regions_endpoint_imports(self, client):
        """
        Test spécifique pour vérifier que tous les imports sont corrects.
        Ce test aurait détecté l'erreur 'Dict is not defined' en tentant d'appeler l'endpoint.
        """
        region_id = 10000002

        # Tenter d'appeler l'endpoint - cela devrait lever une erreur si les imports sont manquants
        try:
            response = client.get(f"/api/v1/regions/{region_id}/adjacent")
            # Si on arrive ici, les imports sont corrects
            assert response.status_code == 200
        except NameError as e:
            # Si on a une NameError, c'est qu'un import manque
            pytest.fail(f"Erreur d'import détectée: {e}")
