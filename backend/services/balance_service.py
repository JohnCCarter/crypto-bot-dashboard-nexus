import os

import ccxt
from dotenv import load_dotenv

load_dotenv()


def fetch_balances():
    """
    Hämtar saldon från Bitfinex via ccxt och returnerar hela balance-objektet.
    Kastar ValueError om API-nycklar saknas.
    :return: dict med balansdata från ccxt
    :raises: ValueError, ccxt.BaseError
    """
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")
    if not api_key or not api_secret:
        raise ValueError("API keys not configured properly")
    exchange = ccxt.bitfinex(
        {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
        }
    )
    return exchange.fetch_balance()
