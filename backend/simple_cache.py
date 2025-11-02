"""
Cache simple basé sur des fichiers JSON
"""

import os
import json
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any


class SimpleCache:
    """Cache simple utilisant des fichiers JSON locaux"""

    def __init__(self, cache_dir: str = "cache", expiry_hours: int = 24):
        """
        Initialise le cache

        Args:
            cache_dir: Répertoire où stocker les fichiers de cache
            expiry_hours: Durée de vie du cache en heures
        """
        self.cache_dir = cache_dir
        self.expiry_hours = expiry_hours

        # Créer le répertoire de cache s'il n'existe pas
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_cache_file(self, key: str) -> str:
        """Retourne le chemin du fichier de cache pour une clé"""
        safe_key = key.replace("/", "_").replace("\\", "_")
        return os.path.join(self.cache_dir, f"{safe_key}.json")

    def _get_metadata_file(self) -> str:
        """Retourne le chemin du fichier de métadonnées"""
        return os.path.join(self.cache_dir, "metadata.json")

    def is_valid(self, key: str) -> bool:
        """
        Vérifie si le cache pour une clé est encore valide

        Args:
            key: Clé du cache

        Returns:
            True si le cache est valide, False sinon
        """
        metadata_file = self._get_metadata_file()

        if not os.path.exists(metadata_file):
            return False

        try:
            with open(metadata_file, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            if key not in metadata:
                return False

            last_updated_str = metadata[key].get("last_updated")
            if not last_updated_str:
                return False

            last_updated = datetime.fromisoformat(last_updated_str)
            # S'assurer que la date est timezone-aware
            if last_updated.tzinfo is None:
                last_updated = last_updated.replace(tzinfo=timezone.utc)
            expiry_time = last_updated + timedelta(hours=self.expiry_hours)

            return datetime.now(timezone.utc) < expiry_time
        except (json.JSONDecodeError, KeyError, ValueError) as e:
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

        cache_file = self._get_cache_file(key)

        if not os.path.exists(cache_file):
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("items", [])
        except (json.JSONDecodeError, IOError) as e:
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
        cache_file = self._get_cache_file(key)
        metadata_file = self._get_metadata_file()

        # Sauvegarder les données
        cache_data = {
            "key": key,
            "items": items,
            "cached_at": datetime.now(timezone.utc).isoformat(),
        }

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise Exception(f"Erreur lors de l'écriture du cache: {e}")

        # Mettre à jour les métadonnées
        metadata_data = {}
        if os.path.exists(metadata_file):
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    metadata_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                metadata_data = {}

        metadata_data[key] = {
            "last_updated": datetime.now(timezone.utc).isoformat(),
            "count": len(items),
            "metadata": metadata or {},
        }

        try:
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise Exception(f"Erreur lors de l'écriture des métadonnées: {e}")

    def clear(self, key: Optional[str] = None):
        """
        Vide le cache pour une clé spécifique ou tout le cache

        Args:
            key: Clé à supprimer, ou None pour tout supprimer
        """
        if key:
            cache_file = self._get_cache_file(key)
            if os.path.exists(cache_file):
                os.remove(cache_file)

            metadata_file = self._get_metadata_file()
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, "r", encoding="utf-8") as f:
                        metadata_data = json.load(f)
                    if key in metadata_data:
                        del metadata_data[key]
                    with open(metadata_file, "w", encoding="utf-8") as f:
                        json.dump(metadata_data, f, indent=2, ensure_ascii=False)
                except (json.JSONDecodeError, IOError):
                    pass
        else:
            # Supprimer tout le répertoire de cache
            import shutil

            if os.path.exists(self.cache_dir):
                shutil.rmtree(self.cache_dir)
                os.makedirs(self.cache_dir, exist_ok=True)
