# Tests d'intégration

Ce dossier contient les tests d'intégration pour l'application Eve Trade Helper.

## Structure

```
tests/
├── __init__.py           # Module de tests
├── conftest.py           # Configuration et fixtures pytest
├── test_eve_api_client.py  # Tests pour EveAPIClient
├── test_cache_decorator.py # Tests pour le décorateur de cache
├── reference/            # Données de référence pour comparaison
│   ├── regions_list.json
│   ├── region_details_*.json
│   └── ...
└── README.md            # Ce fichier
```

## Exécution des tests

```bash
# Installer pytest
pip install pytest

# Exécuter tous les tests
pytest backend/tests/

# Exécuter avec détails
pytest backend/tests/ -v

# Exécuter un fichier de test spécifique
pytest backend/tests/test_eve_api_client.py

# Exécuter un test spécifique
pytest backend/tests/test_eve_api_client.py::TestEveAPIClientRegions::test_get_regions_list
```

## Génération des références

Lors du premier exécution, les tests vont :
1. Faire des appels API réels
2. Sauvegarder les résultats dans `tests/reference/`
3. Skip les tests avec un message indiquant que les références ont été créées

Lors des exécutions suivantes, les tests vont :
1. Comparer les résultats API avec les références
2. Signaler les différences si elles existent

## Mise à jour des références

Pour régénérer les références :

```bash
# Supprimer les anciennes références
rm -rf backend/tests/reference/*.json

# Réexécuter les tests
pytest backend/tests/
```

## Notes

- Les tests font des appels API réels vers l'API ESI d'Eve Online
- Les références sont stockées en JSON pour faciliter la comparaison
- Le cache de test est isolé dans `tests/test_cache/`
- Les données sont normalisées avant comparaison (tri, etc.)

