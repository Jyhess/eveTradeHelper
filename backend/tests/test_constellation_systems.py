"""
Tests pour les systèmes d'une constellation
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


@pytest.fixture
def region_service():
    """Fixture pour créer un service de région"""
    api_client = EveAPIClient()
    repository = EveRepositoryImpl(api_client)
    return RegionService(repository)


class TestConstellationSystems:
    """Tests pour les systèmes d'une constellation"""

    @pytest.mark.asyncio
    async def test_get_constellation_systems_with_details(self, region_service):
        """Test de récupération des systèmes d'une constellation"""
        # Utiliser une constellation connue (première constellation de The Forge)
        # D'abord récupérer les constellations de la région
        region_id = 10000002
        constellations = await region_service.get_region_constellations_with_details(
            region_id
        )

        assert (
            len(constellations) > 0
        ), "La région doit avoir au moins une constellation"
        constellation_id = constellations[0]["constellation_id"]

        # Récupérer les systèmes de cette constellation
        result = await region_service.get_constellation_systems_with_details(
            constellation_id
        )

        # Vérifications de base
        assert isinstance(result, list), "Le résultat doit être une liste"
        assert len(result) > 0, "La constellation doit avoir au moins un système"

        for system in result:
            assert isinstance(system, dict), "Chaque système doit être un dictionnaire"
            assert "system_id" in system, "Chaque système doit avoir un system_id"
            assert "name" in system, "Chaque système doit avoir un name"
            assert (
                "security_status" in system
            ), "Chaque système doit avoir un security_status"

    @pytest.mark.asyncio
    async def test_get_constellation_systems_structure(self, region_service):
        """Vérifie que les systèmes ont la structure attendue"""
        # Récupérer une constellation pour tester
        region_id = 10000002
        constellations = await region_service.get_region_constellations_with_details(
            region_id
        )

        if not constellations:
            pytest.skip("Aucune constellation disponible pour le test")

        constellation_id = constellations[0]["constellation_id"]
        result = await region_service.get_constellation_systems_with_details(
            constellation_id
        )

        if result:
            # Vérifier la structure du premier élément
            first = result[0]
            assert "system_id" in first
            assert "name" in first
            assert "security_status" in first
            assert isinstance(first["system_id"], int)
            assert isinstance(first["name"], str)
            assert isinstance(first["security_status"], (int, float))
            # Le security_status doit être entre -1.0 et 1.0
            assert -1.0 <= first["security_status"] <= 1.0
