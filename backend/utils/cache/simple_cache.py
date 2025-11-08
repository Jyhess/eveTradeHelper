"""
Cache basé sur Redis
"""

import json
from datetime import UTC, datetime, timedelta
from typing import Any

try:
    import redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class SimpleCache:
    """Cache utilisant Redis"""

    def __init__(
        self,
        expiry_hours: int,
        redis_url: str | None = None,
        redis_host: str | None = None,
        redis_port: int = 6379,
        redis_db: int = 0,
    ):
        """
        Initialise le cache Redis

        Args:
            expiry_hours: Durée de vie du cache en heures
            redis_url: URL de connexion Redis (ex: redis://localhost:6379/0)
            redis_host: Host Redis (ignoré si redis_url est fourni)
            redis_port: Port Redis (ignoré si redis_url est fourni)
            redis_db: Base de données Redis (ignoré si redis_url est fourni)

        Raises:
            ImportError: Si redis-py n'est pas installé
            ConnectionError: Si la connexion à Redis échoue
        """
        if not REDIS_AVAILABLE:
            raise ImportError(
                "Redis est requis mais redis-py n'est pas installé. "
                "Installez-le avec: pip install redis"
            )

        self.expiry_hours = expiry_hours

        # Vérifier qu'au moins une configuration Redis est fournie
        if not redis_url and not redis_host:
            raise ValueError(
                "Redis est requis mais aucune configuration n'est fournie. "
                "Veuillez fournir REDIS_URL ou REDIS_HOST dans les variables d'environnement."
            )

        try:
            if redis_url:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    decode_responses=True,
                )
            # Test de connexion
            self.redis_client.ping()
        except redis.ConnectionError as e:
            raise ConnectionError(
                f"❌ Impossible de se connecter à Redis.\n"
                f"   Vérifiez que Redis est démarré avec: docker-compose up -d redis\n"
                f"   Ou démarrez le service Redis dans Docker: docker-compose up redis\n"
                f"   Détails de l'erreur: {e}"
            ) from e
        except Exception as e:
            raise ConnectionError(
                f"❌ Erreur lors de la connexion à Redis.\n"
                f"   Vérifiez que Redis est démarré avec: docker-compose up -d redis\n"
                f"   Détails de l'erreur: {e}"
            ) from e

    def is_valid(self, key: str) -> bool:
        """
        Vérifie si le cache pour une clé est encore valide

        Args:
            key: Clé du cache

        Returns:
            True si le cache est valide, False sinon
        """
        metadata_key = f"metadata:{key}"
        last_updated_str = self.redis_client.hget(metadata_key, "last_updated")

        if not last_updated_str:
            return False

        try:
            last_updated = datetime.fromisoformat(last_updated_str)
            # S'assurer que la date est timezone-aware
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=UTC)
            expiry_time = last_updated + timedelta(hours=self.expiry_hours)
            return datetime.now(UTC) < expiry_time
        except (ValueError, TypeError):
            return False

    def get(self, key: str) -> list[dict[str, Any]] | None:
        """
        Récupère les données depuis le cache

        Args:
            key: Clé du cache

        Returns:
            Les données en cache ou None si non disponible
        """
        if not self.is_valid(key):
            return None

        try:
            cache_data_str = self.redis_client.get(f"cache:{key}")
            if cache_data_str:
                cache_data = json.loads(cache_data_str)
                return cache_data.get("items", [])
            return None
        except (json.JSONDecodeError, Exception):
            return None

    def set(self, key: str, items: list[dict[str, Any]], metadata: dict | None = None):
        """
        Sauvegarde des données dans le cache

        Args:
            key: Clé du cache
            items: Liste des éléments à mettre en cache
            metadata: Métadonnées optionnelles (ex: region_ids)
        """
        now = datetime.now(UTC)

        # Sauvegarder les données
        cache_data = {
            "key": key,
            "items": items,
            "cached_at": now.isoformat(),
        }

        try:
            # Sauvegarder les données dans Redis
            cache_key = f"cache:{key}"
            self.redis_client.set(cache_key, json.dumps(cache_data, ensure_ascii=False))

            # Mettre à jour les métadonnées
            metadata_key = f"metadata:{key}"
            metadata_data = {
                "last_updated": now.isoformat(),
                "count": len(items),
                "metadata": json.dumps(metadata or {}, ensure_ascii=False),
            }
            self.redis_client.hset(metadata_key, mapping=metadata_data)
        except Exception as e:
            raise Exception(f"Erreur lors de l'écriture du cache Redis: {e}") from e

    def clear(self, key: str | None = None):
        """
        Vide le cache pour une clé spécifique ou tout le cache

        Args:
            key: Clé à supprimer, ou None pour tout supprimer
        """
        try:
            if key:
                cache_key = f"cache:{key}"
                metadata_key = f"metadata:{key}"
                self.redis_client.delete(cache_key, metadata_key)
            else:
                # Supprimer toutes les clés du cache
                for cache_key in self.redis_client.scan_iter(match="cache:*"):
                    self.redis_client.delete(cache_key)
                for metadata_key in self.redis_client.scan_iter(match="metadata:*"):
                    self.redis_client.delete(metadata_key)
        except Exception as e:
            raise Exception(f"Erreur lors de la suppression du cache Redis: {e}") from e
