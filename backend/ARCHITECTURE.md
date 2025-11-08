# Architecture du Backend

Ce document décrit l'architecture détaillée du backend selon les principes de **Clean Architecture**.

## Vue d'ensemble

Le backend est organisé en couches selon les principes de Clean Architecture, permettant une séparation claire des responsabilités et une meilleure maintenabilité.

```
┌─────────────────────────────────────────┐
│         Application Layer               │  ← Endpoints FastAPI, Cas d'usage
│   (application/)                        │
├─────────────────────────────────────────┤
│         Domain Layer                    │  ← Logique métier pure
│   (domain/)                             │
├─────────────────────────────────────────┤
│         Infrastructure Layer            │  ← Repository, Cache, API Client
│   (eve/, utils/)                        │
└─────────────────────────────────────────┘
```

## Structure des modules

### 1. Domain Layer (`domain/`)

**Responsabilité** : Contient la logique métier pure, indépendante de toute infrastructure.

#### Fichiers principaux

- `repository.py` : Interface abstraite `EveRepository` définissant le contrat
- `region_service.py` : Service de domaine pour les régions
- `market_service.py` : Service de domaine pour les marchés
- `deals_service.py` : Service de domaine pour les opportunités de trading
- `constants.py` : Constantes du domaine (pas de nombres magiques)
- `helpers.py` : Fonctions utilitaires du domaine

#### Principes

- ✅ Indépendant des frameworks (FastAPI, etc.)
- ✅ Indépendant de la base de données et des APIs externes
- ✅ Contient uniquement la logique métier
- ✅ Définit les interfaces que l'infrastructure doit implémenter

### 2. Infrastructure Layer

#### `eve/` - Client API et Repository

**Responsabilité** : Implémentation concrète des interfaces définies dans le Domain, gestion de l'accès aux données.

##### Composants

- **Repository** (`eve_repository_impl.py`) : Implémentation de `EveRepository` utilisant `EveAPIClient`
- **API Client** (`eve_api_client.py`) : Client HTTP pour l'API ESI d'Eve Online avec retry automatique
- **Factory** (`eve_repository_factory.py`) : Factory pour créer les instances de repository

##### Principes

- ✅ Implémente les interfaces définies dans le Domain
- ✅ Gère les détails techniques (HTTP, retry, etc.)
- ✅ Peut être remplacé sans modifier le Domain

#### `utils/` - Utilitaires

##### Cache

Utilitaire simplifiant l'utilisation d'un cache Redis avec expiration.

### 3. Application Layer (`application/`)

**Responsabilité** : Cas d'usage, orchestration, endpoints HTTP.

#### Fichiers

- `app_factory.py` : Factory pour créer l'application FastAPI
- `region_api.py` : Endpoints FastAPI pour les régions (`/api/v1/regions`)
- `market_api.py` : Endpoints FastAPI pour les marchés (`/api/v1/markets/*`)
- `deals_api.py` : Endpoints FastAPI pour les opportunités (`/api/v1/deals`)
- `health_api.py` : Endpoints de santé (`/api/health`, `/api/hello`)
- `services_provider.py` : Provider pour l'injection de dépendances FastAPI
- `utils.py` : Utilitaires de l'application (cache LRU, etc.)

#### Principes

- ✅ Utilise les services du Domain
- ✅ Gère les requêtes HTTP (FastAPI Routers)
- ✅ Gère le cache au niveau application (si nécessaire)
- ✅ Transforme les données pour l'API

## Flux de données

### Requête API typique

```
1. Client HTTP
   ↓
2. Application Layer (RegionAPI)
   ├─ Injection de dépendances (ServicesProvider)
   ├─ Appelle Domain Service
   └─ Retourne réponse JSON
   ↓
3. Domain Layer (RegionService)
   ├─ Appelle Repository
   ├─ Applique la logique métier
   └─ Transforme les données
   ↓
4. Infrastructure Layer (EveRepositoryImpl)
   ├─ Utilise EveAPIClient
   ├─ Gère le cache (via @cached)
   └─ Retourne les données brutes
   ↓
5. API ESI d'Eve Online
```

### Exemple : Récupération des régions

1. **Requête** : `GET /api/v1/regions`
2. **Application** (`region_api.py`)
   - Injection de `RegionService` via `ServicesProvider`
   - Appelle `RegionService.get_regions_with_details()`
3. **Domain** (`RegionService`)
   - Récupère les IDs via `repository.get_regions_list()`
   - Récupère les détails via `repository.get_region_details()`
   - Applique la limite et transforme les données
4. **Infrastructure** (`EveRepositoryImpl`)
   - Appelle `EveAPIClient.get_regions_list()` (avec cache via `@cached`)
   - Appelle `EveAPIClient.get_region_details()` (avec cache via `@cached`)
5. **Cache** : Résultat mis en cache automatiquement par le décorateur `@cached`

## Principes de Clean Architecture

### Dépendances

```
Application → Domain ← Infrastructure
     ↓                   ↑
     └───────────────────┘
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

L'initialisation se fait dans `app.py` et `app_factory.py` :

```python
# Infrastructure Layer
api_client = EveAPIClient()
eve_repository = EveRepositoryImpl(api_client)
cache = SimpleCache(redis_client, expiry_hours=24)

# Domain Layer
region_service = RegionService(eve_repository)
market_service = MarketService(eve_repository)
deals_service = DealsService(eve_repository)

# Application Layer
app = create_app(region_service, market_service, deals_service)
```

Cette configuration suit le pattern **Dependency Injection** : chaque couche reçoit ses dépendances via le constructeur.

## Cache

Le cache est géré à plusieurs niveaux :

### Cache au niveau Infrastructure (via `@cached`)

Le décorateur `@cached` est appliqué aux méthodes du repository pour mettre en cache automatiquement les résultats :

```python
@cached(expiry_hours=24)
async def get_regions_list(self) -> list[int]:
    """Récupère la liste des IDs de régions"""
    return await self._get("/universe/regions/")
```

### Cache au niveau Application (LRU)

Pour certains cas spécifiques (ex: régions adjacentes), un cache LRU en mémoire est utilisé dans l'application layer.

### Types de cache

- **SimpleCache** : Cache Redis avec expiration (production et tests d'intégration)
- **FakeCache** : Cache en mémoire pour les tests unitaires (pas de dépendance Redis)

## Tests

Les tests sont organisés dans :

- `unit_tests/` : Tests unitaires avec `FakeCache` (pas de Redis)
- `integration_tests/` : Tests d'intégration avec `SimpleCache` (vrai Redis)

Les tests utilisent des données de référence stockées dans `unit_tests/reference/` pour comparer les résultats API.

## Évolutions futures

Cette architecture permet facilement :

- Ajout de nouveaux services de domaine (ex: `SystemService`, `StationService`)
- Ajout de nouvelles APIs (ex: `SystemAPI`, `StationAPI`)
- Remplacement du repository (ex: base de données locale au lieu de l'API)
- Ajout de nouveaux endpoints sans modifier la logique métier
- Changement de framework (ex: Django au lieu de FastAPI) sans toucher au Domain

## Références

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) - Robert C. Martin
- [The Clean Architecture](https://www.youtube.com/watch?v=CnailTcJV_U) - Conférence
