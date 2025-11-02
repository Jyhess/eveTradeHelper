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
