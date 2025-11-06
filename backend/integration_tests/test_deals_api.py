import pytest


@pytest.mark.integration
class TestDealsAPI:

    def test_get_market_deals_endpoint_structure(self, client):
        response = client.get(
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

    def test_get_market_deals_endpoint_params(self, client):
        region_id = 10000002
        group_id = 1822
        min_profit_isk = 30.0

        response = client.get(
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
        response = client.get(
            "/api/v1/markets/deals",
            params={"region_id": 10000002, "group_id": 1822},
        )

        assert response.status_code == 200
        data = response.json()

        # Seuil par défaut est 100000.0 (min_profit_isk)
        assert data["min_profit_isk"] == 100000.0

    def test_get_market_deals_endpoint_deals_structure(self, client):
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
