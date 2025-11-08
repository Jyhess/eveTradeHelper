import logging
import os

from .manager import CacheManager
from .simple_cache import SimpleCache

logger = logging.getLogger(__name__)


def create_cache() -> SimpleCache:
    """
    Factory pour créer et configurer le cache Redis

    Utilise les variables d'environnement suivantes (avec valeurs par défaut):
    - REDIS_URL: URL de connexion Redis (optionnel, prioritaire)
    - REDIS_HOST: Host Redis (défaut: "localhost")
    - REDIS_PORT: Port Redis (défaut: 6379)
    - REDIS_DB: Base de données Redis (défaut: 0)
    - CACHE_EXPIRY_HOURS: Durée de vie du cache en heures (défaut: 720)

    Returns:
        Instance de SimpleCache configurée

    Raises:
        ConnectionError: Si la connexion à Redis échoue
    """
    # Configuration du cache Redis (obligatoire)
    cache_expiry_hours = int(os.getenv("CACHE_EXPIRY_HOURS", str(24 * 30)))

    # Vérifier si Redis est configuré (valeurs par défaut pour développement local)
    redis_url = os.getenv("REDIS_URL")
    redis_host = os.getenv("REDIS_HOST", "localhost")

    try:
        if redis_url:
            logger.info(f"Connexion à Redis via URL: {redis_url}")
            cache = SimpleCache(expiry_hours=cache_expiry_hours, redis_url=redis_url)
        else:
            # Utiliser les valeurs par défaut si redis_host n'est pas défini
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            logger.info(f"Connexion à Redis: {redis_host}:{redis_port}/{redis_db}")
            cache = SimpleCache(
                expiry_hours=cache_expiry_hours,
                redis_host=redis_host,
                redis_port=redis_port,
                redis_db=redis_db,
            )
    except ConnectionError as e:
        logger.error(str(e))
        raise
    except ValueError as e:
        logger.error(str(e))
        raise

    CacheManager.initialize(cache)

    return cache
