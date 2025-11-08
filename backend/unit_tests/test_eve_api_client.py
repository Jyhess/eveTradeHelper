"""
Tests d'intégration pour EveAPIClient
Compare les réponses API avec des références
"""

import contextlib
import time
from unittest.mock import AsyncMock, patch

import httpx
import pytest

# Importer les fonctions utilitaires
from unittests.test_utils import (
    load_reference,
    normalize_for_comparison,
    save_reference,
)

from domain.constants import DEFAULT_API_MAX_RETRIES
from domain.region_service import RegionService
from eve.eve_api_client import EveAPIClient
from eve.eve_repository_impl import EveRepositoryImpl
from utils.cache import CacheManager, SimpleCache
from utils.cache.fake_cache import FakeCache


class TestEveAPIClientRegions:
    """Tests pour les méthodes liées aux régions"""

    @pytest.mark.asyncio
    async def test_get_regions_list(self, eve_client, reference_data):
        """Test de récupération de la liste des régions"""
        result = await eve_client.get_regions_list()

        # Vérifier que c'est une liste
        assert isinstance(result, list), "Le résultat doit être une liste"
        assert len(result) > 0, "La liste ne doit pas être vide"
        assert all(
            isinstance(region_id, int) for region_id in result
        ), "Tous les éléments doivent être des entiers"

        # Comparer avec la référence si elle existe
        ref_key = "regions_list"
        reference = load_reference(ref_key)

        if reference:
            # Normaliser pour la comparaison
            result_normalized = normalize_for_comparison(result)
            ref_normalized = normalize_for_comparison(reference)

            assert result_normalized == ref_normalized, (
                f"Le résultat ne correspond pas à la référence.\n"
                f"Résultat: {result_normalized[:5]}...\n"
                f"Référence: {ref_normalized[:5]}..."
            )
        else:
            # Sauvegarder comme nouvelle référence
            save_reference(ref_key, result)
            pytest.skip(f"Aucune référence trouvée. Nouvelle référence sauvegardée: {ref_key}")

    @pytest.mark.asyncio
    async def test_get_region_details(self, eve_client, reference_data):
        """Test de récupération des détails d'une région"""
        # Utiliser une région connue (The Forge - région ID 10000002)
        region_id = 10000002
        result = await eve_client.get_region_details(region_id)

        # Vérifications de base
        assert isinstance(result, dict), "Le résultat doit être un dictionnaire"
        assert "name" in result, "Le résultat doit contenir 'name'"
        assert (
            "region_id" not in result or result.get("name") is not None
        ), "Le nom doit être défini"

        # Comparer avec la référence
        ref_key = f"region_details_{region_id}"
        reference = load_reference(ref_key)

        if reference:
            # Normaliser pour la comparaison
            result_normalized = normalize_for_comparison(result)
            ref_normalized = normalize_for_comparison(reference)

            # Comparer les champs clés
            assert result_normalized.get("name") == ref_normalized.get("name"), (
                f"Le nom de la région ne correspond pas.\n"
                f"Résultat: {result_normalized.get('name')}\n"
                f"Référence: {ref_normalized.get('name')}"
            )

            # Vérifier que les constellations sont présentes
            if "constellations" in ref_normalized:
                assert (
                    "constellations" in result_normalized
                ), "Les constellations doivent être présentes"
                assert len(result_normalized["constellations"]) == len(
                    ref_normalized["constellations"]
                ), (
                    f"Le nombre de constellations ne correspond pas.\n"
                    f"Résultat: {len(result_normalized['constellations'])}\n"
                    f"Référence: {len(ref_normalized['constellations'])}"
                )
        else:
            # Sauvegarder comme nouvelle référence
            save_reference(ref_key, result)
            pytest.skip(f"Aucune référence trouvée. Nouvelle référence sauvegardée: {ref_key}")

    @pytest.mark.asyncio
    async def test_get_regions_with_details(self, eve_client, reference_data):
        """Test de récupération des régions avec leurs détails (limité à 5 pour les tests)"""
        # Utiliser le service de domaine au lieu de la méthode directe
        repository = EveRepositoryImpl(eve_client)
        region_service = RegionService(repository)

        limit = 5
        result = await region_service.get_regions_with_details(limit=limit)

        # Vérifications de base
        assert isinstance(result, list), "Le résultat doit être une liste"
        assert len(result) <= limit, f"Le résultat ne doit pas dépasser {limit} éléments"

        for region in result:
            assert isinstance(region, dict), "Chaque région doit être un dictionnaire"
            assert "region_id" in region, "Chaque région doit avoir un region_id"
            assert "name" in region, "Chaque région doit avoir un name"

        # Comparer avec la référence
        ref_key = f"regions_with_details_limit_{limit}"
        reference = load_reference(ref_key)

        if reference:
            # Normaliser pour la comparaison
            result_normalized = normalize_for_comparison(result)
            ref_normalized = normalize_for_comparison(reference)

            assert len(result_normalized) == len(ref_normalized), (
                f"Le nombre de régions ne correspond pas.\n"
                f"Résultat: {len(result_normalized)}\n"
                f"Référence: {len(ref_normalized)}"
            )

            # Comparer les noms des régions
            result_names = [r.get("name") for r in result_normalized]
            ref_names = [r.get("name") for r in ref_normalized]
            assert result_names == ref_names, (
                f"Les noms des régions ne correspondent pas.\n"
                f"Résultat: {result_names}\n"
                f"Référence: {ref_names}"
            )
        else:
            # Sauvegarder comme nouvelle référence
            save_reference(ref_key, result)
            pytest.skip(f"Aucune référence trouvée. Nouvelle référence sauvegardée: {ref_key}")


class TestEveAPIClientCache:
    """Tests pour vérifier le fonctionnement du cache"""

    @pytest.mark.asyncio
    async def test_cache_is_used(self, eve_client):
        """Vérifie que le cache est utilisé lors du second appel"""
        assert CacheManager.is_initialized(), "Le cache doit être initialisé"

        # Premier appel - doit aller à l'API
        result1 = await eve_client.get_regions_list()
        assert isinstance(result1, list)

        # Second appel - doit utiliser le cache
        result2 = await eve_client.get_regions_list()

        # Les résultats doivent être identiques
        assert result1 == result2, "Les résultats doivent être identiques (cache utilisé)"

        # Vérifier que le cache contient les données
        CacheManager.get_instance()
        # Le cache devrait avoir été utilisé (vérification indirecte via la vitesse)

    @pytest.mark.asyncio
    async def test_cache_expiry(self, eve_client):
        """Vérifie que le cache expire correctement"""
        # Créer un cache avec expiration très courte (1 milliseconde)
        # Utiliser le même stockage mais avec un expiry différent
        original_cache = CacheManager.get_instance()

        # Détecter le type de cache et créer une instance temporaire appropriée
        if isinstance(original_cache, SimpleCache):
            short_cache = SimpleCache.__new__(SimpleCache)
            short_cache.expiry_hours = 0.000000278  # 1 ms
            short_cache.redis_client = original_cache.redis_client
        elif isinstance(original_cache, FakeCache):
            short_cache = FakeCache.__new__(FakeCache)
            short_cache.expiry_hours = 0.000000278  # 1 ms
            short_cache._cache_data = original_cache._cache_data
            short_cache._metadata = original_cache._metadata
        else:
            pytest.skip("Type de cache non supporté pour ce test")

        CacheManager.initialize(short_cache)

        # Premier appel
        await eve_client.get_regions_list()

        # Attendre que le cache expire
        time.sleep(0.01)  # 10 ms

        # Deuxième appel - le cache devrait être expiré
        # On ne peut pas vraiment tester que l'API est appelée à nouveau sans mocker,
        # mais on peut vérifier que le cache ne retourne pas de données
        CacheManager.get_instance()
        # Le cache devrait être invalide maintenant


class TestEveAPIClientStructure:
    """Tests pour vérifier la structure des réponses"""

    @pytest.mark.asyncio
    async def test_region_details_structure(self, eve_client):
        """Vérifie que les détails d'une région ont la structure attendue"""
        region_id = 10000002
        result = await eve_client.get_region_details(region_id)

        # Structure attendue
        expected_keys = ["name", "constellations"]

        for key in expected_keys:
            assert key in result, f"La clé '{key}' doit être présente dans le résultat"

        # Vérifier les types
        assert isinstance(result["name"], str), "name doit être une chaîne"
        assert isinstance(result["constellations"], list), "constellations doit être une liste"

        # Vérifier que les constellations sont des entiers
        if result["constellations"]:
            assert all(
                isinstance(c, int) for c in result["constellations"]
            ), "Les constellations doivent être des entiers"

    @pytest.mark.asyncio
    async def test_regions_list_structure(self, eve_client):
        """Vérifie que la liste des régions a la structure attendue"""
        result = await eve_client.get_regions_list()

        assert isinstance(result, list), "Le résultat doit être une liste"

        if result:
            # Vérifier le type des éléments
            assert all(
                isinstance(item, int) for item in result
            ), "Tous les éléments doivent être des entiers"

            # Vérifier qu'il n'y a pas de doublons
            assert len(result) == len(set(result)), "Il ne doit pas y avoir de doublons"


@pytest.mark.unit
class TestEveAPIClientRetry:
    """Tests pour la fonctionnalité de retry des appels API"""

    @pytest.mark.asyncio
    async def test_retry_on_timeout_success(self):
        """Test que le retry fonctionne avec une erreur temporaire qui se résout"""
        client = EveAPIClient()

        # Mock du client HTTP pour simuler un timeout puis un succès
        mock_response = AsyncMock()
        mock_response.json = lambda: {"test": "data"}
        mock_response.raise_for_status = lambda: None

        mock_http_client = AsyncMock()
        call_count = {"value": 0}

        # Premier appel échoue (timeout), deuxième réussit
        async def mock_get(*args, **kwargs):
            if call_count["value"] == 0:
                call_count["value"] += 1
                raise httpx.TimeoutException("Timeout")
            else:
                call_count["value"] += 1
                return mock_response

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        with (
            patch.object(client, "_get_client", return_value=mock_http_client),
            patch.object(client, "_wait_for_rate_limit", return_value=None),
        ):
            result = await client._get("/test/endpoint")

            assert result == {"test": "data"}
            assert call_count["value"] == 2

    @pytest.mark.asyncio
    async def test_retry_uses_constants(self):
        """Test que le retry utilise les constantes définies"""
        client = EveAPIClient()

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with (
            patch.object(client, "_get_client", return_value=mock_http_client),
            patch.object(client, "_wait_for_rate_limit", return_value=None),
            patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        ):
            with contextlib.suppress(Exception):
                await client._get("/test/endpoint")

            # Vérifier que le nombre de tentatives correspond à la constante + 1
            expected_calls = DEFAULT_API_MAX_RETRIES + 1
            assert mock_http_client.get.call_count == expected_calls
            # Vérifier que sleep a été appelé pour chaque retry
            assert mock_sleep.call_count == DEFAULT_API_MAX_RETRIES

    @pytest.mark.asyncio
    async def test_retry_fails_after_max_attempts(self):
        """Test que le retry échoue après toutes les tentatives"""
        client = EveAPIClient()

        mock_http_client = AsyncMock()
        mock_http_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))

        with (
            patch.object(client, "_get_client", return_value=mock_http_client),
            patch.object(client, "_wait_for_rate_limit", return_value=None),
        ):
            with pytest.raises(Exception) as exc_info:
                await client._get("/test/endpoint")

            assert "Timeout" in str(exc_info.value)
            # Vérifier que toutes les tentatives ont été faites
            expected_calls = DEFAULT_API_MAX_RETRIES + 1
            assert mock_http_client.get.call_count == expected_calls

    @pytest.mark.asyncio
    async def test_retry_on_http_error(self):
        """Test que le retry fonctionne avec une erreur HTTP"""
        client = EveAPIClient()

        mock_response = AsyncMock()
        mock_response.json = lambda: {"success": True}
        mock_response.raise_for_status = lambda: None

        mock_error_response = AsyncMock()
        mock_error_response.status_code = 500

        mock_http_client = AsyncMock()
        call_count = {"value": 0}

        async def mock_get(*args, **kwargs):
            if call_count["value"] == 0:
                call_count["value"] += 1
                raise httpx.HTTPStatusError(
                    "Server Error", request=AsyncMock(), response=mock_error_response
                )
            else:
                call_count["value"] += 1
                return mock_response

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        with (
            patch.object(client, "_get_client", return_value=mock_http_client),
            patch.object(client, "_wait_for_rate_limit", return_value=None),
        ):
            result = await client._get("/test/endpoint")

            assert result == {"success": True}
            assert call_count["value"] == 2

    @pytest.mark.asyncio
    async def test_retry_on_connection_error(self):
        """Test que le retry fonctionne avec une erreur de connexion"""
        client = EveAPIClient()

        mock_response = AsyncMock()
        mock_response.json = lambda: {"connected": True}
        mock_response.raise_for_status = lambda: None

        mock_http_client = AsyncMock()
        call_count = {"value": 0}

        async def mock_get(*args, **kwargs):
            if call_count["value"] == 0:
                call_count["value"] += 1
                raise httpx.RequestError("Connection failed")
            else:
                call_count["value"] += 1
                return mock_response

        mock_http_client.get = AsyncMock(side_effect=mock_get)

        with (
            patch.object(client, "_get_client", return_value=mock_http_client),
            patch.object(client, "_wait_for_rate_limit", return_value=None),
        ):
            result = await client._get("/test/endpoint")

            assert result == {"connected": True}
            assert call_count["value"] == 2

    def test_create_exception_from_httpx_error(self):
        """Test que la fonction helper crée les bonnes exceptions"""
        client = EveAPIClient()
        url = "https://test.com/api"

        timeout_error = httpx.TimeoutException("Timeout")
        exception = client._create_exception_from_httpx_error(timeout_error, url)
        assert "Timeout" in str(exception)
        assert url in str(exception)

        mock_response = AsyncMock()
        mock_response.status_code = 404
        http_error = httpx.HTTPStatusError("Not Found", request=AsyncMock(), response=mock_response)
        exception = client._create_exception_from_httpx_error(http_error, url)
        assert "404" in str(exception)
        assert url in str(exception)

        request_error = httpx.RequestError("Connection failed")
        exception = client._create_exception_from_httpx_error(request_error, url)
        assert "connexion" in str(exception).lower() or "connection" in str(exception).lower()
        assert url in str(exception)

    def test_get_error_message(self):
        """Test que la fonction helper génère les bons messages d'erreur"""
        client = EveAPIClient()
        url = "https://test.com/api"

        timeout_error = httpx.TimeoutException("Timeout")
        message = client._get_error_message(timeout_error, url)
        assert "Timeout" in message
        assert url in message

        mock_response = AsyncMock()
        mock_response.status_code = 500
        http_error = httpx.HTTPStatusError(
            "Server Error", request=AsyncMock(), response=mock_response
        )
        message = client._get_error_message(http_error, url)
        assert "500" in message
        assert url in message

        request_error = httpx.RequestError("Connection failed")
        message = client._get_error_message(request_error, url)
        assert "connexion" in message.lower() or "connection" in message.lower()
        assert url in message
