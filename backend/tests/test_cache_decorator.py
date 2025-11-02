"""
Tests pour le décorateur de cache
"""

import sys
from pathlib import Path
import pytest

# Ajouter le répertoire parent au path pour les imports
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from eve import cached, CacheManager


class TestCacheDecorator:
    """Tests pour le décorateur @cached"""

    def test_cached_method_with_cache(self, cache):
        """Test que le décorateur fonctionne avec un cache"""
        
        class TestClass:
            call_count = 0
            
            @cached()
            def test_method(self, value):
                TestClass.call_count += 1
                return {"value": value, "call": TestClass.call_count}
        
        obj = TestClass()
        
        # Premier appel - doit exécuter la méthode
        result1 = obj.test_method(42)
        assert result1["value"] == 42
        assert result1["call"] == 1
        assert TestClass.call_count == 1
        
        # Second appel - doit utiliser le cache
        result2 = obj.test_method(42)
        assert result2["value"] == 42
        assert TestClass.call_count == 1, "La méthode ne doit pas être appelée à nouveau"
    
    def test_cached_method_without_cache(self):
        """Test que le décorateur fonctionne sans cache"""
        CacheManager._instance = None
        
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
        
        class TestClass:
            @cached()
            def test_method(self, value):
                return {"value": value}
        
        obj = TestClass()
        
        result1 = obj.test_method(1)
        result2 = obj.test_method(2)
        
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

