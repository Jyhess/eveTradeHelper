# Guide de contribution

## Test-Driven Development (TDD)

Ce projet suit strictement la méthodologie **TDD** pour toutes les modifications de code.

### Processus obligatoire

Chaque modification de code **DOIT** suivre ce cycle :

#### 1. 🔴 RED - Écrire le test qui échoue

```bash
# Écrire le test
# Exécuter et vérifier qu'il échoue
python -m pytest tests/test_new_feature.py::test_new_functionality -v
# ❌ Le test doit échouer (c'est normal)
```

#### 2. 🟢 GREEN - Implémenter le minimum

```bash
# Implémenter uniquement ce qui est nécessaire
# Exécuter le test
python -m pytest tests/test_new_feature.py::test_new_functionality -v
# ✅ Le test doit maintenant passer
```

#### 3. 🔵 REFACTOR - Améliorer le code

```bash
# Améliorer le code (lisibilité, performance, structure)
# Vérifier que tous les tests passent toujours
python -m pytest tests/ -v
# ✅ Tous les tests doivent rester verts
```

### Types de tests

#### Tests unitaires (`@pytest.mark.unit`)

- Testent la logique métier avec des mocks
- **Cache désactivé** (via fixture `cache` dans `conftest.py`)
- Utilisent des repositories mockés
- Exemples : `test_deals_service.py`, `test_market_service.py`

#### Tests d'intégration (`@pytest.mark.integration`)

- Testent l'intégration complète avec le vrai repository
- **Cache Redis activé et partagé** avec la production
- Utilisent le vrai `EveAPIClient` et `EveRepositoryImpl`
- Exemples : `test_deals_api.py`, `test_region_api.py`, `test_market_api.py`

### Commandes utiles

```bash
# Tous les tests
python -m pytest tests/ -v

# Tests unitaires uniquement
python -m pytest tests/ -m unit -v

# Tests d'intégration uniquement
python -m pytest tests/ -m integration -v

# Un fichier spécifique
python -m pytest tests/test_example.py -v

# Un test spécifique
python -m pytest tests/test_example.py::test_function_name -v

# Avec traceback court
python -m pytest tests/ -v --tb=short

# Arrêter au premier échec
python -m pytest tests/ -x
```

### Règles de cache

- **Tests unitaires** : Cache désactivé (pas de conflits avec mocks)
- **Tests d'intégration** : Cache Redis partagé avec la production
- **Pas de nettoyage** : Le cache persiste entre les tests et est mutualisé

### Bonnes pratiques

1. ✅ **Toujours** commencer par le test
2. ✅ **Toujours** vérifier que le test échoue avant d'implémenter
3. ✅ **Toujours** exécuter tous les tests après chaque modification
4. ✅ Utiliser `@pytest.mark.parametrize` pour éviter la duplication
5. ✅ Un test = une assertion principale (peut avoir plusieurs assertions liées)

### Exemple complet

```python
# 1. RED - Écrire le test
def test_multiply_numbers():
    """Test que la multiplication fonctionne"""
    result = multiply(3, 4)
    assert result == 12

# Exécuter : python -m pytest tests/test_math.py::test_multiply_numbers -v
# ❌ Échec : NameError: name 'multiply' is not defined

# 2. GREEN - Implémenter le minimum
def multiply(a, b):
    return a * b

# Exécuter : python -m pytest tests/test_math.py::test_multiply_numbers -v
# ✅ Succès

# 3. REFACTOR - Améliorer
def multiply(a: int, b: int) -> int:
    """
    Multiplie deux nombres entiers.

    Args:
        a: Premier nombre
        b: Deuxième nombre

    Returns:
        Le produit des deux nombres
    """
    return a * b

# Exécuter : python -m pytest tests/ -v
# ✅ Tous les tests passent
```

Pour plus de détails, consultez [TDD.md](../TDD.md) à la racine du projet.
