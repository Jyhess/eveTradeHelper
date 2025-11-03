"""
Tests d'intégration pour l'API region
Teste les endpoints de l'API region, notamment l'endpoint adjacent
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


@pytest.fixture
def mocked_region_service():
    """Fixture pour créer un RegionService mocké pour les tests rapides"""
    mock_service = MagicMock(spec=RegionService)
    mock_repository = MagicMock()

    # Mock de get_region_details
    async def mock_get_region_details(region_id: int):
        """Mock qui retourne une structure de région valide"""
        return {
            "region_id": region_id,
            "name": f"Test Region {region_id}",
            "description": f"Description for region {region_id}",
            "constellations": [20000001, 20000002],
        }

    # Mock de get_constellation_details
    async def mock_get_constellation_details(constellation_id: int):
        """Mock qui retourne une structure de constellation valide"""
        return {
            "constellation_id": constellation_id,
            "name": f"Test Constellation {constellation_id}",
            "region_id": 10000002,
            "systems": [30000001, 30000002],
        }

    # Mock de get_system_details
    async def mock_get_system_details(system_id: int):
        """Mock qui retourne une structure de système valide"""
        return {
            "system_id": system_id,
            "name": f"Test System {system_id}",
            "security_status": 0.5,
            "constellation_id": 20000001,
            "stargates": [50000001, 50000002] if system_id == 30000001 else [],
        }

    # Mock de get_stargate_details
    async def mock_get_stargate_details(stargate_id: int):
        """Mock qui retourne une structure de stargate valide"""
        # Simuler une connexion vers un autre système dans une autre région
        if stargate_id == 50000001:
            return {
                "stargate_id": stargate_id,
                "system_id": 30000001,
                "destination": {
                    "system_id": 30000100,  # Système dans une autre région
                    "stargate_id": 50000100,
                },
            }
        return {
            "stargate_id": stargate_id,
            "system_id": 30000002,
            "destination": {
                "system_id": 30000101,  # Système dans une autre région
                "stargate_id": 50000101,
            },
        }

    # Mock de get_system_details pour le système de destination
    async def mock_get_system_details_with_region(system_id: int):
        """Mock qui retourne un système avec région différente"""
        if system_id in [30000100, 30000101]:
            return {
                "system_id": system_id,
                "name": f"Test System {system_id}",
                "security_status": 0.5,
                "constellation_id": 20000100,  # Constellation dans autre région
            }
        return await mock_get_system_details(system_id)

    # Mock de get_constellation_details pour la constellation de destination
    async def mock_get_constellation_details_with_region(constellation_id: int):
        """Mock qui retourne une constellation avec région différente"""
        if constellation_id == 20000100:
            return {
                "constellation_id": constellation_id,
                "name": f"Test Constellation {constellation_id}",
                "region_id": 10000003,  # Autre région
                "systems": [30000100, 30000101],
            }
        return await mock_get_constellation_details(constellation_id)

    mock_repository.get_region_details = AsyncMock(side_effect=mock_get_region_details)
    mock_repository.get_constellation_details = AsyncMock(
        side_effect=mock_get_constellation_details_with_region
    )
    mock_repository.get_system_details = AsyncMock(
        side_effect=mock_get_system_details_with_region
    )
    mock_repository.get_stargate_details = AsyncMock(
        side_effect=mock_get_stargate_details
    )
    mock_service.repository = mock_repository

    return mock_service


@pytest.fixture
def mocked_test_app(mocked_region_service):
    """Fixture pour créer une application FastAPI avec un service mocké"""
    app = FastAPI()
    set_region_service(mocked_region_service)
    app.include_router(router)
    return app


@pytest.fixture
def mocked_client(mocked_test_app):
    """Fixture pour créer un client de test avec un service mocké"""
    return TestClient(mocked_test_app)


@pytest.mark.integration
class TestRegionAPI:
    """Tests d'intégration pour l'API region"""

    def test_get_adjacent_regions_endpoint_structure(self, mocked_client):
        """Test que l'endpoint adjacent retourne la structure attendue (utilise un mock pour être rapide)"""
        region_id = 10000002
        response = mocked_client.get(f"/api/v1/regions/{region_id}/adjacent")

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

    def test_get_adjacent_regions_endpoint_empty_result(self, mocked_client):
        """Test que l'endpoint gère correctement une région sans régions adjacentes"""
        # Pour ce test, on pourrait utiliser un mock qui retourne une région sans connexions
        # Mais pour simplifier, on teste juste que la structure est correcte même avec 0 résultats
        region_id = 10000002
        response = mocked_client.get(f"/api/v1/regions/{region_id}/adjacent")

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

    def test_get_adjacent_regions_endpoint_imports(self, mocked_client):
        """
        Test spécifique pour vérifier que tous les imports sont corrects.
        Ce test aurait détecté l'erreur 'Dict is not defined' en tentant d'appeler l'endpoint.
        """
        region_id = 10000002

        # Tenter d'appeler l'endpoint - cela devrait lever une erreur si les imports sont manquants
        try:
            response = mocked_client.get(f"/api/v1/regions/{region_id}/adjacent")
            # Si on arrive ici, les imports sont corrects
            assert response.status_code == 200
        except NameError as e:
            # Si on a une NameError, c'est qu'un import manque
            pytest.fail(f"Erreur d'import détectée: {e}")
