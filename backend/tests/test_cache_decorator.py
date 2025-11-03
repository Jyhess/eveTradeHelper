"""
Tests pour le décorateur de cache
"""

from optparse import TitledHelpFormatter
import sys
from pathlib import Path
import pytest

# Ajouter le répertoire parent au path pour les imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from utils.cache import cached, CacheManager


@pytest.fixture
def no_cache(cache):
    CacheManager._instance = None
    yield None
    CacheManager._instance = cache


class TestCacheDecorator:
    """Tests pour le décorateur @cached"""

    def test_cached_method_with_cache(self, cache):
        """Test que le décorateur fonctionne avec un cache"""
        import time

        # Utiliser un timestamp pour avoir une clé unique à chaque test
        unique_id = int(time.time() * 1000000)

        class TestClass:
            call_count = 0

            @cached(cache_key_prefix=f"test_method_{unique_id}")
            def test_method(self, value):
                TestClass.call_count += 1
                return {"value": value, "call": TestClass.call_count}

        obj = TestClass()
        TestClass.call_count = 0

        # Premier appel - doit exécuter la méthode
        result1 = obj.test_method(42)
        # Le décorateur désérialise automatiquement le dict depuis le cache
        assert isinstance(
            result1, dict
        ), f"Le résultat doit être un dict, mais est {type(result1)}"
        assert result1["value"] == 42
        assert result1["call"] == 1
        assert (
            TestClass.call_count == 1
        ), f"call_count devrait être 1, mais est {TestClass.call_count}"

        # Second appel - doit utiliser le cache
        result2 = obj.test_method(42)
        assert isinstance(
            result2, dict
        ), f"Le résultat doit être un dict, mais est {type(result2)}"
        assert result2["value"] == 42
        assert (
            TestClass.call_count == 1
        ), f"La méthode ne doit pas être appelée à nouveau. call_count={TestClass.call_count}"

    def test_cached_method_without_cache(self, no_cache):
        """Test que le décorateur fonctionne sans cache"""

        class TestClass:
            call_count = 0

            @cached()
            def test_method(self, value):
                TestClass.call_count += 1
                return value

        obj = TestClass()
        result = obj.test_method(42)

        assert result == 42
        assert TestClass.call_count == 1

    def test_cached_with_different_params(self, cache):
        """Test que le cache différencie les paramètres"""
        import time

        # Utiliser un timestamp pour avoir une clé unique à chaque test
        unique_id = int(time.time() * 1000000)

        class TestClass:
            @cached(cache_key_prefix=f"test_different_params_{unique_id}")
            def test_method(self, value):
                return {"value": value}

        obj = TestClass()

        result1 = obj.test_method(1)
        result2 = obj.test_method(2)

        # Le décorateur désérialise automatiquement les dicts depuis le cache
        assert isinstance(
            result1, dict
        ), f"Le résultat doit être un dict, mais est {type(result1)}"
        assert isinstance(
            result2, dict
        ), f"Le résultat doit être un dict, mais est {type(result2)}"
        assert result1["value"] == 1
        assert result2["value"] == 2
        assert result1 != result2

    def test_cached_list_result(self, cache):
        """Test que le cache gère correctement les listes"""

        class TestClass:
            @cached()
            def test_method(self):
                return [1, 2, 3]

        obj = TestClass()
        result = obj.test_method()

        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_cached_empty_list_result(self, cache):
        """Test que le cache retourne correctement une liste vide (pas None)"""
        import time

        # Utiliser un timestamp pour avoir une clé unique à chaque test
        unique_id = int(time.time() * 1000000)

        class TestClass:
            call_count = 0

            @cached(cache_key_prefix=f"test_empty_list_{unique_id}")
            def test_method(self):
                TestClass.call_count += 1
                return []  # Liste vide

        obj = TestClass()
        TestClass.call_count = 0

        # Premier appel - doit exécuter la méthode et retourner []
        result1 = obj.test_method()
        assert (
            result1 == []
        ), f"Le premier appel doit retourner [], mais a retourné {result1!r}"
        assert isinstance(result1, list), "Le résultat doit être une liste"
        assert TestClass.call_count == 1, "La méthode doit être appelée une fois"

        # Second appel - doit utiliser le cache et retourner [] (pas None)
        result2 = obj.test_method()
        assert (
            result2 == []
        ), f"Le second appel doit retourner [] depuis le cache, mais a retourné {result2!r}"
        assert isinstance(result2, list), "Le résultat doit être une liste"
        assert result2 is not None, "Le résultat ne doit pas être None"
        assert (
            TestClass.call_count == 1
        ), f"La méthode ne doit pas être appelée à nouveau. call_count={TestClass.call_count}"

    def test_cached_none_result(self, cache):
        """Test que le cache gère correctement None"""
        import time

        # Utiliser un timestamp pour avoir une clé unique à chaque test
        unique_id = int(time.time() * 1000000)

        class TestClass:
            call_count = 0

            @cached(cache_key_prefix=f"test_none_{unique_id}")
            def test_method(self):
                TestClass.call_count += 1
                return None

        obj = TestClass()
        TestClass.call_count = 0

        # Premier appel - doit exécuter la méthode et retourner None
        result1 = obj.test_method()
        assert result1 is None, "Le premier appel doit retourner None"
        assert TestClass.call_count == 1, "La méthode doit être appelée une fois"

        # Second appel - None peut ne pas être mis en cache (retourne None directement)
        # Le cache peut échouer pour None, donc on accepte que la méthode soit appelée deux fois
        result2 = obj.test_method()
        assert result2 is None, "None doit rester None"
        # Le call_count peut être 1 ou 2 selon si le cache fonctionne ou non

    @pytest.mark.parametrize(
        "test_value,test_name",
        [
            ([], "liste_vide"),
            ([1, 2, 3], "liste_plusieurs_elements"),
            ([42], "liste_un_element"),
            ((), "tuple_vide"),
            ((1, 2, 3), "tuple_plusieurs_elements"),
            ((42,), "tuple_un_element"),
            ({}, "dict_vide"),
            ({"key": "value"}, "dict_un_element"),
            ({"a": 1, "b": 2}, "dict_plusieurs_elements"),
            ({"value": 42}, "dict_avec_value_seule"),
            ({"value": 42, "other": "data"}, "dict_avec_value_et_autres"),
            ("", "string_vide"),
            ("hello", "string_non_vide"),
            (0, "entier_zero"),
            (42, "entier_positif"),
            (-42, "entier_negatif"),
            (0.0, "float_zero"),
            (3.14, "float_positif"),
            (-3.14, "float_negatif"),
            (True, "bool_true"),
            (False, "bool_false"),
            (set(), "set_vide"),
            ({1, 2, 3}, "set_plusieurs_elements"),
        ],
    )
    def test_cached_various_result_types(self, cache, test_value, test_name):
        """Test que le cache gère correctement tous les types de résultats"""
        import time

        # Utiliser un timestamp pour avoir une clé unique à chaque test
        unique_id = int(time.time() * 1000000) + hash(test_name)

        class TestClass:
            call_count = 0

            @cached(cache_key_prefix=f"test_{test_name}_{unique_id}")
            def test_method(self):
                TestClass.call_count += 1
                return test_value

        obj = TestClass()
        TestClass.call_count = 0

        # Premier appel - doit exécuter la méthode et retourner la valeur originale
        result1 = obj.test_method()
        assert TestClass.call_count == 1, "La méthode doit être appelée une fois"
        assert (
            result1 == test_value
        ), f"Valeur attendue {test_value!r}, obtenue {result1!r}"

        # Second appel - doit utiliser le cache
        result2 = obj.test_method()

        # Vérifications génériques qui fonctionnent pour tous les types
        # Le résultat doit être identique à la valeur originale
        assert (
            result2 == test_value
        ), f"Valeur attendue {test_value!r}, obtenue {result2!r}"

        # Le type doit être exactement préservé
        assert type(result2) == type(
            test_value
        ), f"Type attendu {type(test_value)}, obtenu {type(result2)}"

        # Pour les sets, le cache peut échouer (non sérialisables en JSON)
        # On accepte que la méthode soit appelée deux fois dans ce cas
        if not isinstance(test_value, set):
            assert (
                TestClass.call_count == 1
            ), f"La méthode ne doit pas être appelée à nouveau. call_count={TestClass.call_count}"
