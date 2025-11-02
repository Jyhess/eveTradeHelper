"""
Application Flask principale
Toute la logique de l'application est définie ici
"""

import os
import requests
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Base URL de l'API ESI d'Eve Online
ESI_BASE_URL = "https://esi.evetech.net/latest"


@app.route("/api/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello World from Python Backend!"})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/v1/regions", methods=["GET"])
def get_regions():
    """
    Récupère la liste des régions d'Eve Online avec leurs détails
    """
    try:
        # Récupérer la liste des IDs de régions
        regions_list_url = f"{ESI_BASE_URL}/universe/regions/"
        response = requests.get(regions_list_url, timeout=10)

        if response.status_code != 200:
            return (
                jsonify({"error": f"Erreur API ESI: {response.status_code}"}),
                response.status_code,
            )

        region_ids = response.json()

        # Récupérer les détails de chaque région
        regions = []
        for region_id in region_ids[:50]:  # Limiter à 50 régions pour les performances
            try:
                region_detail_url = f"{ESI_BASE_URL}/universe/regions/{region_id}/"
                detail_response = requests.get(region_detail_url, timeout=10)

                if detail_response.status_code == 200:
                    region_data = detail_response.json()
                    regions.append(
                        {
                            "region_id": region_id,
                            "name": region_data.get("name", "Unknown"),
                            "description": region_data.get("description", ""),
                            "constellations": region_data.get("constellations", []),
                        }
                    )
            except Exception as e:
                # Continuer même si une région échoue
                app.logger.warning(
                    f"Erreur lors de la récupération de la région {region_id}: {e}"
                )
                continue

        return jsonify({"total": len(regions), "regions": regions})

    except requests.RequestException as e:
        return jsonify({"error": f"Erreur de connexion à l'API ESI: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Erreur inattendue: {str(e)}"}), 500


if __name__ == "__main__":
    # Lecture de FLASK_DEBUG depuis les variables d'environnement
    # Peut être défini dans .vscode/launch.json ou via export FLASK_DEBUG=1
    debug_mode = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

    # Le mode debug est géré automatiquement par debugpy via la configuration launch.json
    # Quand lancé depuis Cursor/VS Code avec F5, debugpy s'injecte automatiquement
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
