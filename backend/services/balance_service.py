THIS SHOULD BE A LINTER ERRORimport os
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
    I utvecklingsläge returneras mock-data.
    :return: dict med balansdata från ccxt eller mock-data
    :raises: ValueError, ccxt.BaseError
    """
    # Kolla om vi är i utvecklingsläge
    development_mode = os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"
    
    if development_mode:
        # Returnera mock balance data för utveckling
        return {
            "info": {},
            "BTC": {"free": 0.15, "used": 0.05, "total": 0.20},
            "ETH": {"free": 2.5, "used": 0.0, "total": 2.5},
            "USD": {"free": 1500.0, "used": 500.0, "total": 2000.0},
            "free": {"BTC": 0.15, "ETH": 2.5, "USD": 1500.0},
            "used": {"BTC": 0.05, "ETH": 0.0, "USD": 500.0},
            "total": {"BTC": 0.20, "ETH": 2.5, "USD": 2000.0}
        }
    
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")
    if not api_key or not api_secret:
        raise ValueError("API keys not configured properly")
    exchange = MyBitfinex({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
    })
    return exchange.fetch_balance()
