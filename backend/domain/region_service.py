"""
Service de domaine pour la gestion des régions
Contient la logique métier pure, indépendante de l'infrastructure
"""

from typing import List, Dict, Any, Optional
from .repository import EveRepository


class RegionService:
    """Service de domaine pour les régions d'Eve Online"""

    def __init__(self, repository: EveRepository):
        """
        Initialise le service avec un repository

        Args:
            repository: Implémentation du repository Eve
        """
        self.repository = repository

    def get_regions_with_details(
        self, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Récupère la liste des régions avec leurs détails
        Logique métier : orchestration des appels au repository

        Args:
            limit: Nombre maximum de régions à récupérer (None = toutes)

        Returns:
            Liste des régions avec leurs détails formatés

        Raises:
            Exception: Si une erreur survient lors de la récupération
        """
        # Récupérer la liste des IDs depuis le repository
        region_ids = self.repository.get_regions_list()

        # Appliquer la limite si spécifiée (logique métier)
        if limit:
            region_ids = region_ids[:limit]

        # Récupérer les détails de chaque région
        regions = []
        for region_id in region_ids:
            try:
                region_data = self.repository.get_region_details(region_id)
                # Transformation des données selon le besoin métier
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
                # C'est une décision métier : on ne fait pas échouer toute la requête
                import logging

                logging.warning(
                    f"Erreur lors de la récupération de la région {region_id}: {e}"
                )
                continue

        return regions

    def get_region_constellations_with_details(
        self, region_id: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère les détails de toutes les constellations d'une région
        Logique métier : orchestration des appels au repository

        Args:
            region_id: ID de la région

        Returns:
            Liste des constellations avec leurs détails formatés

        Raises:
            Exception: Si une erreur survient lors de la récupération
        """
        # Récupérer les détails de la région pour obtenir les IDs des constellations
        region_data = self.repository.get_region_details(region_id)
        constellation_ids = region_data.get("constellations", [])

        # Récupérer les détails de chaque constellation
        constellations = []
        for constellation_id in constellation_ids:
            try:
                constellation_data = self.repository.get_constellation_details(
                    constellation_id
                )
                # Transformation des données selon le besoin métier
                constellations.append(
                    {
                        "constellation_id": constellation_id,
                        "name": constellation_data.get("name", "Unknown"),
                        "systems": constellation_data.get("systems", []),
                        "position": constellation_data.get("position", {}),
                    }
                )
            except Exception as e:
                # Logger l'erreur mais continuer avec les autres constellations
                # C'est une décision métier : on ne fait pas échouer toute la requête
                import logging

                logging.warning(
                    f"Erreur lors de la récupération de la constellation {constellation_id}: {e}"
                )
                continue

        return constellations

    def get_constellation_systems_with_details(
        self, constellation_id: int
    ) -> List[Dict[str, Any]]:
        """
        Récupère les détails de tous les systèmes d'une constellation
        Logique métier : orchestration des appels au repository

        Args:
            constellation_id: ID de la constellation

        Returns:
            Liste des systèmes avec leurs détails formatés

        Raises:
            Exception: Si une erreur survient lors de la récupération
        """
        # Récupérer les détails de la constellation pour obtenir les IDs des systèmes
        constellation_data = self.repository.get_constellation_details(constellation_id)
        system_ids = constellation_data.get("systems", [])

        # Récupérer les détails de chaque système
        systems = []
        for system_id in system_ids:
            try:
                system_data = self.repository.get_system_details(system_id)
                # Transformation des données selon le besoin métier
                systems.append(
                    {
                        "system_id": system_id,
                        "name": system_data.get("name", "Unknown"),
                        "security_status": system_data.get("security_status", 0.0),
                        "security_class": system_data.get("security_class", ""),
                        "position": system_data.get("position", {}),
                        "constellation_id": system_data.get("constellation_id"),
                        "planets": system_data.get("planets", []),
                        "star_id": system_data.get("star_id"),
                    }
                )
            except Exception as e:
                # Logger l'erreur mais continuer avec les autres systèmes
                # C'est une décision métier : on ne fait pas échouer toute la requête
                import logging

                logging.warning(
                    f"Erreur lors de la récupération du système {system_id}: {e}"
                )
                continue

        return systems

    def get_system_connections(self, system_id: int) -> List[Dict[str, Any]]:
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
        system_data = self.repository.get_system_details(system_id)
        stargate_ids = system_data.get("stargates", [])

        # Récupérer la constellation et la région du système source pour comparaison
        source_constellation_id = system_data.get("constellation_id")
        source_region_id = None
        if source_constellation_id:
            source_constellation = self.repository.get_constellation_details(
                source_constellation_id
            )
            source_region_id = source_constellation.get("region_id")

        # Récupérer les détails de chaque stargate pour trouver les systèmes de destination
        connected_systems = []
        for stargate_id in stargate_ids:
            try:
                stargate_data = self.repository.get_stargate_details(stargate_id)
                destination = stargate_data.get("destination", {})
                destination_system_id = destination.get("system_id")

                if destination_system_id and destination_system_id != system_id:
                    # Récupérer les détails du système de destination
                    destination_system = self.repository.get_system_details(
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
                            self.repository.get_constellation_details(
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
                            destination_region = self.repository.get_region_details(
                                destination_region_id
                            )
                            destination_region_name = destination_region.get(
                                "name", "Unknown"
                            )

                    # Transformation des données selon le besoin métier
                    connected_systems.append(
                        {
                            "system_id": destination_system_id,
                            "name": destination_system.get("name", "Unknown"),
                            "security_status": destination_system.get(
                                "security_status", 0.0
                            ),
                            "security_class": destination_system.get(
                                "security_class", ""
                            ),
                            "stargate_id": stargate_id,
                            "constellation_id": destination_constellation_id,
                            "constellation_name": destination_constellation_name,
                            "region_id": destination_region_id,
                            "region_name": destination_region_name,
                            "same_constellation": same_constellation,
                            "same_region": same_region,
                        }
                    )
            except Exception as e:
                # Logger l'erreur mais continuer avec les autres stargates
                # C'est une décision métier : on ne fait pas échouer toute la requête
                import logging

                logging.warning(
                    f"Erreur lors de la récupération de la stargate {stargate_id}: {e}"
                )
                continue

        return connected_systems
