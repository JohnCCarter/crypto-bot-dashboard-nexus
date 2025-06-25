import os
import time
import logging

from backend.services.authenticated_websocket_service import get_authenticated_websocket_client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

def fetch_balances():
    """
    Hämtar saldon från Bitfinex via AUTHENTICATED WebSocket.
    Använder riktig Bitfinex authentication protokoll istället för ccxt.
    :return: dict med balansdata från Bitfinex WebSocket eller mock data
    :raises: ValueError
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
    
    # Använd authenticated WebSocket för KORREKT Bitfinex integration
    try:
        logger.info("📄 [WALLET] Connecting to Bitfinex via authenticated WebSocket...")
        
        # Hämta authenticated WebSocket klient
        client = get_authenticated_websocket_client()
        
        if not client:
            logger.warning("⚠️ [WALLET] Authenticated WebSocket client not available")
            raise ValueError("Authenticated WebSocket client not available")
        
        if not client.authenticated:
            logger.warning("⚠️ [WALLET] WebSocket not authenticated")
            raise ValueError("WebSocket not authenticated")
        
        # Hämta wallet data från authenticated WebSocket
        wallets = client.get_wallets()
        
        if not wallets:
            logger.warning("⚠️ [WALLET] No wallet data available from WebSocket")
            # Returnera tom struktur istället för att fejla
            return {
                "info": {},
                "free": {},
                "used": {},
                "total": {}
            }
        
        logger.info(f"✅ [WALLET] Successfully fetched {len(wallets)} wallet entries from WebSocket")
        
        # Konvertera Bitfinex WebSocket wallet format till ccxt-kompatibel format
        balance_result = {
            "info": wallets,  # Rå Bitfinex data
            "free": {},
            "used": {},
            "total": {}
        }
        
        # Processa wallet data från WebSocket
        for wallet_key, wallet_data in wallets.items():
            currency = wallet_data["currency"]
            wallet_type = wallet_data["type"]
            balance = wallet_data["balance"]
            available = wallet_data["available"]
            
            # Logga wallet information
            logger.info(f"   💰 {wallet_type} {currency}: {balance} (Available: {available})")
            
            # Sätt huvudvaluta-data (använd exchange wallet som primär)
            if wallet_type == "exchange":
                if currency not in balance_result:
                    balance_result[currency] = {"free": 0.0, "used": 0.0, "total": 0.0}
                
                balance_result[currency]["free"] = available
                balance_result[currency]["used"] = balance - available
                balance_result[currency]["total"] = balance
                
                # Sätt även i top-level dictionaries
                balance_result["free"][currency] = available
                balance_result["used"][currency] = balance - available
                balance_result["total"][currency] = balance
        
        logger.info("✅ [WALLET] Successfully processed wallet data from Bitfinex WebSocket")
        return balance_result
        
    except Exception as e:
        logger.error(f"❌ [WALLET] Failed to fetch balances from WebSocket: {str(e)}")
        raise ValueError(f"Failed to fetch balances from Bitfinex WebSocket: {str(e)}")


def fetch_balances_list():
    """
    Hämtar balances och returnerar i list-format för API endpoints.
    Konverterar från WebSocket-format till vårt standardformat.
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
