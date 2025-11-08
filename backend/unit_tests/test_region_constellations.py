"""
Tests pour les constellations d'une région
"""

import pytest

from domain.region_service import RegionService


@pytest.fixture
def region_service(eve_repository):
    """Fixture pour créer un service de région"""
    return RegionService(eve_repository)


class TestRegionConstellations:
    """Tests pour les constellations d'une région"""

    @pytest.mark.asyncio
    async def test_get_region_constellations_with_details(self, region_service):
        """Test de récupération des constellations d'une région"""
        # Utiliser une région connue (The Forge - région ID 10000002)
        region_id = 10000002
        result = await region_service.get_region_constellations_with_details(region_id)

        # Vérifications de base
        assert isinstance(result, list), "Le résultat doit être une liste"
        assert len(result) > 0, "La liste ne doit pas être vide"

        for constellation in result:
            assert isinstance(constellation, dict), "Chaque constellation doit être un dictionnaire"
            assert (
                "constellation_id" in constellation
            ), "Chaque constellation doit avoir un constellation_id"
            assert "name" in constellation, "Chaque constellation doit avoir un name"
            assert (
                "systems" in constellation
            ), "Chaque constellation doit avoir une liste de systems"
            assert isinstance(constellation["systems"], list), "systems doit être une liste"

    @pytest.mark.asyncio
    async def test_get_region_constellations_structure(self, region_service):
        """Vérifie que les constellations ont la structure attendue"""
        region_id = 10000002
        result = await region_service.get_region_constellations_with_details(region_id)

        if result:
            # Vérifier la structure du premier élément
            first = result[0]
            assert "constellation_id" in first
            assert "name" in first
            assert "systems" in first
            assert isinstance(first["constellation_id"], int)
            assert isinstance(first["name"], str)
            assert isinstance(first["systems"], list)
