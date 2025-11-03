"""
Gestionnaire de cache statique pour l'application
"""

from typing import Optional
from .simple_cache import SimpleCache


class CacheManager:
    """Gestionnaire de cache statique"""

    _instance: Optional[SimpleCache] = None

    @classmethod
    def initialize(cls, cache: SimpleCache):
        """
        Initialise le gestionnaire de cache

        Args:
            cache: Instance de SimpleCache à utiliser
        """
        cls._instance = cache

    @classmethod
    def get_instance(cls) -> Optional[SimpleCache]:
        """
        Retourne l'instance du cache

        Returns:
            Instance de SimpleCache ou None si non initialisée
        """
        return cls._instance

    @classmethod
    def is_initialized(cls) -> bool:
        """
        Vérifie si le cache est initialisé

        Returns:
            True si le cache est initialisé, False sinon
        """
        return cls._instance is not None
