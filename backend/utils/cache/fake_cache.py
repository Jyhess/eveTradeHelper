"""
Cache en mémoire pour les tests unitaires
Simule le comportement de SimpleCache sans connexion Redis
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any


class FakeCache:
    """Cache en mémoire pour les tests unitaires, simulant le comportement de SimpleCache"""

    def __init__(
        self,
        expiry_hours: int,
        redis_url: Optional[str] = None,
        redis_host: Optional[str] = None,
        redis_port: int = 6379,
        redis_db: int = 0,
    ):
        """
        Initialise le fake cache en mémoire

        Args:
            expiry_hours: Durée de vie du cache en heures
            redis_url: Ignoré (compatibilité avec SimpleCache)
            redis_host: Ignoré (compatibilité avec SimpleCache)
            redis_port: Ignoré (compatibilité avec SimpleCache)
            redis_db: Ignoré (compatibilité avec SimpleCache)
        """
        self.expiry_hours = expiry_hours
        self._cache_data: Dict[str, Dict[str, Any]] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}

    def is_valid(self, key: str) -> bool:
        """
        Vérifie si le cache pour une clé est encore valide

        Args:
            key: Clé du cache

        Returns:
            True si le cache est valide, False sinon
        """
        metadata_key = f"metadata:{key}"
        metadata = self._metadata.get(metadata_key)

        if not metadata:
            return False

        last_updated_str = metadata.get("last_updated")
        if not last_updated_str:
            return False

        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            expiry_time = last_updated + timedelta(hours=self.expiry_hours)
            return datetime.now(timezone.utc) < expiry_time
        except (ValueError, TypeError):
            return False

    def get(self, key: str) -> Optional[List[Dict[str, Any]]]:
        """
        Récupère les données depuis le cache

        Args:
            key: Clé du cache

        Returns:
            Les données en cache ou None si non disponible
        """
        if not self.is_valid(key):
            return None

        cache_key = f"cache:{key}"
        cache_data = self._cache_data.get(cache_key)
        if cache_data:
            return cache_data.get("items", [])
        return None

    def set(
        self, key: str, items: List[Dict[str, Any]], metadata: Optional[Dict] = None
    ):
        """
        Sauvegarde des données dans le cache

        Args:
            key: Clé du cache
            items: Liste des éléments à mettre en cache
            metadata: Métadonnées optionnelles (ex: region_ids)
        """
        now = datetime.now(timezone.utc)

        cache_key = f"cache:{key}"
        self._cache_data[cache_key] = {
            "key": key,
            "items": items,
            "cached_at": now.isoformat(),
        }

        metadata_key = f"metadata:{key}"
        self._metadata[metadata_key] = {
            "last_updated": now.isoformat(),
            "count": len(items),
            "metadata": metadata or {},
        }

    def clear(self, key: Optional[str] = None):
        """
        Vide le cache pour une clé spécifique ou tout le cache

        Args:
            key: Clé à supprimer, ou None pour tout supprimer
        """
        if key:
            cache_key = f"cache:{key}"
            metadata_key = f"metadata:{key}"
            self._cache_data.pop(cache_key, None)
            self._metadata.pop(metadata_key, None)
        else:
            self._cache_data.clear()
            self._metadata.clear()

