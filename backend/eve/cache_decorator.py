"""
Décorateur pour mettre en cache automatiquement les résultats des méthodes
"""

import functools
import hashlib
import json
from typing import Callable, Any, Optional
from eve.cache_manager import CacheManager


def cached(cache_key_prefix: Optional[str] = None, expiry_hours: Optional[int] = None):
    """
    Décorateur pour mettre en cache automatiquement les résultats d'une méthode

    Utilise CacheManager pour accéder au cache statique

    Args:
        cache_key_prefix: Préfixe pour la clé de cache (utilise le nom de la fonction si None)
        expiry_hours: Durée de vie du cache en heures (utilise celle du cache statique si None)

    Usage:
        @cached()
        def my_method(self, param1, param2):
            # ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Vérifier si le cache est disponible via CacheManager
            if not CacheManager.is_initialized():
                # Pas de cache, exécuter directement
                return func(self, *args, **kwargs)

            cache_instance = CacheManager.get_instance()

            # Créer une clé de cache unique basée sur le nom de la fonction et ses paramètres
            prefix = cache_key_prefix or func.__name__
            cache_key_parts = [prefix]

            # Ajouter les arguments positionnels (ignorer 'self')
            if args:
                args_str = str(args) if len(args) > 0 else ""
                cache_key_parts.append(args_str)

            # Ajouter les arguments nommés
            if kwargs:
                # Trier les kwargs pour garantir un ordre cohérent
                sorted_kwargs = sorted(kwargs.items())
                cache_key_parts.append(str(sorted_kwargs))

            # Créer une clé de cache hashée pour éviter les noms trop longs
            cache_key_raw = "_".join(str(part) for part in cache_key_parts)
            cache_key_hash = hashlib.md5(cache_key_raw.encode()).hexdigest()
            cache_key = f"{prefix}_{cache_key_hash}"

            # Créer une instance temporaire si expiry_hours est différent
            if expiry_hours and expiry_hours != cache_instance.expiry_hours:
                from eve.simple_cache import SimpleCache

                cache_instance = SimpleCache(
                    cache_dir=cache_instance.cache_dir, expiry_hours=expiry_hours
                )

            # Vérifier si le cache existe et est valide
            if cache_instance.is_valid(cache_key):
                cached_result = cache_instance.get(cache_key)
                if cached_result is not None:
                    # Le cache stocke une liste, récupérer le premier élément si nécessaire
                    if isinstance(cached_result, list):
                        # Si c'est une liste d'un seul élément et que la fonction retourne un dict/liste unique
                        # On retourne la liste complète ou le premier élément selon le contexte
                        return (
                            cached_result
                            if len(cached_result) > 1
                            else cached_result[0]
                        )
                    return cached_result

            # Le cache est invalide ou n'existe pas, exécuter la méthode
            result = func(self, *args, **kwargs)

            # Mettre en cache le résultat
            # Normaliser le résultat pour le cache (toujours stocker comme liste)
            if isinstance(result, list):
                cache_data = result
            elif isinstance(result, dict):
                cache_data = [result]
            else:
                # Pour les types simples (int, str, etc.), les envelopper
                cache_data = [{"value": result}]

            try:
                cache_instance.set(cache_key, cache_data)
            except Exception as e:
                # Si la mise en cache échoue, continuer quand même
                import logging

                logging.warning(f"Erreur lors de la mise en cache: {e}")

            return result

        return wrapper

    return decorator

