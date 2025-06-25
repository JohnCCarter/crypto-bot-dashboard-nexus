import os
import time

import ccxt
from dotenv import load_dotenv

load_dotenv()


class MyBitfinex(ccxt.bitfinex):
    _last_nonce = int(time.time() * 1000)
    def nonce(self):
        now = int(time.time() * 1000)
        self._last_nonce = max(self._last_nonce + 1, now)
        return self._last_nonce


def fetch_balances():
    """
    Hämtar saldon från Bitfinex via ccxt och returnerar hela balance-objektet.
    Stöder både utvecklingsläge (mock data) och paper trading med riktiga API-nycklar.
    :return: dict med balansdata från ccxt eller mock data
    :raises: ValueError, ccxt.BaseError
    """
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")
    
    # Kolla om vi har placeholder-nycklar (utvecklingsläge)
    has_placeholder_keys = (not api_key or not api_secret or 
                          api_key.startswith("your_") or api_secret.startswith("your_") or
                          "placeholder" in api_key or "placeholder" in api_secret)
    
    if has_placeholder_keys:
        # Returnera mock balance data för utveckling
        print("🔧 [DEV] Using mock balance data (no real API keys configured)")
        return {
            "info": {},
            "BTC": {"free": 0.15, "used": 0.05, "total": 0.20},
            "ETH": {"free": 2.5, "used": 0.0, "total": 2.5},
            "USD": {"free": 1500.0, "used": 500.0, "total": 2000.0},
            "free": {"BTC": 0.15, "ETH": 2.5, "USD": 1500.0},
            "used": {"BTC": 0.05, "ETH": 0.0, "USD": 500.0},
            "total": {"BTC": 0.20, "ETH": 2.5, "USD": 2000.0}
        }
    
    # Använd riktiga API-nycklar för Bitfinex Paper Trading
    try:
        print("📄 [PAPER] Connecting to Bitfinex Paper Trading...")
        exchange = MyBitfinex({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "sandbox": True  # Viktigt för paper trading
        })
        balance = exchange.fetch_balance()
        print("✅ [PAPER] Successfully fetched balance from Bitfinex Paper Trading")
        return balance
    except Exception as e:
        print(f"❌ [PAPER] Failed to fetch balances: {str(e)}")
        raise ValueError(f"Failed to fetch balances from Bitfinex Paper Trading: {str(e)}")
