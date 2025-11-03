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
from utils.cache import SimpleCache, CacheManager

# Chemin vers le dossier de tests
TESTS_DIR = Path(__file__).parent
REFERENCE_DIR = TESTS_DIR / "reference"


@pytest.fixture(scope="function")
def cache():
    """Fixture pour créer un cache de test isolé avec fakeredis"""
    try:
        import fakeredis
        # Utiliser fakeredis pour les tests (Redis en mémoire, pas de persistance)
        fake_redis = fakeredis.FakeStrictRedis(decode_responses=True)
        
        # Créer un SimpleCache en utilisant le fake Redis
        # On doit passer par l'initialisation manuelle car SimpleCache attend redis_host ou redis_url
        cache = SimpleCache.__new__(SimpleCache)
        cache.expiry_hours = 24
        cache.redis_client = fake_redis
        
        CacheManager.initialize(cache)
        yield cache
        
        # Nettoyer après le test
        CacheManager._instance = None
        fake_redis.flushall()
    except ImportError:
        pytest.skip("fakeredis n'est pas installé. Installez-le avec: pip install fakeredis")


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

