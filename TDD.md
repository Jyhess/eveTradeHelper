# Test-Driven Development (TDD)

Ce projet suit strictement la méthodologie **Test-Driven Development (TDD)** pour toutes les modifications de code.

## Cycle TDD : Red-Green-Refactor

### 🔴 Étape 1 : RED - Écrire le test qui échoue

**Objectif** : Définir le comportement attendu avant d'implémenter.

1. **Écrire le test** qui décrit le comportement souhaité
2. **Exécuter le test** et vérifier qu'il **échoue** pour la bonne raison
3. Le test doit être **spécifique** et tester **une seule chose**

**Exemple** :

```python
def test_add_numbers():
    """Test que l'addition fonctionne correctement"""
    result = add(2, 3)
    assert result == 5
```

**Commande** :

```bash
python -m pytest tests/test_example.py::test_add_numbers -v
# Le test doit échouer car la fonction add() n'existe pas encore
```

### 🟢 Étape 2 : GREEN - Implémenter le minimum

**Objectif** : Faire passer le test avec le code le plus simple possible.

1. **Implémenter uniquement** ce qui est nécessaire pour que le test passe
2. **Ne pas ajouter** de fonctionnalités supplémentaires
3. Le code peut être "sale" ou "pas optimal" à ce stade

**Exemple** :

```python
def add(a, b):
    return a + b  # Implémentation minimale
```

**Commande** :

```bash
python -m pytest tests/test_example.py::test_add_numbers -v
# Le test doit maintenant passer ✅
```

### 🔵 Étape 3 : REFACTOR - Améliorer le code

**Objectif** : Améliorer la qualité du code tout en gardant les tests verts.

1. **Refactoriser** le code pour améliorer :
   - La lisibilité
   - La performance
   - La maintenabilité
   - La structure
2. **S'assurer** que tous les tests passent toujours après le refactoring

**Exemple** :

```python
def add(a: int, b: int) -> int:
    """
    Additionne deux nombres entiers.

    Args:
        a: Premier nombre
        b: Deuxième nombre

    Returns:
        La somme des deux nombres
    """
    return a + b
```

**Commande** :

```bash
python -m pytest tests/ -v
# Tous les tests doivent toujours passer ✅
```

## Workflow complet

```
1. Écrire le test → 🔴 RED
   ↓
2. Exécuter le test → 🔴 ÉCHEC (attendu)
   ↓
3. Implémenter le minimum → 🟢 GREEN
   ↓
4. Exécuter le test → 🟢 SUCCÈS
   ↓
5. Refactoriser le code → 🔵 REFACTOR
   ↓
6. Exécuter tous les tests → 🟢 TOUS VERT
```

## Règles strictes

### ✅ À FAIRE

- **Toujours** commencer par écrire le test
- **Toujours** vérifier que le test échoue avant d'implémenter
- **Toujours** exécuter tous les tests après chaque modification
- **Toujours** refactoriser après avoir fait passer le test

### ❌ À NE PAS FAIRE

- ❌ Implémenter sans test préalable
- ❌ Écrire plusieurs tests en même temps sans les faire passer un par un
- ❌ Ignorer les tests qui échouent
- ❌ Refactoriser avant que le test ne passe

## Avantages du TDD

1. **Code testé** : Toutes les fonctionnalités sont couvertes par des tests
2. **Design simple** : Le TDD encourage le code simple et minimal
3. **Confiance** : Les tests permettent de refactoriser en toute sécurité
4. **Documentation** : Les tests servent de documentation vivante
5. **Détection précoce** : Les bugs sont détectés immédiatement

## Exemples concrets dans ce projet

### Ajout d'une nouvelle fonctionnalité

1. **RED** : Créer `test_new_feature.py` avec un test qui échoue
2. **GREEN** : Implémenter la fonctionnalité minimale
3. **REFACTOR** : Améliorer le code si nécessaire

### Correction d'un bug

1. **RED** : Écrire un test qui reproduit le bug (il doit échouer)
2. **GREEN** : Corriger le bug pour que le test passe
3. **REFACTOR** : Améliorer la solution si nécessaire

### Refactoring

1. **Assurer** que tous les tests passent avant de commencer
2. **Refactoriser** le code
3. **Vérifier** que tous les tests passent toujours

## Commandes utiles

```bash
# Exécuter tous les tests
python -m pytest tests/ -v

# Exécuter un fichier de test spécifique
python -m pytest tests/test_example.py -v

# Exécuter un test spécifique
python -m pytest tests/test_example.py::test_function_name -v

# Exécuter uniquement les tests unitaires
python -m pytest tests/ -m unit -v

# Exécuter uniquement les tests d'intégration
python -m pytest tests/ -m integration -v

# Exécuter avec couverture de code
python -m pytest tests/ --cov=backend --cov-report=html
```

## Références

- [TDD par Kent Beck](https://www.amazon.fr/Test-Driven-Development-Kent-Beck/dp/0321146530)
- [Red-Green-Refactor](https://www.codecademy.com/article/tdd-red-green-refactor)
