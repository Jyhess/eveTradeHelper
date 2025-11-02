"""
API pour la gestion des régions
Endpoints Flask pour les régions
"""

import os
from flask import Blueprint, jsonify, current_app
from typing import Optional
from domain.region_service import RegionService
from eve import SimpleCache


class RegionAPI:
    """API Flask pour la gestion des régions"""

    def __init__(
        self,
        region_service: RegionService,
        cache: SimpleCache,
        blueprint_name: str = "regions",
    ):
        """
        Initialise l'API des régions

        Args:
            region_service: Service de domaine pour les régions
            cache: Instance du cache
            blueprint_name: Nom du blueprint Flask
        """
        self.region_service = region_service
        self.cache = cache
        self.blueprint = Blueprint(blueprint_name, __name__)
        self._register_routes()

    def _register_routes(self):
        """Enregistre les routes de l'API"""
        self.blueprint.route("/api/v1/regions", methods=["GET"])(self.get_regions)

    def get_regions(self):
        """
        Récupère la liste des régions d'Eve Online avec leurs détails
        Utilise un cache JSON local pour éviter les appels répétés à l'API ESI

        Returns:
            Réponse JSON avec les régions
        """
        cache_key = "regions_list"

        try:
            # Vérifier si le cache est valide
            if self.cache.is_valid(cache_key):
                # Utiliser le cache
                current_app.logger.info("Utilisation du cache pour les régions")
                regions = self.cache.get(cache_key)
                if regions:
                    # Trier par nom pour un affichage cohérent
                    regions_sorted = sorted(regions, key=lambda x: x.get("name", ""))
                    return jsonify(
                        {
                            "total": len(regions_sorted),
                            "regions": regions_sorted,
                            "cached": True,
                        }
                    )

            # Le cache est expiré ou n'existe pas, récupérer depuis le service
            current_app.logger.info("Récupération des régions depuis l'API ESI")
            limit = int(os.getenv("REGIONS_LIMIT", "50"))
            regions = self.region_service.get_regions_with_details(limit=limit)

            # Récupérer la liste complète des IDs pour les métadonnées
            region_ids = self.region_service.repository.get_regions_list()

            # Sauvegarder dans le cache
            self.cache.set(cache_key, regions, metadata={"region_ids": region_ids})

            # Trier par nom
            regions_sorted = sorted(regions, key=lambda x: x.get("name", ""))

            return jsonify(
                {
                    "total": len(regions_sorted),
                    "regions": regions_sorted,
                    "cached": False,
                }
            )

        except Exception as e:
            # En cas d'erreur API, essayer de retourner le cache même expiré
            current_app.logger.warning(
                f"Erreur API, tentative d'utilisation du cache expiré: {e}"
            )
            regions = self.cache.get(cache_key)
            if regions:
                regions_sorted = sorted(regions, key=lambda x: x.get("name", ""))
                return jsonify(
                    {
                        "total": len(regions_sorted),
                        "regions": regions_sorted,
                        "cached": True,
                        "warning": "Cache expiré mais API indisponible",
                    }
                )
            return jsonify({"error": f"Erreur de connexion à l'API ESI: {str(e)}"}), 500
