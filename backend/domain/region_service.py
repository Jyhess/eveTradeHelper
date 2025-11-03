"""
Service de domaine pour la gestion des régions
Contient la logique métier pure, indépendante de l'infrastructure (version asynchrone)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from .repository import EveRepository

logger = logging.getLogger(__name__)


class RegionService:
    """Service de domaine pour les régions d'Eve Online (asynchrone)"""

    def __init__(self, repository: EveRepository):
        """
        Initialise le service avec un repository

        Args:
            repository: Implémentation du repository Eve
        """
        self.repository = repository

    async def get_regions_with_details(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère la liste des régions avec leurs détails
        Logique métier : orchestration des appels au repository (parallélisée)

        Args:
            limit: Nombre maximum de régions à récupérer (None = toutes)

        Returns:
            Liste des régions avec leurs détails formatés

        Raises:
            Exception: Si une erreur survient lors de la récupération
        """
        # Récupérer la liste des IDs depuis le repository
        region_ids = await self.repository.get_regions_list()

        # Appliquer la limite si spécifiée (logique métier)
        if limit:
            region_ids = region_ids[:limit]

        # Récupérer les détails de chaque région en parallèle
        async def fetch_region(region_id: int) -> Optional[Dict[str, Any]]:
            try:
                region_data = await self.repository.get_region_details(region_id)
                return {
                    "region_id": region_id,
                    "name": region_data.get("name", "Unknown"),
                    "description": region_data.get("description", ""),
                    "constellations": region_data.get("constellations", []),
                }
            except Exception as e:
                # Logger l'erreur mais continuer avec les autres régions
                logger.warning(
                    f"Erreur lors de la récupération de la région {region_id}: {e}"
                )
                return None

        # Exécuter toutes les requêtes en parallèle
        results = await asyncio.gather(*[fetch_region(rid) for rid in region_ids])

        # Filtrer les résultats None
        regions = [r for r in results if r is not None]
        return regions

    async def get_region_constellations_with_details(
        self, region_id: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère les détails de toutes les constellations d'une région
        Logique métier : orchestration des appels au repository (parallélisée)

        Args:
            region_id: ID de la région

        Returns:
            Liste des constellations avec leurs détails formatés

        Raises:
            Exception: Si une erreur survient lors de la récupération
        """
        # Récupérer les détails de la région pour obtenir les IDs des constellations
        region_data = await self.repository.get_region_details(region_id)
        constellation_ids = region_data.get("constellations", [])

        # Récupérer les détails de chaque constellation en parallèle
        async def fetch_constellation(
            constellation_id: int,
        ) -> Optional[Dict[str, Any]]:
            try:
                constellation_data = await self.repository.get_constellation_details(
                    constellation_id
                )
                return {
                    "constellation_id": constellation_id,
                    "name": constellation_data.get("name", "Unknown"),
                    "systems": constellation_data.get("systems", []),
                    "position": constellation_data.get("position", {}),
                }
            except Exception as e:
                logger.warning(
                    f"Erreur lors de la récupération de la constellation {constellation_id}: {e}"
                )
                return None

        # Exécuter toutes les requêtes en parallèle
        results = await asyncio.gather(
            *[fetch_constellation(cid) for cid in constellation_ids]
        )

        # Filtrer les résultats None
        constellations = [c for c in results if c is not None]
        return constellations

    async def get_constellation_systems_with_details(
        self, constellation_id: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère les détails de tous les systèmes d'une constellation
        Logique métier : orchestration des appels au repository (parallélisée)

        Args:
            constellation_id: ID de la constellation

        Returns:
            Liste des systèmes avec leurs détails formatés

        Raises:
            Exception: Si une erreur survient lors de la récupération
        """
        # Récupérer les détails de la constellation pour obtenir les IDs des systèmes
        constellation_data = await self.repository.get_constellation_details(
            constellation_id
        )
        system_ids = constellation_data.get("systems", [])

        # Récupérer les détails de chaque système en parallèle
        async def fetch_system(system_id: int) -> Optional[Dict[str, Any]]:
            try:
                system_data = await self.repository.get_system_details(system_id)
                return {
                    "system_id": system_id,
                    "name": system_data.get("name", "Unknown"),
                    "security_status": system_data.get("security_status", 0.0),
                    "security_class": system_data.get("security_class", ""),
                    "position": system_data.get("position", {}),
                    "constellation_id": system_data.get("constellation_id"),
                    "planets": system_data.get("planets", []),
                    "star_id": system_data.get("star_id"),
                }
            except Exception as e:
                logger.warning(
                    f"Erreur lors de la récupération du système {system_id}: {e}"
                )
                return None

        # Exécuter toutes les requêtes en parallèle
        results = await asyncio.gather(*[fetch_system(sid) for sid in system_ids])

        # Filtrer les résultats None
        systems = [s for s in results if s is not None]
        return systems

    async def get_system_connections(self, system_id: int) -> List[Dict[str, Any]]:
        """
        Récupère les systèmes connectés à un système donné via les stargates
        Logique métier : orchestration des appels au repository

        Args:
            system_id: ID du système

        Returns:
            Liste des systèmes connectés avec leurs détails

        Raises:
            Exception: Si une erreur survient lors de la récupération
        """
        # Récupérer les détails du système pour obtenir les IDs des stargates
        system_data = await self.repository.get_system_details(system_id)
        stargate_ids = system_data.get("stargates", [])

        # Récupérer la constellation et la région du système source pour comparaison
        source_constellation_id = system_data.get("constellation_id")
        source_region_id = None
        if source_constellation_id:
            source_constellation = await self.repository.get_constellation_details(
                source_constellation_id
            )
            source_region_id = source_constellation.get("region_id")

        # Fonction pour récupérer les détails d'une connexion
        async def fetch_connection(stargate_id: int) -> Optional[Dict[str, Any]]:
            try:
                stargate_data = await self.repository.get_stargate_details(stargate_id)
                destination = stargate_data.get("destination", {})
                destination_system_id = destination.get("system_id")

                if destination_system_id and destination_system_id != system_id:
                    # Récupérer les détails du système de destination
                    destination_system = await self.repository.get_system_details(
                        destination_system_id
                    )
                    destination_constellation_id = destination_system.get(
                        "constellation_id"
                    )

                    # Déterminer si le système est dans la même constellation/région
                    same_constellation = (
                        destination_constellation_id == source_constellation_id
                    )
                    same_region = False
                    destination_region_id = None
                    destination_constellation_name = None
                    destination_region_name = None

                    if destination_constellation_id:
                        destination_constellation = (
                            await self.repository.get_constellation_details(
                                destination_constellation_id
                            )
                        )
                        destination_region_id = destination_constellation.get(
                            "region_id"
                        )
                        destination_constellation_name = destination_constellation.get(
                            "name", "Unknown"
                        )
                        same_region = destination_region_id == source_region_id

                        # Récupérer le nom de la région si différente
                        if destination_region_id and not same_region:
                            destination_region = (
                                await self.repository.get_region_details(
                                    destination_region_id
                                )
                            )
                            destination_region_name = destination_region.get(
                                "name", "Unknown"
                            )

                    return {
                        "system_id": destination_system_id,
                        "name": destination_system.get("name", "Unknown"),
                        "security_status": destination_system.get(
                            "security_status", 0.0
                        ),
                        "security_class": destination_system.get("security_class", ""),
                        "stargate_id": stargate_id,
                        "constellation_id": destination_constellation_id,
                        "constellation_name": destination_constellation_name,
                        "region_id": destination_region_id,
                        "region_name": destination_region_name,
                        "same_constellation": same_constellation,
                        "same_region": same_region,
                    }
            except Exception as e:
                logger.warning(
                    f"Erreur lors de la récupération de la stargate {stargate_id}: {e}"
                )
                return None

            return None

        # Exécuter toutes les requêtes en parallèle
        results = await asyncio.gather(*[fetch_connection(sid) for sid in stargate_ids])

        # Filtrer les résultats None
        connected_systems = [c for c in results if c is not None]
        return connected_systems

    async def get_system_details(self, system_id: int) -> Dict[str, Any]:
        return await self.repository.get_system_details(system_id)

    async def get_constellation_details(self, constellation_id: int) -> Dict[str, Any]:
        return await self.repository.get_constellation_details(constellation_id)

    async def get_region_details(self, region_id: int) -> Dict[str, Any]:
        return await self.repository.get_region_details(region_id)
