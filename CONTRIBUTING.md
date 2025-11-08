# Guide de contribution

Ce document explique comment contribuer au projet en respectant les règles de développement.

## 🔧 Configuration initiale

### 1. Installer les outils de vérification

```bash
# Activer l'environnement virtuel
source .venv/bin/activate  # Linux/Mac
# ou
.venv\Scripts\activate  # Windows

# Installer toutes les dépendances (backend + frontend)
make init
```

## 📋 Vérifications automatiques

Les vérifications sont effectuées via `make check` :

1. **Ruff** : Linting et formatage Python
2. **Mypy** : Vérification des types

### Exécution manuelle

Vous pouvez exécuter les vérifications manuellement :

```bash
# Vérifier la qualité du code
make check

# Commandes individuelles
make format      # Formater le code
make lint        # Vérifier le code sans formater
make typecheck   # Vérifier les types uniquement
```

## 📝 Règles de code

### Checklist avant commit

Avant de commiter, vérifiez que :

- [ ] Pas de nombres magiques (utiliser `domain/constants.py`)
- [ ] Fonctions courtes (< 50 lignes)
- [ ] Noms explicites et significatifs
- [ ] Pas de duplication de code (DRY)
- [ ] Fonctions nommées plutôt que commentaires explicatifs
- [ ] Respect du SRP (une responsabilité par fonction/classe)
- [ ] Encapsulation respectée (pas d'accès direct aux repositories depuis les APIs)
- [ ] Docstrings uniquement dans les APIs et quand vraiment nécessaire
- [ ] Imports en haut du fichier uniquement
- [ ] Logique métier dans les services, pas dans les APIs
- [ ] Tous les tests passent (`make test-unit`)
- [ ] Le code est formaté (`make format`)
- [ ] Pas d'erreurs de linting (`make lint`)

### Exécuter les tests

```bash
# Tests unitaires (avec fake cache)
make test-unit

# Tests d'intégration (avec vrai cache Redis)
make test-integration

# Tous les tests
make test
```

## 🛠️ Outils de développement

### Commandes Make

```bash
make check      # Vérifier la qualité du code (format, lint, typecheck)
make format     # Formater le code avec Ruff
make lint       # Vérifier le code avec Ruff (sans formater)
make typecheck  # Vérifier les types avec Mypy
make test       # Exécuter tous les tests
make all        # Tout exécuter (check, test, coverage)
```

## 🚀 Workflow Git

1. **Créer une branche** pour votre fonctionnalité
2. **Développer en suivant TDD**
3. **Vérifier le code** : `make check`
4. **Exécuter les tests** : `make test-unit`
5. **Commit** et push
6. **Créer une Pull Request**

## 📚 Ressources

- [Règles de développement](.cursorrules)
- [Architecture Backend](backend/ARCHITECTURE.md)
- [Architecture Frontend](frontend/ARCHITECTURE.md)
