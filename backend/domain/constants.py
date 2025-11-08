"""
Eve Online domain constants
"""

# ID threshold to distinguish stations from systems
# IDs >= STATION_ID_THRESHOLD are stations
STATION_ID_THRESHOLD = 60000000

# Default limits
DEFAULT_MIN_PROFIT_ISK = 100000.0
DEFAULT_MAX_CONCURRENT_ANALYSES = 20
DEFAULT_MARKET_ORDERS_LIMIT = 50

# Cache TTL (in seconds)
MARKET_CATEGORIES_CACHE_TTL = 3600  # 1 hour
ADJACENT_REGIONS_CACHE_TTL = 86400  # 24 hours

# Cache TTL for market orders (in hours)
MARKET_ORDERS_CACHE_EXPIRY_HOURS = 1

# Retry configuration for API calls
DEFAULT_API_MAX_RETRIES = 2
DEFAULT_API_RETRY_DELAY_SECONDS = 0.5
