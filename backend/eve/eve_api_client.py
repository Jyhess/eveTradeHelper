"""
Client pour l'API ESI (Eve Swagger Interface) d'Eve Online
Version asynchrone avec httpx
"""

import asyncio
import httpx
import logging
import time
from typing import List, Dict, Any, Optional
from collections import deque
from utils.cache import cached

logger = logging.getLogger(__name__)


class EveAPIClient:
    """Client pour interagir avec l'API ESI d'Eve Online (asynchrone)"""

    def __init__(
        self,
        base_url: str = "https://esi.evetech.net/latest",
        timeout: int = 10,
        rate_limit_per_second: int = 60,
    ):
        """
        Initialise le client API

        Args:
            base_url: URL de base de l'API ESI
            timeout: Timeout pour les requêtes en secondes
            rate_limit_per_second: Nombre maximum de requêtes par seconde (défaut: 20)
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.rate_limit_per_second = rate_limit_per_second
        self._client: Optional[httpx.AsyncClient] = None

        # Rate limiting: garder les timestamps des dernières requêtes
        self._request_timestamps: deque = deque()
        self._rate_limit_lock: Optional[asyncio.Lock] = None

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

    async def _wait_for_rate_limit(self):
        """
        Attend si nécessaire pour respecter le rate limit
        Utilise une fenêtre glissante de 1 seconde
        """
        # Initialiser le lock de manière lazy (nécessaire car asyncio.Lock() ne peut pas être créé en dehors d'une event loop)
        if self._rate_limit_lock is None:
            self._rate_limit_lock = asyncio.Lock()

        async with self._rate_limit_lock:
            now = time.time()

            # Supprimer les timestamps de plus d'1 seconde
            while self._request_timestamps and self._request_timestamps[0] < now - 1.0:
                self._request_timestamps.popleft()

            # Si on a atteint la limite, attendre jusqu'à ce qu'une requête sorte de la fenêtre
            if len(self._request_timestamps) >= self.rate_limit_per_second:
                oldest_timestamp = self._request_timestamps[0]
                wait_time = 1.0 - (now - oldest_timestamp)
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    # Nettoyer à nouveau après l'attente
                    now = time.time()
                    while (
                        self._request_timestamps
                        and self._request_timestamps[0] < now - 1.0
                    ):
                        self._request_timestamps.popleft()

            # Ajouter le timestamp de cette requête
            self._request_timestamps.append(time.time())

    async def _get(
        self, endpoint: str, params: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Effectue une requête GET vers l'API (asynchrone)
        Respecte automatiquement le rate limit configuré

        Args:
            endpoint: Chemin de l'endpoint (ex: "/universe/regions/")
            params: Paramètres de requête optionnels

        Returns:
            Réponse JSON de l'API

        Raises:
            Exception: Si la requête échoue
        """
        # Respecter le rate limit avant de faire la requête
        await self._wait_for_rate_limit()

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

    @cached()
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
