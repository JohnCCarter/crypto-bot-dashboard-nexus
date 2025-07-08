"""Balance service using shared exchange service to avoid nonce conflicts."""

from backend.services.cache_service import get_cache_service


def get_shared_exchange_service():
    """Get shared exchange service (Flask context is removed)."""
    # Flask context is removed; this function should be refactored if needed.
    return None


def fetch_balances():
    """
    Hämtar saldon från Bitfinex via shared exchange service med caching.
    Använder 30s cache för att minska API-belastning på routine polling.
    :return: dict med balansdata från exchange
    :raises: ValueError, ExchangeError
    """
    cache = get_cache_service()
    cache_key = "balances"
    
    # Check cache first (30 second TTL for balances)
    cached_balance = cache.get(cache_key, ttl_seconds=30)
    if cached_balance is not None:
        return cached_balance
    
    exchange_service = get_shared_exchange_service()
    if not exchange_service:
        raise ValueError("Exchange service not available - check API configuration")

    try:
        # Use shared exchange service for thread-safe nonce handling
        # But call raw ccxt method to get full balance structure
        raw_balance = exchange_service.exchange.fetch_balance()

        # Cache the result for 30 seconds to reduce API calls
        cache.set(cache_key, raw_balance)

        # Return raw ccxt format with ["total"] and ["free"] keys
        # This is what balances.py route expects
        return raw_balance

    except Exception as e:
        print(f"Failed to fetch balances: {e}")
        raise
