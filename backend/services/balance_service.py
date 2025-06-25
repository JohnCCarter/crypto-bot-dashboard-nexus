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
    Använder riktiga API-nycklar för paper trading.
    :return: dict med balansdata från ccxt
    :raises: ValueError, ccxt.BaseError
    """
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")
    
    if not api_key or not api_secret or api_key.startswith("your_") or api_secret.startswith("your_"):
        raise ValueError("API keys not configured properly. Please update .env with your Bitfinex Paper Trading API keys.")
    
    try:
        exchange = MyBitfinex({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "sandbox": True  # Viktigt för paper trading
        })
        return exchange.fetch_balance()
    except Exception as e:
        raise ValueError(f"Failed to fetch balances from Bitfinex: {str(e)}")
