"""
Constantes du domaine Eve Online
"""

# Limite d'ID pour distinguer les stations des systèmes
# Les IDs >= STATION_ID_THRESHOLD sont des stations
STATION_ID_THRESHOLD = 60000000

# Limites par défaut
DEFAULT_MIN_PROFIT_ISK = 100000.0
DEFAULT_MAX_CONCURRENT_ANALYSES = 20
DEFAULT_MARKET_ORDERS_LIMIT = 50

# Cache TTL (en secondes)
MARKET_CATEGORIES_CACHE_TTL = 3600  # 1 heure
ADJACENT_REGIONS_CACHE_TTL = 86400  # 24 heures

# Cache TTL pour les ordres de marché (en heures)
MARKET_ORDERS_CACHE_EXPIRY_HOURS = 1

