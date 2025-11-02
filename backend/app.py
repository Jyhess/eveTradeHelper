"""
Application Flask principale
Toute la logique de l'application est définie ici
"""

import os
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


@app.route("/api/hello", methods=["GET"])
def hello():
    return jsonify({"message": "Hello World from Python Backend!"})


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    # Lecture de FLASK_DEBUG depuis les variables d'environnement
    # Peut être défini dans .vscode/launch.json ou via export FLASK_DEBUG=1
    debug_mode = os.getenv("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")

    # Le mode debug est géré automatiquement par debugpy via la configuration launch.json
    # Quand lancé depuis Cursor/VS Code avec F5, debugpy s'injecte automatiquement
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
