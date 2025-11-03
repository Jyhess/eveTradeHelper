"""
Client pour l'API ESI (Eve Swagger Interface) d'Eve Online
Version asynchrone avec httpx
"""

import httpx
import logging
from typing import List, Dict, Any, Optional
from utils.cache import cached

logger = logging.getLogger(__name__)


class EveAPIClient:
    """Client pour interagir avec l'API ESI d'Eve Online (asynchrone)"""

    def __init__(
        self,
        base_url: str = "https://esi.evetech.net/latest",
        timeout: int = 10,
    ):
        """
        Initialise le client API

        Args:
            base_url: URL de base de l'API ESI
            timeout: Timeout pour les requêtes en secondes
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtient ou crée un client HTTP asynchrone"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Ferme le client HTTP"""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _get(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Effectue une requête GET vers l'API (asynchrone)

        Args:
            endpoint: Chemin de l'endpoint (ex: "/universe/regions/")
            params: Paramètres de requête optionnels

        Returns:
            Réponse JSON de l'API

        Raises:
            Exception: Si la requête échoue
        """
        url = f"{self.base_url}{endpoint}"
        client = await self._get_client()

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise Exception(f"Timeout lors de l'appel à l'API: {url}")
        except httpx.HTTPStatusError as e:
            raise Exception(
                f"Erreur HTTP {e.response.status_code} lors de l'appel à {url}: {e}"
            )
        except httpx.RequestError as e:
            raise Exception(f"Erreur de connexion à l'API {url}: {e}")

    @cached()
    async def get_regions_list(self) -> List[int]:
        """
        Récupère la liste des IDs de régions

        Returns:
            Liste des IDs de régions

        Raises:
            Exception: Si l'appel API échoue
        """
        return await self._get("/universe/regions/")

    @cached()
    async def get_region_details(self, region_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une région

        Args:
            region_id: ID de la région

        Returns:
            Dictionnaire contenant les détails de la région

        Raises:
            Exception: Si l'appel API échoue
        """
        return await self._get(f"/universe/regions/{region_id}/")

    @cached()
    async def get_systems_list(self) -> List[int]:
        """
        Récupère la liste des IDs de systèmes solaires

        Returns:
            Liste des IDs de systèmes

        Raises:
            Exception: Si l'appel API échoue
        """
        return await self._get("/universe/systems/")

    @cached()
    async def get_constellation_details(self, constellation_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une constellation

        Args:
            constellation_id: ID de la constellation

        Returns:
            Dictionnaire contenant les détails de la constellation

        Raises:
            Exception: Si l'appel API échoue
        """
        return await self._get(f"/universe/constellations/{constellation_id}/")

    @cached()
    async def get_system_details(self, system_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'un système solaire

        Args:
            system_id: ID du système

        Returns:
            Dictionnaire contenant les détails du système

        Raises:
            Exception: Si l'appel API échoue
        """
        return await self._get(f"/universe/systems/{system_id}/")

    @cached()
    async def get_item_type(self, type_id: int) -> Dict[str, Any]:
        """
        Récupère les informations d'un type d'item

        Args:
            type_id: ID du type d'item

        Returns:
            Dictionnaire contenant les informations de l'item

        Raises:
            Exception: Si l'appel API échoue
        """
        return await self._get(f"/universe/types/{type_id}/")

    @cached()
    async def get_stargate_details(self, stargate_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une stargate (porte stellaire)

        Args:
            stargate_id: ID de la stargate

        Returns:
            Dictionnaire contenant les détails de la stargate

        Raises:
            Exception: Si l'appel API échoue
        """
        return await self._get(f"/universe/stargates/{stargate_id}/")

    @cached()
    async def get_station_details(self, station_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'une station

        Args:
            station_id: ID de la station

        Returns:
            Dictionnaire contenant les détails de la station

        Raises:
            Exception: Si l'appel API échoue
        """
        return await self._get(f"/universe/stations/{station_id}/")

    @cached()
    async def get_market_groups_list(self) -> List[int]:
        """
        Récupère la liste des IDs de groupes de marché

        Returns:
            Liste des IDs de groupes de marché

        Raises:
            Exception: Si l'appel API échoue
        """
        return await self._get("/markets/groups/")

    @cached()
    async def get_market_group_details(self, group_id: int) -> Dict[str, Any]:
        """
        Récupère les détails d'un groupe de marché

        Args:
            group_id: ID du groupe de marché

        Returns:
            Dictionnaire contenant les détails du groupe de marché

        Raises:
            Exception: Si l'appel API échoue
        """
        return await self._get(f"/markets/groups/{group_id}/")

    @cached(expiry_hours=1)
    async def get_market_orders(
        self, region_id: int, type_id: int = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère les ordres de marché pour une région, optionnellement filtrés par type

        Args:
            region_id: ID de la région
            type_id: Optionnel, ID du type d'item pour filtrer les ordres

        Returns:
            Liste des ordres de marché

        Raises:
            Exception: Si l'appel API échoue
        """
        params = {}
        if type_id:
            params["type_id"] = type_id
        return await self._get(f"/markets/{region_id}/orders/", params=params)

    @cached()
    async def get_route(
        self,
        origin: int,
        destination: int,
        avoid: List[int] = None,
        connections: List[List[int]] = None,
    ) -> List[int]:
        """
        Calcule la route entre deux systèmes

        Args:
            origin: ID du système d'origine
            destination: ID du système de destination
            avoid: Liste optionnelle d'IDs de systèmes à éviter
            connections: Liste optionnelle de paires de systèmes connectés

        Returns:
            Liste des IDs de systèmes formant la route (incluant origin et destination)
            Si pas de route trouvée, retourne une liste vide

        Raises:
            Exception: Si l'appel API échoue
        """
        params = {}
        if avoid:
            # L'API attend une liste d'IDs séparés par des virgules pour avoid
            params["avoid"] = ",".join(map(str, avoid))
        if connections:
            # Pour connections, l'API attend un format spécial, mais généralement pas utilisé
            # On pourrait l'implémenter si nécessaire
            pass

        try:
            route = await self._get(
                f"/route/{origin}/{destination}/", params=params if params else None
            )
            # L'API retourne une liste d'IDs de systèmes
            return route if isinstance(route, list) else []
        except Exception as e:
            logger.warning(
                f"Erreur lors du calcul de la route entre {origin} et {destination}: {e}"
            )
            return []

    async def search(
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
        return await self._get("/search/", params=params)
