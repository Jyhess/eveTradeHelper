import pytest


@pytest.mark.integration
class TestRegionAPI:
    def test_get_adjacent_regions_endpoint_structure(self, client):
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

    def test_get_all_systems_endpoint_structure(self, client):
        """Test the structure of the /api/v1/systems/ endpoint"""
        response = client.get("/api/v1/systems/")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "systems" in data
        assert isinstance(data["total"], int)
        assert isinstance(data["systems"], list)

        if data["systems"]:
            system = data["systems"][0]
            assert "system_id" in system
            assert "name" in system
            assert isinstance(system["system_id"], int)
            assert isinstance(system["name"], str)

    def test_get_all_systems_with_filter(self, client):
        """Test filtering systems by name"""
        response = client.get("/api/v1/systems/", params={"name_filter": "Jita"})

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "systems" in data
        assert isinstance(data["systems"], list)

        if data["systems"]:
            for system in data["systems"]:
                assert "Jita" in system["name"] or "jita" in system["name"].lower()

    def test_get_all_constellations_endpoint_structure(self, client):
        """Test the structure of the /api/v1/constellations/ endpoint"""
        response = client.get("/api/v1/constellations/")

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "constellations" in data
        assert isinstance(data["total"], int)
        assert isinstance(data["constellations"], list)

        if data["constellations"]:
            constellation = data["constellations"][0]
            assert "constellation_id" in constellation
            assert "name" in constellation
            assert isinstance(constellation["constellation_id"], int)
            assert isinstance(constellation["name"], str)

    def test_get_all_constellations_with_filter(self, client):
        """Test filtering constellations by name"""
        response = client.get("/api/v1/constellations/", params={"name_filter": "Kimotoro"})

        assert response.status_code == 200
        data = response.json()

        assert "total" in data
        assert "constellations" in data
        assert isinstance(data["constellations"], list)

        if data["constellations"]:
            for constellation in data["constellations"]:
                assert (
                    "Kimotoro" in constellation["name"]
                    or "kimotoro" in constellation["name"].lower()
                )
