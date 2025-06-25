import os
import time
import logging
from typing import Dict, List, Any

import ccxt
from dotenv import load_dotenv
from backend.services.authenticated_websocket_service import get_authenticated_websocket_client

load_dotenv()
logger = logging.getLogger(__name__)


class MyBitfinex(ccxt.bitfinex):
    _last_nonce = int(time.time() * 1000)
    def nonce(self):
        now = int(time.time() * 1000)
        self._last_nonce = max(self._last_nonce + 1, now)
        return self._last_nonce


def fetch_balances():
    """
    Hämtar saldon från Bitfinex via authenticated WebSocket (första prioritet) 
    eller ccxt som fallback.
    Returnerar data i standardformat för trading systemet.
    """
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")
    
    # Kolla om vi har placeholder-nycklar (utvecklingsläge)
    has_placeholder_keys = (not api_key or not api_secret or 
                          api_key.startswith("your_") or api_secret.startswith("your_") or
                          "placeholder" in api_key or "placeholder" in api_secret)
    
    if has_placeholder_keys:
        # Returnera mock balance data för utveckling
        logger.info("🔧 [DEV] Using mock balance data (no real API keys configured)")
        return {
            "info": {},
            "BTC": {"free": 0.15, "used": 0.05, "total": 0.20},
            "ETH": {"free": 2.5, "used": 0.0, "total": 2.5},
            "USD": {"free": 1500.0, "used": 500.0, "total": 2000.0},
            "free": {"BTC": 0.15, "ETH": 2.5, "USD": 1500.0},
            "used": {"BTC": 0.05, "ETH": 0.0, "USD": 500.0},
            "total": {"BTC": 0.20, "ETH": 2.5, "USD": 2000.0}
        }
    
    # Försök hämta från authenticated WebSocket först
    try:
        ws_client = get_authenticated_websocket_client()
        if ws_client and ws_client.authenticated:
            logger.info("� [WS] Fetching balances from authenticated WebSocket...")
            
            wallets = ws_client.get_wallets()
            if wallets:
                # Konvertera WebSocket wallet format till ccxt-kompatibelt format
                balance_data = {
                    "info": wallets,
                    "free": {},
                    "used": {},
                    "total": {}
                }
                
                # Gruppera per currency
                currencies = {}
                for wallet_key, wallet in wallets.items():
                    currency = wallet["currency"]
                    wallet_type = wallet["type"]
                    
                    if currency not in currencies:
                        currencies[currency] = {"free": 0.0, "used": 0.0, "total": 0.0}
                    
                    # Bitfinex wallet types: exchange, margin, funding
                    # available = trading balance, balance = total balance
                    available = wallet.get("available", 0.0)
                    total = wallet.get("balance", 0.0)
                    used = max(0.0, total - available)
                    
                    currencies[currency]["free"] += available
                    currencies[currency]["used"] += used  
                    currencies[currency]["total"] += total
                
                # Lägg till i balance_data
                for currency, amounts in currencies.items():
                    balance_data[currency] = amounts
                    balance_data["free"][currency] = amounts["free"]
                    balance_data["used"][currency] = amounts["used"]
                    balance_data["total"][currency] = amounts["total"]
                
                logger.info(f"✅ [WS] Successfully fetched balances for {len(currencies)} currencies")
                return balance_data
            
            else:
                logger.warning("⚠️ [WS] WebSocket authenticated but no wallet data available yet")
                
    except Exception as e:
        logger.warning(f"⚠️ [WS] WebSocket balance fetch failed: {e}")
    
    # Fallback till ccxt REST API
    try:
        logger.info("📄 [REST] Falling back to Bitfinex REST API...")
        exchange = MyBitfinex({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True
        })
        balance = exchange.fetch_balance()
        logger.info("✅ [REST] Successfully fetched balance from Bitfinex REST API")
        return balance
        
    except Exception as e:
        logger.error(f"❌ [REST] Failed to fetch balances: {str(e)}")
        if "authentication" in str(e).lower() or "api" in str(e).lower():
            logger.error("🔧 [REST] API authentication failed - check if keys are from Paper Trading sub account")
        raise ValueError(f"Failed to fetch balances from Bitfinex: {str(e)}")


def fetch_balances_list():
    """
    Hämtar balances och returnerar i list-format för API endpoints.
    Konverterar från ccxt-format till vårt standardformat.
    """
    try:
        balance_data = fetch_balances()
        
        # Konvertera till list format som förväntas av API
        balances_list = []
        
        # Extrahera currencies från balance data
        currencies_to_process = []
        for key, value in balance_data.items():
            if key not in ["info", "free", "used", "total"] and isinstance(value, dict):
                if "total" in value:
                    currencies_to_process.append((key, value))
        
        for currency, amounts in currencies_to_process:
            # Filtrera bort valutor med 0 balance
            if amounts.get("total", 0) > 0:
                balances_list.append({
                    "currency": currency,
                    "total_balance": amounts.get("total", 0.0),
                    "available": amounts.get("free", 0.0)
                })
        
        logger.info(f"💰 Converted balances to list format: {len(balances_list)} currencies")
        return balances_list
        
    except Exception as e:
        logger.error(f"❌ Error converting balances to list: {e}")
        # Returnera tom lista vid fel istället för att krascha
        return []
