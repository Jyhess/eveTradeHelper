"""
Décorateur pour mettre en cache automatiquement les résultats des méthodes
Supporte les fonctions synchrones et asynchrones
"""

import functools
import hashlib
import inspect
import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any, cast

from .manager import CacheManager
from .simple_cache import SimpleCache

if TYPE_CHECKING:
    from .fake_cache import FakeCache
else:
    try:
        from .fake_cache import FakeCache
    except ImportError:
        FakeCache = None  # type: ignore[assignment, misc]

logger = logging.getLogger(__name__)


def _generate_cache_key(func_name: str, prefix: str | None, args: tuple, kwargs: dict) -> str:
    """
    Génère une clé de cache unique basée sur le nom de la fonction et ses paramètres

    Args:
        func_name: Nom de la fonction
        prefix: Préfixe optionnel pour la clé
        args: Arguments positionnels
        kwargs: Arguments nommés

    Returns:
        Clé de cache hashée
    """
    prefix = prefix or func_name
    cache_key_parts = [prefix]

    # Ajouter les arguments positionnels
    if args:
        args_str = str(args) if len(args) > 0 else ""
        cache_key_parts.append(args_str)

    # Ajouter les arguments nommés (triés pour garantir un ordre cohérent)
    if kwargs:
        sorted_kwargs = sorted(kwargs.items())
        cache_key_parts.append(str(sorted_kwargs))

    # Créer une clé de cache hashée pour éviter les noms trop longs
    cache_key_raw = "_".join(str(part) for part in cache_key_parts)
    cache_key_hash = hashlib.md5(cache_key_raw.encode()).hexdigest()
    return f"{prefix}_{cache_key_hash}"


def _get_cache_instance(expiry_hours: int | None) -> SimpleCache | Any | None:
    """
    Récupère l'instance de cache, avec gestion de l'expiry personnalisé

    Args:
        expiry_hours: Durée de vie personnalisée du cache en heures

    Returns:
        Instance de cache ou None si le cache n'est pas initialisé
    """
    if not CacheManager.is_initialized():
        return None

    cache_instance = CacheManager.get_instance()
    if cache_instance is None:
        return None

    # À ce point, cache_instance ne peut pas être None (vérifié par is_initialized)
    # Utiliser cast pour aider le type checker
    cache_instance = cast(SimpleCache | Any, cache_instance)

    # Créer une instance temporaire si expiry_hours est différent
    if expiry_hours and expiry_hours != cache_instance.expiry_hours:
        # Détecter le type de cache et créer une instance temporaire appropriée
        if isinstance(cache_instance, SimpleCache):
            temp_cache = SimpleCache.__new__(SimpleCache)
            temp_cache.expiry_hours = expiry_hours
            temp_cache.redis_client = cache_instance.redis_client
            return temp_cache
        elif FakeCache is not None and isinstance(cache_instance, FakeCache):
            # Pour FakeCache, créer une nouvelle instance qui partage le même stockage
            temp_cache = FakeCache.__new__(FakeCache)  # type: ignore[assignment]
            temp_cache.expiry_hours = expiry_hours
            temp_cache._cache_data = cache_instance._cache_data  # type: ignore[attr-defined]
            temp_cache._metadata = cache_instance._metadata  # type: ignore[attr-defined]
            return temp_cache  # type: ignore[return-value]

    return cache_instance


def _get_cached_result(cache_instance: SimpleCache | Any, cache_key: str) -> Any | None:
    """
    Récupère le résultat depuis le cache si disponible et valide

    Args:
        cache_instance: Instance du cache
        cache_key: Clé du cache

    Returns:
        Résultat en cache ou None si non disponible
    """
    if not cache_instance.is_valid(cache_key):
        return None

    cached_result = cache_instance.get(cache_key)
    if cached_result is None:
        return None

    # Le cache stocke une liste, récupérer le premier élément si nécessaire
    if isinstance(cached_result, list):
        # Si la liste a plusieurs éléments ou est vide, c'est une liste originale
        if len(cached_result) != 1:
            return cached_result
        # Si la liste a un seul élément, vérifier si c'est un wrapper normalisé
        single_item = cached_result[0]
        if isinstance(single_item, dict) and "_type" in single_item:
            # C'est un wrapper normalisé avec métadonnée de type
            original_type = single_item["_type"]
            value = single_item["value"]

            # Vérifier si c'est une valeur originale (list ou dict) à préserver
            if single_item.get("_original", False):
                if original_type == "list":
                    # Liste originale avec un seul élément
                    return value
                elif original_type == "dict":
                    # Dict original (même s'il contient "value")
                    return value

            # Restaurer le type original pour les wrappers normalisés
            if original_type == "tuple":
                return tuple(value)
            elif original_type == "set":
                return set(value)
            elif original_type == "int":
                return int(value)
            elif original_type == "float":
                return float(value)
            elif original_type == "str":
                return str(value)
            elif original_type == "bool":
                return bool(value)
            elif original_type == "NoneType" or value is None:
                return None
            else:
                # Type non géré, retourner la valeur telle quelle
                return value
        else:
            # C'est un dict unique qui était le résultat original
            return single_item

    return cached_result


def _normalize_result_for_cache(result: Any) -> list:
    """
    Normalise le résultat pour le stockage dans le cache (toujours stocker comme liste)

    Args:
        result: Résultat à normaliser

    Returns:
        Liste normalisée pour le cache avec métadonnées de type
    """
    if isinstance(result, list):
        # Liste : si un seul élément, marquer comme liste originale
        if len(result) == 1:
            return [{"_type": "list", "_original": True, "value": result}]
        # Liste avec plusieurs éléments ou vide : retourner telle quelle
        return result
    elif isinstance(result, tuple):
        # Tuple : stocker avec métadonnée de type pour le restaurer
        return [{"_type": "tuple", "value": list(result)}]
    elif isinstance(result, dict):
        # Dict : retourner dans une liste avec marqueur pour distinguer des wrappers
        return [{"_type": "dict", "_original": True, "value": result}]
    elif isinstance(result, set):
        # Set : stocker comme liste avec métadonnée de type
        return [{"_type": "set", "value": list(result)}]
    else:
        # Types simples (int, str, float, bool, None) : envelopper avec métadonnée de type
        return [{"_type": type(result).__name__, "value": result}]


def _save_to_cache(cache_instance: SimpleCache | Any, cache_key: str, result: Any) -> None:
    """
    Sauvegarde le résultat dans le cache

    Args:
        cache_instance: Instance du cache
        cache_key: Clé du cache
        result: Résultat à mettre en cache
    """
    cache_data = _normalize_result_for_cache(result)
    try:
        cache_instance.set(cache_key, cache_data)
    except Exception as e:
        logger.warning(f"Erreur lors de la mise en cache: {e}")


def _try_get_from_cache(
    func_name: str,
    cache_key_prefix: str | None,
    expiry_hours: int | None,
    args: tuple,
    kwargs: dict,
) -> tuple[SimpleCache | None, str | None, Any | None]:
    """
    Essaie de récupérer le résultat depuis le cache

    Args:
        func_name: Nom de la fonction
        cache_key_prefix: Préfixe optionnel pour la clé
        expiry_hours: Durée de vie personnalisée du cache
        args: Arguments positionnels
        kwargs: Arguments nommés

    Returns:
        Tuple (cache_instance, cache_key, cached_result)
        Si le cache n'est pas disponible, retourne (None, None, None)
        Si le résultat n'est pas en cache, retourne (cache_instance, cache_key, None)
    """
    cache_instance = _get_cache_instance(expiry_hours)
    if cache_instance is None:
        return None, None, None

    cache_key = _generate_cache_key(func_name, cache_key_prefix, args, kwargs)
    cached_result = _get_cached_result(cache_instance, cache_key)

    return cache_instance, cache_key, cached_result


def cached(cache_key_prefix: str | None = None, expiry_hours: int | None = None):
    """
    Décorateur pour mettre en cache automatiquement les résultats d'une méthode
    Supporte les fonctions synchrones et asynchrones

    Utilise CacheManager pour accéder au cache statique

    Args:
        cache_key_prefix: Préfixe pour la clé de cache (utilise le nom de la fonction si None)
        expiry_hours: Durée de vie du cache en heures (utilise celle du cache statique si None)

    Usage:
        @cached()
        def my_method(self, param1, param2):
            # ...

        @cached()
        async def my_async_method(self, param1, param2):
            # ...
    """

    def decorator(func: Callable) -> Callable:
        is_async = inspect.iscoroutinefunction(func)

        if is_async:

            @functools.wraps(func)
            async def async_wrapper(self, *args, **kwargs):
                cache_instance, cache_key, cached_result = _try_get_from_cache(
                    func.__name__, cache_key_prefix, expiry_hours, args, kwargs
                )

                if cached_result is not None:
                    return cached_result

                if cache_instance is None:
                    return await func(self, *args, **kwargs)

                # Exécuter la méthode et mettre en cache le résultat
                result = await func(self, *args, **kwargs)
                _save_to_cache(cache_instance, cache_key, result)
                return result

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(self, *args, **kwargs):
                cache_instance, cache_key, cached_result = _try_get_from_cache(
                    func.__name__, cache_key_prefix, expiry_hours, args, kwargs
                )

                if cached_result is not None:
                    return cached_result

                if cache_instance is None:
                    return func(self, *args, **kwargs)

                # Exécuter la méthode et mettre en cache le résultat
                result = func(self, *args, **kwargs)
                _save_to_cache(cache_instance, cache_key, result)
                return result

            return sync_wrapper

    return decorator
