"""
Client pour l'API ESI (Eve Swagger Interface) d'Eve Online
Version asynchrone avec httpx
"""

import asyncio
import logging
import time
from collections import deque
from typing import Any

import httpx

from domain.constants import DEFAULT_API_MAX_RETRIES, DEFAULT_API_RETRY_DELAY_SECONDS
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
        self._client: httpx.AsyncClient | None = None

        # Rate limiting: garder les timestamps des dernières requêtes
        self._request_timestamps: deque = deque()
        self._rate_limit_lock: asyncio.Lock | None = None

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
                    while self._request_timestamps and self._request_timestamps[0] < now - 1.0:
                        self._request_timestamps.popleft()

            # Ajouter le timestamp de cette requête
            self._request_timestamps.append(time.time())

    def _create_exception_from_httpx_error(self, error: Exception, url: str) -> Exception:
        """
        Crée une exception appropriée à partir d'une erreur httpx

        Args:
            error: Exception httpx
            url: URL de la requête

        Returns:
            Exception formatée
        """
        if isinstance(error, httpx.TimeoutException):
            return Exception(f"Timeout lors de l'appel à l'API: {url}")
        elif isinstance(error, httpx.HTTPStatusError):
            return Exception(
                f"Erreur HTTP {error.response.status_code} lors de l'appel à {url}: {error}"
            )
        elif isinstance(error, httpx.RequestError):
            return Exception(f"Erreur de connexion à l'API {url}: {error}")
        else:
            return Exception(f"Erreur inattendue lors de l'appel à {url}: {error}")

    def _get_error_message(self, error: Exception, url: str) -> str:
        """
        Génère un message d'erreur formaté pour le logging

        Args:
            error: Exception httpx
            url: URL de la requête

        Returns:
            Message d'erreur formaté
        """
        if isinstance(error, httpx.TimeoutException):
            return f"Timeout lors de l'appel à {url}"
        elif isinstance(error, httpx.HTTPStatusError):
            return f"Erreur HTTP {error.response.status_code} lors de l'appel à {url}"
        elif isinstance(error, httpx.RequestError):
            return f"Erreur de connexion à {url}"
        else:
            return f"Erreur inattendue lors de l'appel à {url}"

    async def _execute_request_with_retry(
        self, url: str, params: dict | None, max_retries: int
    ) -> dict[str, Any]:
        """
        Exécute une requête HTTP avec retry automatique

        Args:
            url: URL complète de la requête
            params: Paramètres de requête optionnels
            max_retries: Nombre maximum de tentatives supplémentaires

        Returns:
            Réponse JSON de l'API

        Raises:
            Exception: Si la requête échoue après toutes les tentatives
        """
        client = await self._get_client()

        for attempt in range(max_retries + 1):
            try:
                await self._wait_for_rate_limit()
                response = await client.get(url, params=params)
                response.raise_for_status()
                return response.json()
            except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.RequestError) as e:
                exception = self._create_exception_from_httpx_error(e, url)

                if attempt < max_retries:
                    error_message = self._get_error_message(e, url)
                    logger.warning(
                        f"{error_message} (tentative {attempt + 1}/{max_retries + 1}). Nouvelle tentative..."
                    )
                    await asyncio.sleep(DEFAULT_API_RETRY_DELAY_SECONDS)
                else:
                    raise exception from None

        raise Exception(f"Erreur inattendue lors de l'appel à {url}")

    async def _get(
        self,
        endpoint: str,
        params: dict | None = None,
        max_retries: int = DEFAULT_API_MAX_RETRIES,
    ) -> dict[str, Any]:
        """
        Effectue une requête GET vers l'API (asynchrone)
        Respecte automatiquement le rate limit configuré
        Réessaie automatiquement en cas d'erreur

        Args:
            endpoint: Chemin de l'endpoint (ex: "/universe/regions/")
            params: Paramètres de requête optionnels
            max_retries: Nombre maximum de tentatives supplémentaires en cas d'erreur

        Returns:
            Réponse JSON de l'API

        Raises:
            Exception: Si la requête échoue après toutes les tentatives
        """
        url = f"{self.base_url}{endpoint}"
        return await self._execute_request_with_retry(url, params, max_retries)

    @cached()
    async def get_regions_list(self) -> list[int]:
        """
        Récupère la liste des IDs de régions

        Returns:
            Liste des IDs de régions

        Raises:
            Exception: Si l'appel API échoue
        """
        result = await self._get("/universe/regions/")
        return result if isinstance(result, list) else []

    @cached()
    async def get_region_details(self, region_id: int) -> dict[str, Any]:
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
    async def get_systems_list(self) -> list[int]:
        """
        Récupère la liste des IDs de systèmes solaires

        Returns:
            Liste des IDs de systèmes

        Raises:
            Exception: Si l'appel API échoue
        """
        result = await self._get("/universe/systems/")
        return result if isinstance(result, list) else []

    @cached()
    async def get_constellation_details(self, constellation_id: int) -> dict[str, Any]:
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
    async def get_system_details(self, system_id: int) -> dict[str, Any]:
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
    async def get_item_type(self, type_id: int) -> dict[str, Any]:
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
    async def get_stargate_details(self, stargate_id: int) -> dict[str, Any]:
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
    async def get_station_details(self, station_id: int) -> dict[str, Any]:
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
    async def get_market_groups_list(self) -> list[int]:
        """
        Récupère la liste des IDs de groupes de marché

        Returns:
            Liste des IDs de groupes de marché

        Raises:
            Exception: Si l'appel API échoue
        """
        result = await self._get("/markets/groups/")
        return result if isinstance(result, list) else []

    @cached()
    async def get_market_group_details(self, group_id: int) -> dict[str, Any]:
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
        self, region_id: int, type_id: int | None = None
    ) -> list[dict[str, Any]]:
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
        result = await self._get(f"/markets/{region_id}/orders/", params=params)
        return result if isinstance(result, list) else []

    @cached()
    async def get_route(
        self,
        origin: int,
        destination: int,
        avoid: list[int] | None = None,
        connections: list[list[int]] | None = None,
    ) -> list[int]:
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
        self, categories: list[str], search: str, strict: bool = False
    ) -> dict[str, Any]:
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
