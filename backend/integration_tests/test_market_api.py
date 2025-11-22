import pytest


@pytest.mark.integration
class TestMarketAPI:
    def test_get_market_categories_endpoint_structure(self, client):
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
        # Premier appel
        response1 = client.get("/api/v1/markets/categories")
        assert response1.status_code == 200

        # Deuxième appel - devrait utiliser le cache
        response2 = client.get("/api/v1/markets/categories")
        assert response2.status_code == 200

        # Les données doivent être identiques
        assert response1.json() == response2.json()

    def test_get_item_type_endpoint_structure(self, client):
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
        response = client.get("/api/v1/universe/types/999999999")

        # L'API peut retourner 200 avec des données vides ou 404/500
        # Selon l'implémentation, on accepte les deux
        assert response.status_code in [200, 404, 500]

    def test_get_market_orders_endpoint_structure(self, client):
        region_id = 10000002
        response = client.get(f"/api/v1/markets/regions/{region_id}/orders")

        # Vérifier le statut HTTP
        assert response.status_code == 200

        # Vérifier la structure de la réponse
        data = response.json()
        assert "region_id" in data
        assert "type_id" not in data  # type_id should not be present when not specified
        assert "total" in data
        assert "buy_orders" in data
        assert "sell_orders" in data

        assert isinstance(data["region_id"], int)
        assert data["region_id"] == region_id
        assert isinstance(data["total"], int)
        assert isinstance(data["buy_orders"], list)
        assert isinstance(data["sell_orders"], list)

    def test_get_market_orders_with_type_filter(self, client):
        region_id = 10000002
        type_id = 34  # Tritanium
        response = client.get(
            f"/api/v1/markets/regions/{region_id}/orders", params={"type_id": type_id}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["type_id"] == type_id

    def test_get_market_orders_orders_structure(self, client):
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

    def test_get_item_types_endpoint_with_filter(self, client):
        response = client.get(
            "/api/v1/markets/types/",
            params={"name_filter": "Tritanium", "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert "total" in data
        assert isinstance(data["types"], list)
        assert isinstance(data["total"], int)
        if data["types"]:
            result = data["types"][0]
            assert "type_id" in result
            assert "name" in result

    def test_get_item_types_endpoint_without_filter(self, client):
        response = client.get("/api/v1/markets/types/", params={"limit": 10})

        assert response.status_code == 200
        data = response.json()
        assert "types" in data
        assert "total" in data
        assert isinstance(data["types"], list)
        assert isinstance(data["total"], int)
        assert len(data["types"]) <= 10

    @pytest.mark.slow
    def test_get_type_prices_by_region_endpoint_structure(self, client):
        """Test the structure of the type prices by region endpoint"""
        # Use a common type_id (Tritanium)
        type_id = 34
        response = client.get(f"/api/v1/markets/types/{type_id}/prices")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "type_id" in data
        assert "regions" in data
        assert data["type_id"] == type_id
        assert isinstance(data["regions"], list)

        # Verify that regions without prices are not included
        # All returned regions should have at least one price
        for region in data["regions"]:
            assert "region_id" in region
            assert "region_name" in region
            assert "max_buy_price" in region  # Must be present (can be null)
            assert "min_sell_price" in region  # Must be present (can be null)

            # At least one price must be non-null
            assert (
                region["max_buy_price"] is not None or region["min_sell_price"] is not None
            ), "Regions without any prices should not be returned"

    @pytest.mark.slow
    def test_get_type_prices_by_region_price_fields_always_present(self, client):
        """Test that max_buy_price and min_sell_price are always present in the response"""
        type_id = 34  # Tritanium
        response = client.get(f"/api/v1/markets/types/{type_id}/prices")

        assert response.status_code == 200
        data = response.json()

        # Verify that all regions have both price fields (even if null)
        for region in data["regions"]:
            # Fields must be present in the JSON (not undefined)
            assert "max_buy_price" in region, "max_buy_price field must always be present"
            assert "min_sell_price" in region, "min_sell_price field must always be present"

            # Fields can be null, but must be present
            assert region["max_buy_price"] is None or isinstance(
                region["max_buy_price"], int | float
            )
            assert region["min_sell_price"] is None or isinstance(
                region["min_sell_price"], int | float
            )

    @pytest.mark.slow
    def test_get_type_prices_by_region_statistics_calculable(self, client):
        """Test that the response data can be used to calculate statistics"""
        type_id = 34  # Tritanium
        response = client.get(f"/api/v1/markets/types/{type_id}/prices")

        assert response.status_code == 200
        data = response.json()

        if not data["regions"]:
            pytest.skip("No regions with prices found for this type")

        # Extract prices (filtering out null values)
        buy_prices = [r["max_buy_price"] for r in data["regions"] if r["max_buy_price"] is not None]
        sell_prices = [
            r["min_sell_price"] for r in data["regions"] if r["min_sell_price"] is not None
        ]
        spreads = [
            r["min_sell_price"] - r["max_buy_price"]
            for r in data["regions"]
            if r["max_buy_price"] is not None and r["min_sell_price"] is not None
        ]

        # Verify that statistics can be calculated
        # At least one price type should be available
        assert len(buy_prices) > 0 or len(sell_prices) > 0, "At least one region should have prices"

        # If we have buy prices, verify they are valid numbers
        if buy_prices:
            assert all(isinstance(p, int | float) and p > 0 for p in buy_prices)
            # Statistics should be calculable
            min_buy = min(buy_prices)
            max_buy = max(buy_prices)
            avg_buy = sum(buy_prices) / len(buy_prices)
            assert min_buy > 0
            assert max_buy >= min_buy
            assert avg_buy >= min_buy and avg_buy <= max_buy

        # If we have sell prices, verify they are valid numbers
        if sell_prices:
            assert all(isinstance(p, int | float) and p > 0 for p in sell_prices)
            # Statistics should be calculable
            min_sell = min(sell_prices)
            max_sell = max(sell_prices)
            avg_sell = sum(sell_prices) / len(sell_prices)
            assert min_sell > 0
            assert max_sell >= min_sell
            assert avg_sell >= min_sell and avg_sell <= max_sell

        # If we have spreads, verify they are valid
        if spreads:
            assert all(isinstance(s, int | float) for s in spreads)
            # Spreads can be negative (arbitrage opportunity: sell < buy)
            # Statistics should be calculable
            min_spread = min(spreads)
            max_spread = max(spreads)
            avg_spread = sum(spreads) / len(spreads)
            assert max_spread >= min_spread
            assert avg_spread >= min_spread and avg_spread <= max_spread

    @pytest.mark.slow
    def test_get_type_prices_by_region_no_regions_without_prices(self, client):
        """Test that regions without any prices are filtered out"""
        type_id = 34  # Tritanium
        response = client.get(f"/api/v1/markets/types/{type_id}/prices")

        assert response.status_code == 200
        data = response.json()

        # Verify that no region has both prices as null
        for region in data["regions"]:
            has_buy_price = region["max_buy_price"] is not None
            has_sell_price = region["min_sell_price"] is not None
            assert (
                has_buy_price or has_sell_price
            ), f"Region {region['region_id']} ({region['region_name']}) should have at least one price"
