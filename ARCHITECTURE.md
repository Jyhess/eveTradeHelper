# Architecture du Projet Eve Trade Helper

Ce document décrit l'architecture du projet selon les principes de **Clean Architecture**.

## Vue d'ensemble

Le projet est organisé en couches selon les principes de Clean Architecture, permettant une séparation claire des responsabilités et une meilleure maintenabilité.

```
┌─────────────────────────────────────────┐
│         Application Layer               │  ← Endpoints Flask, Cas d'usage
│   (application/)                        │
├─────────────────────────────────────────┤
│         Domain Layer                    │  ← Logique métier pure
│   (domain/)                             │
├─────────────────────────────────────────┤
│         Infrastructure Layer            │  ← Repository, Cache, API Client
│   (eve/)                                │
└─────────────────────────────────────────┘
```

## Structure des modules

### 1. Domain Layer (`backend/domain/`)

**Responsabilité** : Contient la logique métier pure, indépendante de toute infrastructure.

#### Fichiers
- `repository.py` : Interface abstraite `EveRepository` définissant le contrat
- `region_service.py` : Service de domaine `RegionService` avec la logique métier des régions

#### Principes
- ✅ Indépendant des frameworks (Flask, etc.)
- ✅ Indépendant de la base de données et des APIs externes
- ✅ Contient uniquement la logique métier
- ✅ Définit les interfaces que l'infrastructure doit implémenter

#### Exemple
```python
class RegionService:
    """Service de domaine pour les régions"""
    
    def __init__(self, repository: EveRepository):
        self.repository = repository
    
    def get_regions_with_details(self, limit: Optional[int] = None):
        # Logique métier : orchestration des appels au repository
        # Transformation des données selon le besoin métier
```

### 2. Infrastructure Layer (`backend/eve/`)

**Responsabilité** : Implémentation concrète des interfaces définies dans le Domain, gestion de l'accès aux données.

#### Composants
- **Repository** (`repository.py`) : Implémentation de `EveRepository` utilisant `EveAPIClient`
- **API Client** (`api_client.py`) : Client HTTP pour l'API ESI d'Eve Online
- **Cache** :
  - `simple_cache.py` : Cache JSON local
  - `cache_manager.py` : Gestionnaire de cache statique
  - `cache_decorator.py` : Décorateur pour la mise en cache automatique

#### Principes
- ✅ Implémente les interfaces définies dans le Domain
- ✅ Gère les détails techniques (HTTP, fichiers, etc.)
- ✅ Peut être remplacé sans modifier le Domain

### 3. Application Layer (`backend/application/`)

**Responsabilité** : Cas d'usage, orchestration, endpoints HTTP.

#### Fichiers
- `region_api.py` : Endpoints Flask pour les régions (`/api/v1/regions`)
- `health_api.py` : Endpoints de santé (`/api/health`, `/api/hello`)

#### Principes
- ✅ Utilise les services du Domain
- ✅ Gère les requêtes HTTP (Flask Blueprints)
- ✅ Gère le cache au niveau application
- ✅ Transforme les données pour l'API

#### Exemple
```python
class RegionAPI:
    """API Flask pour la gestion des régions"""
    
    def __init__(self, region_service: RegionService, cache: SimpleCache):
        self.region_service = region_service
        self.cache = cache
```

## Flux de données

### Requête API typique

```
1. Client HTTP
   ↓
2. Application Layer (RegionAPI)
   ├─ Vérifie le cache
   ├─ Si cache invalide : appelle Domain
   └─ Retourne réponse JSON
   ↓
3. Domain Layer (RegionService)
   ├─ Appelle Repository
   ├─ Applique la logique métier
   └─ Transforme les données
   ↓
4. Infrastructure Layer (EveRepositoryImpl)
   ├─ Utilise EveAPIClient
   └─ Retourne les données brutes
   ↓
5. API ESI d'Eve Online
```

### Exemple : Récupération des régions

1. **Requête** : `GET /api/v1/regions`
2. **Application** (`RegionAPI.get_regions()`)
   - Vérifie le cache
   - Si invalide, appelle `RegionService.get_regions_with_details()`
3. **Domain** (`RegionService`)
   - Récupère les IDs via `repository.get_regions_list()`
   - Récupère les détails via `repository.get_region_details()`
   - Applique la limite et transforme les données
4. **Infrastructure** (`EveRepositoryImpl`)
   - Appelle `EveAPIClient.get_regions_list()`
   - Appelle `EveAPIClient.get_region_details()`
5. **Cache** : Résultat mis en cache par l'Application layer

## Principes de Clean Architecture

### Dépendances

```
Application → Domain ← Infrastructure
     ↓              ↑
     └──────────────┘
```

- Le **Domain** ne dépend de rien
- L'**Infrastructure** implémente les interfaces du Domain
- L'**Application** dépend du Domain et utilise l'Infrastructure via les interfaces

### Avantages

1. **Testabilité** : Facile de mocker le repository pour tester le Domain
2. **Flexibilité** : Changer de source de données sans modifier le Domain
3. **Maintenabilité** : Séparation claire des responsabilités
4. **Évolutivité** : Ajout de nouvelles fonctionnalités simplifié

## Configuration et Initialisation

L'initialisation se fait dans `app.py` :

```python
# Infrastructure Layer
api_client = EveAPIClient()
eve_repository = EveRepositoryImpl(api_client)

# Domain Layer
region_service = RegionService(eve_repository)

# Application Layer
region_api = RegionAPI(region_service, cache)
health_api = HealthAPI()
```

Cette configuration suit le pattern **Dependency Injection** : chaque couche reçoit ses dépendances via le constructeur.

## Cache

Le cache est géré au niveau **Application** :
- Vérification de la validité du cache
- Récupération depuis le cache si valide
- Appel au service si invalide
- Mise à jour du cache après récupération

Le cache utilise :
- `SimpleCache` : Stockage JSON local
- `CacheManager` : Gestionnaire statique pour l'accès global
- `@cached` : Décorateur pour la mise en cache automatique des méthodes du repository

## Tests

Les tests sont organisés dans `backend/tests/` :
- `test_eve_api_client.py` : Tests d'intégration du client API
- `test_cache_decorator.py` : Tests du décorateur de cache
- `conftest.py` : Fixtures pytest partagées

Les tests utilisent des données de référence stockées dans `backend/tests/reference/` pour comparer les résultats API.

## Évolutions futures

Cette architecture permet facilement :
- Ajout de nouveaux services de domaine (ex: `SystemService`, `MarketService`)
- Ajout de nouvelles APIs (ex: `MarketAPI`, `SystemAPI`)
- Remplacement du repository (ex: base de données locale au lieu de l'API)
- Ajout de nouveaux endpoints sans modifier la logique métier

## Références

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) - Robert C. Martin
- [The Clean Architecture](https://www.youtube.com/watch?v=CnailTcJV_U) - Conférence

