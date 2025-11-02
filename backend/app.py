"""
Application Flask principale
Toute la logique de l'application est définie ici
"""

import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS
from simple_cache import SimpleCache
from eve_api_client import EveAPIClient

app = Flask(__name__)
CORS(app)

# Configuration du cache
CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache")
CACHE_EXPIRY_HOURS = int(os.getenv("CACHE_EXPIRY_HOURS", "240"))
cache = SimpleCache(cache_dir=CACHE_DIR, expiry_hours=CACHE_EXPIRY_HOURS)

# Client API Eve Online
eve_client = EveAPIClient()


@app.route("/api/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello World from Python Backend!"})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


def fetch_regions_from_api(limit: int = 50):
    """Récupère les régions depuis l'API ESI"""
    # Utiliser le client API pour récupérer les régions
    regions = eve_client.get_regions_with_details(limit=limit)

    # Récupérer la liste complète des IDs pour les métadonnées
    region_ids = eve_client.get_regions_list()

    return regions, region_ids


@app.route("/api/v1/regions", methods=["GET"])
def get_regions():
    """
    Récupère la liste des régions d'Eve Online avec leurs détails
    Utilise un cache JSON local pour éviter les appels répétés à l'API ESI
    """
    cache_key = "regions_list"

    try:
        # Vérifier si le cache est valide
        if cache.is_valid(cache_key):
            # Utiliser le cache
            app.logger.info("Utilisation du cache pour les régions")
            regions = cache.get(cache_key)
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

        # Le cache est expiré ou n'existe pas, récupérer depuis l'API
        app.logger.info("Récupération des régions depuis l'API ESI")
        limit = int(os.getenv("REGIONS_LIMIT", "50"))
        regions, region_ids = fetch_regions_from_api(limit=limit)

        # Sauvegarder dans le cache
        cache.set(cache_key, regions, metadata={"region_ids": region_ids})

        # Trier par nom
        regions_sorted = sorted(regions, key=lambda x: x.get("name", ""))

        return jsonify(
            {"total": len(regions_sorted), "regions": regions_sorted, "cached": False}
        )

    except requests.RequestException as e:
        # En cas d'erreur API, essayer de retourner le cache même expiré
        app.logger.warning(f"Erreur API, tentative d'utilisation du cache expiré: {e}")
        regions = cache.get(cache_key)
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

    except Exception as e:
        app.logger.error(f"Erreur inattendue: {e}")
        return jsonify({"error": f"Erreur inattendue: {str(e)}"}), 500


if __name__ == "__main__":
    # Lecture de FLASK_DEBUG depuis les variables d'environnement
    # Peut être défini dans .vscode/launch.json ou via export FLASK_DEBUG=1
    debug_mode = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

    # Le mode debug est géré automatiquement par debugpy via la configuration launch.json
    # Quand lancé depuis Cursor/VS Code avec F5, debugpy s'injecte automatiquement
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
