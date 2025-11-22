# Performance Monitoring

Ce système de monitoring permet de suivre les performances de l'application via le tracing distribué.

## Architecture

- **Zipkin** : Tracing distribué pour analyser les requêtes en profondeur
- **OpenTelemetry** : Standard de tracing distribué

## Distributed Tracing (Zipkin)

Le tracing distribué permet de :

- Suivre une requête à travers tous les services et appels HTTP
- Voir où le temps est passé dans chaque étape (spans)
- Identifier les goulots d'étranglement
- Visualiser les dépendances entre services
- Analyser les erreurs et leur propagation

Chaque requête HTTP (entrante et sortante) est automatiquement tracée avec :

- Durée de chaque span
- Tags (méthode HTTP, URL, status code, etc.)
- Relations parent-enfant entre les spans

## Démarrage

1. Démarrer les services avec docker-compose :

```bash
docker-compose up -d
```

2. Accéder à Zipkin :
   - **Zipkin** : <http://localhost:9411>

## Utilisation de Zipkin

### Rechercher une trace

1. Aller sur <http://localhost:9411>
2. Utiliser les filtres pour rechercher :
   - **Service Name** : `eve-trade-helper`
   - **Span Name** : Nom de l'endpoint (ex: `GET /api/v1/markets/deals`)
   - **Time Range** : Période à analyser
   - **Tags** : Tags supplémentaires (status code, méthode HTTP, etc.)

### Analyser une trace

Une trace montre :

- **Timeline** : Vue temporelle de tous les spans
- **Service Map** : Carte des dépendances entre services
- **Span Details** : Détails de chaque span (durée, tags, logs)

### Exemple de trace

Pour une requête `/api/v1/markets/deals`, vous verrez :

1. Span principal : `GET /api/v1/markets/deals`
2. Spans enfants :
   - `DealsService.find_market_deals`
   - `OrdersService.get_orders_for_regions`
   - `GET https://esi.evetech.net/...` (appels HTTP externes)
   - `LocalDataRepository.get_types_for_group`

Cela permet d'identifier rapidement où le temps est passé.

## Ajouter un span personnalisé

Pour ajouter un span personnalisé dans votre code :

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

async def my_function():
    with tracer.start_as_current_span("my_custom_operation") as span:
        span.set_attribute("custom.attribute", "value")
        # Votre code ici
        pass
```

## Configuration

### Zipkin

Zipkin est configuré pour stocker les traces en mémoire (par défaut). Pour une persistance :

- Utiliser un backend de stockage (Elasticsearch, MySQL, etc.)
- Configurer via les variables d'environnement de Zipkin

La configuration se fait via la variable d'environnement `ZIPKIN_ENDPOINT` dans le docker-compose (par défaut : `http://zipkin:9411/api/v2/spans`).
