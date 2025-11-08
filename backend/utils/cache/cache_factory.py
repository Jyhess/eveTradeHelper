import logging
import os

from .manager import CacheManager
from .simple_cache import SimpleCache

logger = logging.getLogger(__name__)


def create_cache() -> SimpleCache:
    """
    Factory to create and configure Redis cache

    Uses the following environment variables (with default values):
    - REDIS_URL: Redis connection URL (optional, takes priority)
    - REDIS_HOST: Redis host (default: "localhost")
    - REDIS_PORT: Redis port (default: 6379)
    - REDIS_DB: Redis database (default: 0)
    - CACHE_EXPIRY_HOURS: Cache lifetime in hours (default: 720)

    Returns:
        Configured SimpleCache instance

    Raises:
        ConnectionError: If connection to Redis fails
    """
    # Redis cache configuration (required)
    cache_expiry_hours = int(os.getenv("CACHE_EXPIRY_HOURS", str(24 * 30)))

    # Check if Redis is configured (default values for local development)
    redis_url = os.getenv("REDIS_URL")
    redis_host = os.getenv("REDIS_HOST", "localhost")

    try:
        if redis_url:
            logger.info(f"Connecting to Redis via URL: {redis_url}")
            cache = SimpleCache(expiry_hours=cache_expiry_hours, redis_url=redis_url)
        else:
            # Use default values if redis_host is not defined
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            logger.info(f"Connecting to Redis: {redis_host}:{redis_port}/{redis_db}")
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
