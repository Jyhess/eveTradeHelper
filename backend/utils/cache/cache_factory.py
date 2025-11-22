import logging
import os

import redis

from .manager import CacheManager
from .simple_cache import SimpleCache

logger = logging.getLogger(__name__)


def _create_redis_client(
    redis_url: str | None, redis_host: str | None, redis_port: int, redis_db: int
):
    """
    Create and configure Redis client

    Args:
        redis_url: Redis connection URL (optional, takes priority)
        redis_host: Redis host
        redis_port: Redis port
        redis_db: Redis database

    Returns:
        Configured Redis client instance

    Raises:
        ImportError: If redis-py is not installed
        ConnectionError: If connection to Redis fails
    """
    try:
        if redis_url:
            client = redis.from_url(redis_url, decode_responses=True)
        else:
            client = redis.Redis(
                host=redis_host,
                port=redis_port,
                db=redis_db,
                decode_responses=True,
            )
        # Test connection
        client.ping()
        return client
    except redis.ConnectionError as e:
        raise ConnectionError(
            f"❌ Unable to connect to Redis.\n"
            f"   Check that Redis is started with: docker-compose up -d redis\n"
            f"   Or start the Redis service in Docker: docker-compose up redis\n"
            f"   Error details: {e}"
        ) from e
    except Exception as e:
        raise ConnectionError(
            f"❌ Error connecting to Redis.\n"
            f"   Check that Redis is started with: docker-compose up -d redis\n"
            f"   Error details: {e}"
        ) from e


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
            redis_client = _create_redis_client(redis_url, None, 6379, 0)
        else:
            # Use default values if redis_host is not defined
            redis_port = int(os.getenv("REDIS_PORT", "6379"))
            redis_db = int(os.getenv("REDIS_DB", "0"))
            logger.info(f"Connecting to Redis: {redis_host}:{redis_port}/{redis_db}")
            redis_client = _create_redis_client(None, redis_host, redis_port, redis_db)

        cache = SimpleCache(redis_client=redis_client, default_expiry_hours=cache_expiry_hours)
    except ConnectionError as e:
        logger.error(str(e))
        raise
    except ValueError as e:
        logger.error(str(e))
        raise

    CacheManager.initialize(cache)

    return cache
