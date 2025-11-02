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

from eve import SimpleCache, CacheManager, EveAPIClient

# Chemin vers le dossier de tests
TESTS_DIR = Path(__file__).parent
REFERENCE_DIR = TESTS_DIR / "reference"
CACHE_DIR = TESTS_DIR / "test_cache"


@pytest.fixture(scope="function")
def cache():
    """Fixture pour créer un cache de test isolé"""
    # Nettoyer le cache de test avant chaque test
    if CACHE_DIR.exists():
        import shutil
        shutil.rmtree(CACHE_DIR)
    
    cache = SimpleCache(cache_dir=str(CACHE_DIR), expiry_hours=24)
    CacheManager.initialize(cache)
    yield cache
    
    # Nettoyer après le test
    CacheManager._instance = None
    if CACHE_DIR.exists():
        import shutil
        shutil.rmtree(CACHE_DIR)


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


# Les fonctions utilitaires sont maintenant dans test_utils.py

