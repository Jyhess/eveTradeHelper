# Tests unitaires

Ce dossier contient les tests unitaires pour l'application Eve Trade Helper.

## Structure

```
unittests/
├── __init__.py           # Module de tests
├── conftest.py           # Configuration et fixtures pytest
├── test_eve_api_client.py  # Tests pour EveAPIClient
├── test_cache_decorator.py # Tests pour le décorateur de cache
├── test_deals_service.py   # Tests pour DealsService
├── test_market_service.py   # Tests pour MarketService
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

# Exécuter tous les tests unitaires
pytest backend/unittests/ -m unit

# Exécuter avec détails
pytest backend/unittests/ -m unit -v

# Exécuter un fichier de test spécifique
pytest backend/unittests/test_deals_service.py

# Exécuter un test spécifique
pytest backend/unittests/test_deals_service.py::TestDealsServiceCollectTypes::test_collect_all_types_from_simple_group
```

## Cache pour les tests unitaires

Les tests unitaires utilisent un **fake cache en mémoire** (`FakeCache`) qui simule le comportement de Redis sans nécessiter de connexion réelle. Cela permet de :

- Tester le comportement du cache sans dépendre de Redis
- Exécuter les tests plus rapidement
- Isoler chaque test (le cache est nettoyé après chaque test)

Le fake cache implémente la même interface que `SimpleCache` :
- `get(key)` : récupère les données depuis le cache
- `set(key, items, metadata)` : sauvegarde des données dans le cache
- `is_valid(key)` : vérifie si le cache est encore valide
- `clear(key)` : vide le cache

## Génération des références

Lors du premier exécution, les tests vont :
1. Faire des appels API réels
2. Sauvegarder les résultats dans `unittests/reference/`
3. Skip les tests avec un message indiquant que les références ont été créées

Lors des exécutions suivantes, les tests vont :
1. Comparer les résultats API avec les références
2. Signaler les différences si elles existent

## Mise à jour des références

Pour régénérer les références :

```bash
# Supprimer les anciennes références
rm -rf backend/unittests/reference/*.json

# Réexécuter les tests
pytest backend/unittests/ -m unit
```

## Notes

- Les tests unitaires utilisent des mocks pour isoler la logique métier
- Les tests sont marqués avec `@pytest.mark.unit`
- Le fake cache est automatiquement utilisé pour tous les tests unitaires
- Le cache est nettoyé après chaque test pour éviter les fuites entre tests
- Les tests d'intégration (dans `integration_tests/`) utilisent le vrai cache Redis

