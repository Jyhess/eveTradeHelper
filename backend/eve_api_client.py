"""
Client pour l'API ESI (Eve Swagger Interface) d'Eve Online
"""

import requests
from typing import List, Dict, Any, Optional
from datetime import datetime


class EveAPIClient:
    """Client pour interagir avec l'API ESI d'Eve Online"""

    def __init__(
        self, base_url: str = "https://esi.evetech.net/latest", timeout: int = 10
    ):
        """
        Initialise le client API

        Args:
            base_url: URL de base de l'API ESI
            timeout: Timeout pour les requêtes en secondes
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Effectue une requête GET vers l'API

        Args:
            endpoint: Chemin de l'endpoint (ex: "/universe/regions/")
            params: Paramètres de requête optionnels

        Returns:
            Réponse JSON de l'API

        Raises:
            requests.RequestException: Si la requête échoue
            Exception: Si le statut HTTP n'est pas 200
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.Timeout:
            raise Exception(f"Timeout lors de l'appel à l'API: {url}")
        except requests.HTTPError as e:
            raise Exception(
                f"Erreur HTTP {response.status_code} lors de l'appel à {url}: {e}"
            )
        except requests.RequestException as e:
            raise Exception(f"Erreur de connexion à l'API {url}: {e}")

    def get_regions_list(self) -> List[int]:
        """
        Récupère la liste des IDs de régions

        Returns:
            Liste des IDs de régions

        Raises:
            Exception: Si l'appel API échoue
        """
        return self._get("/universe/regions/")

    def get_region_details(self, region_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une région

        Args:
            region_id: ID de la région

        Returns:
            Dictionnaire contenant les détails de la région

        Raises:
            Exception: Si l'appel API échoue
        """
        return self._get(f"/universe/regions/{region_id}/")

    def get_regions_with_details(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère la liste des régions avec leurs détails

        Args:
            limit: Nombre maximum de régions à récupérer (None = toutes)

        Returns:
            Liste des régions avec leurs détails

        Raises:
            Exception: Si l'appel API échoue
        """
        # Récupérer la liste des IDs
        region_ids = self.get_regions_list()

        # Appliquer la limite si spécifiée
        if limit:
            region_ids = region_ids[:limit]

        # Récupérer les détails de chaque région
        regions = []
        for region_id in region_ids:
            try:
                region_data = self.get_region_details(region_id)
                regions.append(
                    {
                        "region_id": region_id,
                        "name": region_data.get("name", "Unknown"),
                        "description": region_data.get("description", ""),
                        "constellations": region_data.get("constellations", []),
                    }
                )
            except Exception as e:
                # Logger l'erreur mais continuer avec les autres régions
                import logging

                logging.warning(
                    f"Erreur lors de la récupération de la région {region_id}: {e}"
                )
                continue

        return regions

    def get_constellation_details(self, constellation_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une constellation

        Args:
            constellation_id: ID de la constellation

        Returns:
            Dictionnaire contenant les détails de la constellation

        Raises:
            Exception: Si l'appel API échoue
        """
        return self._get(f"/universe/constellations/{constellation_id}/")

    def get_system_details(self, system_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'un système solaire

        Args:
            system_id: ID du système

        Returns:
            Dictionnaire contenant les détails du système

        Raises:
            Exception: Si l'appel API échoue
        """
        return self._get(f"/universe/systems/{system_id}/")

    def get_item_type(self, type_id: int) -> Dict[str, Any]:
        """
        Récupère les informations d'un type d'item

        Args:
            type_id: ID du type d'item

        Returns:
            Dictionnaire contenant les informations de l'item

        Raises:
            Exception: Si l'appel API échoue
        """
        return self._get(f"/universe/types/{type_id}/")

    def get_market_prices(self, region_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les prix de marché pour une région

        Args:
            region_id: ID de la région

        Returns:
            Liste des prix de marché

        Raises:
            Exception: Si l'appel API échoue
        """
        return self._get(f"/markets/{region_id}/orders/")

    def search(
        self, categories: List[str], search: str, strict: bool = False
    ) -> Dict[str, Any]:
        """
        Effectue une recherche dans l'univers d'Eve

        Args:
            categories: Catégories de recherche (ex: ["region", "system"])
            search: Terme de recherche
            strict: Si True, recherche exacte uniquement

        Returns:
            Résultats de la recherche

        Raises:
            Exception: Si l'appel API échoue
        """
        params = {
            "categories": ",".join(categories),
            "search": search,
            "strict": str(strict).lower(),
        }
        return self._get("/search/", params=params)
