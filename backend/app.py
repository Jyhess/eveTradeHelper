"""
Application Flask principale
Configuration et initialisation selon Clean Architecture
"""

import os
from flask import Flask
from flask_cors import CORS
from eve import SimpleCache, CacheManager, EveAPIClient
from eve.repository import EveRepositoryImpl
from domain.region_service import RegionService
from application.region_api import RegionAPI
from application.health_api import HealthAPI

app = Flask(__name__)
CORS(app)

# Configuration du cache
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
CACHE_EXPIRY_HOURS = int(os.getenv("CACHE_EXPIRY_HOURS", "240"))
cache = SimpleCache(cache_dir=CACHE_DIR, expiry_hours=CACHE_EXPIRY_HOURS)

# Initialiser le gestionnaire de cache statique
CacheManager.initialize(cache)

# Infrastructure Layer : Repository
api_client = EveAPIClient()
eve_repository = EveRepositoryImpl(api_client)

# Domain Layer : Services
region_service = RegionService(eve_repository)

# Application Layer : APIs
region_api = RegionAPI(region_service, cache)
health_api = HealthAPI()

# Enregistrer les blueprints
app.register_blueprint(region_api.blueprint)
app.register_blueprint(health_api.blueprint)


if __name__ == "__main__":
    # Lecture de FLASK_DEBUG depuis les variables d'environnement
    # Peut être défini dans .vscode/launch.json ou via export FLASK_DEBUG=1
    debug_mode = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

    # Le mode debug est géré automatiquement par debugpy via la configuration launch.json
    # Quand lancé depuis Cursor/VS Code avec F5, debugpy s'injecte automatiquement
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
