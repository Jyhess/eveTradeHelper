"""
API pour les endpoints de santé
"""

from flask import Blueprint, jsonify


class HealthAPI:
    """API Flask pour les endpoints de santé"""

    def __init__(self, blueprint_name: str = "health"):
        """
        Initialise l'API de santé

        Args:
            blueprint_name: Nom du blueprint Flask
        """
        self.blueprint = Blueprint(blueprint_name, __name__)
        self._register_routes()

    def _register_routes(self):
        """Enregistre les routes de l'API"""
        self.blueprint.route("/api/hello", methods=["GET"])(self.hello)
        self.blueprint.route("/api/health", methods=["GET"])(self.health)

    def hello(self):
        """Endpoint Hello World"""
        return jsonify({"message": "Hello World from Python Backend!"})

    def health(self):
        """Endpoint de santé"""
        return jsonify({"status": "ok"})
