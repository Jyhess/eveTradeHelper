"""
Utilitaires pour les tests
"""

import json
from pathlib import Path

# Chemin vers le dossier de tests
TESTS_DIR = Path(__file__).parent
REFERENCE_DIR = TESTS_DIR / "reference"


def save_reference(key: str, data):
    """
    Sauvegarde des données comme référence pour les tests
    
    Args:
        key: Nom de la référence (nom du fichier sans extension)
        data: Données à sauvegarder (sera converties en JSON)
    """
    REFERENCE_DIR.mkdir(exist_ok=True)
    ref_file = REFERENCE_DIR / f"{key}.json"
    
    with open(ref_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)


def load_reference(key: str):
    """
    Charge une référence pour comparaison
    
    Args:
        key: Nom de la référence (nom du fichier sans extension)
        
    Returns:
        Données de référence ou None si non trouvées
    """
    ref_file = REFERENCE_DIR / f"{key}.json"
    
    if not ref_file.exists():
        return None
    
    with open(ref_file, "r", encoding="utf-8") as f:
        return json.load(f)


def normalize_for_comparison(data):
    """
    Normalise les données pour la comparaison (supprime les variations non importantes)
    
    Args:
        data: Données à normaliser
        
    Returns:
        Données normalisées
    """
    if isinstance(data, dict):
        # Trier les clés et normaliser les valeurs
        return {k: normalize_for_comparison(v) for k, v in sorted(data.items())}
    elif isinstance(data, list):
        # Normaliser chaque élément et trier si possible
        normalized = [normalize_for_comparison(item) for item in data]
        # Essayer de trier si tous les éléments sont des dicts avec une clé commune
        if normalized and all(isinstance(item, dict) for item in normalized):
            if all("name" in item for item in normalized):
                normalized.sort(key=lambda x: x.get("name", ""))
            elif all("region_id" in item for item in normalized):
                normalized.sort(key=lambda x: x.get("region_id", 0))
        return normalized
    else:
        return data

