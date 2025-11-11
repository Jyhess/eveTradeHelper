# Backend Architecture

This document describes the detailed backend architecture following **Clean Architecture** principles.

## Overview

The backend is organized in layers following Clean Architecture principles, allowing clear separation of responsibilities and better maintainability.

```
┌─────────────────────────────────────────┐
│         Application Layer               │  ← FastAPI Endpoints, Use Cases
│   (application/)                        │
├─────────────────────────────────────────┤
│         Domain Layer                    │  ← Pure Business Logic
│   (domain/)                             │
├─────────────────────────────────────────┤
│         Infrastructure Layer            │  ← Repository, Cache, API Client
│   (eve/, utils/)                        │
└─────────────────────────────────────────┘
```

## Module Structure

### 1. Domain Layer (`domain/`)

**Responsibility**: Contains pure business logic, independent of any infrastructure.

#### Principles

- ✅ Independent of frameworks (FastAPI, etc.)
- ✅ Independent of databases and external APIs
- ✅ Contains only business logic
- ✅ Defines interfaces that infrastructure must implement

### 2. Infrastructure Layer

#### `eve/` - API Client and Repository

**Responsibility**: Concrete implementation of interfaces defined in Domain, data access management.

##### Components

- **Repository** (`eve_repository_impl.py`): Implementation of `EveRepository` using `EveAPIClient`
- **API Client** (`eve_api_client.py`): HTTP client for Eve Online ESI API with automatic retry
- **Factory** (`eve_repository_factory.py`): Factory to create repository instances

##### Principles

- ✅ Implements interfaces defined in Domain
- ✅ Handles technical details (HTTP, retry, etc.)
- ✅ Can be replaced without modifying Domain

#### `utils/` - Utilities

##### Cache

Utility simplifying the use of a Redis cache with expiration.

### 3. Application Layer (`application/`)

**Responsibility**: Use cases, orchestration, HTTP endpoints.

#### Principles

- ✅ Uses Domain services
- ✅ Handles HTTP requests (FastAPI Routers)
- ✅ Manages application-level cache (if necessary)
- ✅ Transforms data for API

## Data Flow

### Typical API Request

```
1. HTTP Client
   ↓
2. Application Layer (RegionAPI)
   ├─ Dependency injection (ServicesProvider)
   ├─ Calls Domain Service
   └─ Returns JSON response
   ↓
3. Domain Layer (RegionService)
   ├─ Calls Repository
   ├─ Applies business logic
   └─ Transforms data
   ↓
4. Infrastructure Layer (EveRepositoryImpl)
   ├─ Uses EveAPIClient
   ├─ Manages cache (via @cached)
   └─ Returns raw data
   ↓
5. Eve Online ESI API
```

### Example: Retrieving Regions

1. **Request**: `GET /api/v1/regions`
2. **Application** (`region_api.py`)
   - Injects `RegionService` via `ServicesProvider`
   - Calls `RegionService.get_regions_with_details()`
3. **Domain** (`RegionService`)
   - Retrieves IDs via `repository.get_regions_list()`
   - Retrieves details via `repository.get_region_details()`
   - Applies limit and transforms data
4. **Infrastructure** (`EveRepositoryImpl`)
   - Calls `EveAPIClient.get_regions_list()` (with cache via `@cached`)
   - Calls `EveAPIClient.get_region_details()` (with cache via `@cached`)
5. **Cache**: Result automatically cached by the `@cached` decorator

## Clean Architecture Principles

### Dependencies

```
Application → Domain ← Infrastructure
     ↓                   ↑
     └───────────────────┘
```

- **Domain** depends on nothing
- **Infrastructure** implements Domain interfaces
- **Application** depends on Domain and uses Infrastructure via interfaces

### Advantages

1. **Testability**: Easy to mock repository to test Domain
2. **Flexibility**: Change data source without modifying Domain
3. **Maintainability**: Clear separation of responsibilities
4. **Scalability**: Simplified addition of new features

## Configuration and Initialization

Initialization is done in `app.py` and `app_factory.py`:

This initialization follows the **Dependency Injection** pattern: each layer receives its dependencies via the constructor.

## Cache

Cache is managed at multiple levels:

### Infrastructure-Level Cache (via `@cached`)

The `@cached` decorator is applied to repository methods to automatically cache results:

```python
@cached(expiry_hours=24)
async def get_regions_list(self) -> list[int]:
    """Retrieves the list of region IDs"""
    return await self._get("/universe/regions/")
```

### Application-Level Cache (LRU)

For specific cases (e.g., adjacent regions), an in-memory LRU cache is used in the application layer.

### Cache Types

- **SimpleCache**: Redis cache with expiration (production and integration tests)
- **FakeCache**: In-memory cache for unit tests (no Redis dependency)

## Tests

Tests are organized in:

- `unit_tests/`: Unit tests with `FakeCache` (no Redis)
- `integration_tests/`: Integration tests with `SimpleCache` (real Redis)

Tests use reference data stored in `unit_tests/reference/` to compare API results.

## Future Evolutions

This architecture easily allows:

- Adding new domain services (e.g., `SystemService`, `StationService`)
- Adding new APIs (e.g., `SystemAPI`, `StationAPI`)
- Replacing repository (e.g., local database instead of API)
- Adding new endpoints without modifying business logic
- Changing framework (e.g., Django instead of FastAPI) without touching Domain

## References

- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html) - Robert C. Martin
- [The Clean Architecture](https://www.youtube.com/watch?v=CnailTcJV_U) - Conference
