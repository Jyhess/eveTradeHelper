"""
API pour la gestion des régions
Endpoints Flask pour les régions
"""

import os
from flask import Blueprint, jsonify, current_app
from typing import Optional
from domain.region_service import RegionService


class RegionAPI:
    """API Flask pour la gestion des régions"""

    def __init__(
        self,
        region_service: RegionService,
        blueprint_name: str = "regions",
    ):
        """
        Initialise l'API des régions

        Args:
            region_service: Service de domaine pour les régions
            blueprint_name: Nom du blueprint Flask
        """
        self.region_service = region_service
        self.blueprint = Blueprint(blueprint_name, __name__)
        self._register_routes()

    def _register_routes(self):
        """Enregistre les routes de l'API"""
        self.blueprint.route("/api/v1/regions", methods=["GET"])(self.get_regions)
        self.blueprint.route(
            "/api/v1/regions/<int:region_id>/constellations", methods=["GET"]
        )(self.get_region_constellations)
        self.blueprint.route(
            "/api/v1/constellations/<int:constellation_id>/systems", methods=["GET"]
        )(self.get_constellation_systems)
        self.blueprint.route("/api/v1/systems/<int:system_id>", methods=["GET"])(
            self.get_system_details
        )
        self.blueprint.route(
            "/api/v1/systems/<int:system_id>/connections", methods=["GET"]
        )(self.get_system_connections)
        self.blueprint.route(
            "/api/v1/constellations/<int:constellation_id>", methods=["GET"]
        )(self.get_constellation_info)

    def get_regions(self):
        """
        Récupère la liste des régions d'Eve Online avec leurs détails
        Le cache est géré automatiquement par la couche infrastructure (EveAPIClient)

        Returns:
            Réponse JSON avec les régions
        """
        try:
            current_app.logger.info("Récupération des régions")
            limit = int(os.getenv("REGIONS_LIMIT", "50"))
            regions = self.region_service.get_regions_with_details(limit=limit)

            # Trier par nom
            regions_sorted = sorted(regions, key=lambda x: x.get("name", ""))

            return jsonify(
                {
                    "total": len(regions_sorted),
                    "regions": regions_sorted,
                }
            )

        except Exception as e:
            current_app.logger.error(f"Erreur lors de la récupération des régions: {e}")
            return (
                jsonify({"error": f"Erreur de connexion à l'API ESI: {str(e)}"}),
                500,
            )

    def get_region_constellations(self, region_id: int):
        """
        Récupère les détails de toutes les constellations d'une région
        Le cache est géré automatiquement par la couche infrastructure (EveAPIClient)

        Args:
            region_id: ID de la région

        Returns:
            Réponse JSON avec les constellations
        """
        try:
            current_app.logger.info(
                f"Récupération des constellations de la région {region_id}"
            )
            constellations = self.region_service.get_region_constellations_with_details(
                region_id
            )

            # Trier par nom
            constellations_sorted = sorted(
                constellations, key=lambda x: x.get("name", "")
            )

            return jsonify(
                {
                    "region_id": region_id,
                    "total": len(constellations_sorted),
                    "constellations": constellations_sorted,
                }
            )

        except Exception as e:
            current_app.logger.error(
                f"Erreur lors de la récupération des constellations: {e}"
            )
            return (
                jsonify(
                    {
                        "error": f"Erreur de connexion à l'API ESI: {str(e)}",
                        "region_id": region_id,
                    }
                ),
                500,
            )

    def get_constellation_systems(self, constellation_id: int):
        """
        Récupère les détails de tous les systèmes d'une constellation
        Le cache est géré automatiquement par la couche infrastructure (EveAPIClient)

        Args:
            constellation_id: ID de la constellation

        Returns:
            Réponse JSON avec les systèmes
        """
        try:
            current_app.logger.info(
                f"Récupération des systèmes de la constellation {constellation_id}"
            )
            systems = self.region_service.get_constellation_systems_with_details(
                constellation_id
            )

            # Trier par nom
            systems_sorted = sorted(systems, key=lambda x: x.get("name", ""))

            return jsonify(
                {
                    "constellation_id": constellation_id,
                    "total": len(systems_sorted),
                    "systems": systems_sorted,
                }
            )

        except Exception as e:
            current_app.logger.error(
                f"Erreur lors de la récupération des systèmes: {e}"
            )
            return (
                jsonify(
                    {
                        "error": f"Erreur de connexion à l'API ESI: {str(e)}",
                        "constellation_id": constellation_id,
                    }
                ),
                500,
            )

    def get_system_details(self, system_id: int):
        """
        Récupère les détails d'un système solaire
        Le cache est géré automatiquement par la couche infrastructure (EveAPIClient)

        Args:
            system_id: ID du système

        Returns:
            Réponse JSON avec les détails du système
        """
        try:
            current_app.logger.info(f"Récupération des détails du système {system_id}")
            system_data = self.region_service.repository.get_system_details(system_id)

            # Formater les données selon le besoin
            system = {
                "system_id": system_id,
                "name": system_data.get("name", "Unknown"),
                "security_status": system_data.get("security_status", 0.0),
                "security_class": system_data.get("security_class", ""),
                "position": system_data.get("position", {}),
                "constellation_id": system_data.get("constellation_id"),
                "planets": system_data.get("planets", []),
                "star_id": system_data.get("star_id"),
            }

            return jsonify(
                {
                    "system_id": system_id,
                    "system": system,
                }
            )

        except Exception as e:
            current_app.logger.error(
                f"Erreur lors de la récupération des détails du système: {e}"
            )
            return (
                jsonify(
                    {
                        "error": f"Erreur de connexion à l'API ESI: {str(e)}",
                        "system_id": system_id,
                    }
                ),
                500,
            )

    def get_system_connections(self, system_id: int):
        """
        Récupère les systèmes connectés à un système donné via les stargates
        Le cache est géré automatiquement par la couche infrastructure (EveAPIClient)

        Args:
            system_id: ID du système

        Returns:
            Réponse JSON avec les systèmes connectés
        """
        try:
            current_app.logger.info(
                f"Récupération des connexions du système {system_id}"
            )
            connections = self.region_service.get_system_connections(system_id)

            # Trier par nom
            connections_sorted = sorted(connections, key=lambda x: x.get("name", ""))

            return jsonify(
                {
                    "system_id": system_id,
                    "total": len(connections_sorted),
                    "connections": connections_sorted,
                }
            )

        except Exception as e:
            current_app.logger.error(
                f"Erreur lors de la récupération des connexions: {e}"
            )
            return (
                jsonify(
                    {
                        "error": f"Erreur de connexion à l'API ESI: {str(e)}",
                        "system_id": system_id,
                    }
                ),
                500,
            )

    def get_constellation_info(self, constellation_id: int):
        """
        Récupère les informations d'une constellation et de sa région parente.
        Le cache est géré automatiquement par la couche infrastructure (EveAPIClient).

        Args:
            constellation_id: ID de la constellation

        Returns:
            Réponse JSON avec les détails de la constellation et de la région.
        """
        try:
            current_app.logger.info(
                f"Récupération des infos de la constellation {constellation_id}"
            )

            # Récupérer les détails de la constellation
            constellation_data = (
                self.region_service.repository.get_constellation_details(
                    constellation_id
                )
            )
            region_id = constellation_data.get("region_id")

            # Récupérer les détails de la région
            region_data = None
            if region_id:
                region_data = self.region_service.repository.get_region_details(
                    region_id
                )

            # Formater les données
            info = {
                "constellation": {
                    "constellation_id": constellation_id,
                    "name": constellation_data.get("name", "Unknown"),
                    "region_id": region_id,
                },
            }

            if region_data:
                info["region"] = {
                    "region_id": region_id,
                    "name": region_data.get("name", "Unknown"),
                }

            return jsonify(info)

        except Exception as e:
            current_app.logger.error(
                f"Erreur lors de la récupération des infos de la constellation: {e}"
            )
            return (
                jsonify(
                    {
                        "error": f"Erreur de connexion à l'API ESI: {str(e)}",
                        "constellation_id": constellation_id,
                    }
                ),
                500,
            )
