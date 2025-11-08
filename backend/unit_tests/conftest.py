"""
Configuration des tests et fixtures partagées
"""

import json
from pathlib import Path

import pytest

from eve.eve_api_client import EveAPIClient
from eve.eve_repository_factory import make_eve_repository
from utils.cache import CacheManager, create_cache
from utils.cache.fake_cache import FakeCache
from utils.cache.simple_cache import SimpleCache

# Chemin vers le dossier de tests
TESTS_DIR = Path(__file__).parent
REFERENCE_DIR = TESTS_DIR / "reference"


# Cache Redis partagé pour la session (initialisé une seule fois)
_cache_instance: SimpleCache | None = None


@pytest.fixture(scope="session")
def _shared_cache():
    """
    Cache Redis partagé initialisé une seule fois pour toute la session de tests.
    Utilisé uniquement pour les tests d'intégration.
    """
    global _cache_instance
    if _cache_instance is None:
        try:
            _cache_instance = create_cache()
        except Exception as e:
            pytest.skip(f"Redis n'est pas disponible pour les tests: {e}")
    return _cache_instance


@pytest.fixture(scope="function")
def cache(request, _shared_cache):
    """
    Fixture pour gérer le cache selon le type de test.
    - Pour les tests d'intégration: utilise le cache Redis partagé
    - Pour les tests unitaires (dans unittests/): utilise un fake cache en mémoire
    """
    # Vérifier si c'est un test unitaire
    # Soit marqué avec @pytest.mark.unit, soit dans le dossier unittests
    is_unit_test = request.node.get_closest_marker("unit") is not None or (
        hasattr(request.node, "parent")
        and request.node.parent is not None
        and request.node.parent.get_closest_marker("unit") is not None
    )

    # Si le test est dans le dossier unittests, utiliser le fake cache
    if not is_unit_test:
        test_file = getattr(request.node, "fspath", None)
        if test_file:
            test_path = Path(test_file)
            if "unittests" in test_path.parts:
                is_unit_test = True

    if is_unit_test:
        # Pour les tests unitaires, utiliser un fake cache en mémoire
        # Sauvegarder l'instance actuelle si elle existe
        original_cache = CacheManager._instance
        # Créer un fake cache avec la même durée d'expiration que le cache Redis
        fake_cache = FakeCache(expiry_hours=24 * 30)
        CacheManager.initialize(fake_cache)

        try:
            yield fake_cache
        finally:
            # Nettoyer le cache après chaque test unitaire
            fake_cache.clear()
            # Restaurer le cache original après le test
            CacheManager._instance = original_cache
    else:
        # Pour les tests d'intégration, utiliser le cache Redis partagé
        CacheManager.initialize(_shared_cache)
        yield _shared_cache
        # Ne pas réinitialiser - le cache est partagé


@pytest.fixture(scope="function")
def eve_client(cache):
    """Fixture pour créer un client API Eve avec cache de test"""
    return EveAPIClient()


@pytest.fixture(scope="session")
def reference_data():
    """Charge les données de référence pour les tests"""
    reference_data = {}

    if REFERENCE_DIR.exists():
        for ref_file in REFERENCE_DIR.glob("*.json"):
            key = ref_file.stem
            with open(ref_file, encoding="utf-8") as f:
                reference_data[key] = json.load(f)

    return reference_data


@pytest.fixture
def eve_repository(cache):
    yield make_eve_repository()
