from utils.cache import CacheManager

from .etag_cache import EtagCache
from .eve_api_client import EveAPIClient
from .eve_repository_impl import EveRepositoryImpl
from .rate_limiter import RateLimiter


def make_eve_repository():
    cache = CacheManager.get_instance()
    rate_limiter = RateLimiter()
    etag_cache = EtagCache(cache=cache)
    api_client = EveAPIClient(rate_limiter=rate_limiter, etag_cache=etag_cache)
    return EveRepositoryImpl(api_client)
