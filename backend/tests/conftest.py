"""
Configuration des tests et fixtures partagées
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from eve import EveAPIClient
from utils.cache import CacheManager, create_cache

# Chemin vers le dossier de tests
TESTS_DIR = Path(__file__).parent
REFERENCE_DIR = TESTS_DIR / "reference"


# Cache Redis partagé pour la session (initialisé une seule fois)
_cache_instance = None


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
    - Pour les tests unitaires: désactive le cache (évite les conflits avec les mocks)
    """
    # Vérifier si c'est un test unitaire (marqué avec @pytest.mark.unit)
    # Le marker peut être sur la classe ou sur la méthode
    is_unit_test = request.node.get_closest_marker("unit") is not None or (
        hasattr(request.node, "parent")
        and request.node.parent is not None
        and request.node.parent.get_closest_marker("unit") is not None
    )

    if is_unit_test:
        # Pour les tests unitaires, désactiver le cache
        # Sauvegarder l'instance actuelle si elle existe
        original_cache = CacheManager._instance
        # Désactiver complètement le cache pour ce test
        CacheManager._instance = None

        try:
            yield None
        finally:
            # Toujours restaurer le cache après le test (pour les autres tests)
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
            with open(ref_file, "r", encoding="utf-8") as f:
                reference_data[key] = json.load(f)

    return reference_data
