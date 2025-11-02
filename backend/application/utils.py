"""
Utilitaires pour l'application
Décorateurs et fonctions utilitaires réutilisables
"""

import logging
from functools import wraps
from cachetools import TTLCache
from cachetools.keys import hashkey
from typing import Callable

logger = logging.getLogger(__name__)


def cached_async(cache: TTLCache, exclude_types: tuple = ()):
    """
    Décorateur standard pour mettre en cache les résultats de fonctions async
    Utilise cachetools avec hashkey pour les clés de cache
    
    Args:
        cache: Instance de TTLCache à utiliser
        exclude_types: Types à exclure du hachage des arguments (ex: RegionService pour FastAPI Depends)
    
    Usage:
        @cached_async(_my_cache, exclude_types=(RegionService,))
        async def my_function(region_service: RegionService = Depends(...)):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Créer une clé de cache basée sur les arguments
            # Exclure les types spécifiés (généralement les dépendances FastAPI)
            cache_args = tuple(a for a in args if not isinstance(a, exclude_types))
            cache_kwargs = {
                k: v for k, v in kwargs.items() if not isinstance(v, exclude_types)
            }
            key = hashkey(*cache_args, **cache_kwargs)
            
            # Vérifier le cache
            if key in cache:
                logger.info(f"Cache hit pour {func.__name__}")
                return cache[key]
            
            # Exécuter la fonction
            logger.info(f"Cache miss pour {func.__name__}, exécution...")
            result = await func(*args, **kwargs)
            
            # Mettre en cache
            cache[key] = result
            return result
        
        return wrapper
    return decorator

