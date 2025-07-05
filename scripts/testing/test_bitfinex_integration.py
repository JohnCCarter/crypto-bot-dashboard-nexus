#!/usr/bin/env python3
"""
Testskript för BitfinexClientWrapper.

Detta skript testar integrationen med Bitfinex API Python-biblioteket
genom att ansluta till API:et och utföra några grundläggande operationer.

Användning:
    python test_bitfinex_integration.py

Kräver att API-nycklar finns i miljövariabler:
    BITFINEX_API_KEY
    BITFINEX_API_SECRET
"""

import logging
import os
import platform
import socket
import sys
import time


# Detektera om vi kör på jobbdator eller hemdator
def is_work_computer():
    """Detekterar om skriptet körs på jobbdatorn baserat på datornamn."""
    hostname = socket.gethostname().lower()
    # Ändra dessa villkor baserat på ditt datornamn på jobbet
    return "work" in hostname or "job" in hostname


def is_home_computer():
    """Detekterar om skriptet körs på hemdatorn baserat på datornamn."""
    hostname = socket.gethostname().lower()
    # Ändra dessa villkor baserat på ditt datornamn hemma
    return "skynet" in hostname or "home" in hostname


# Konfigurera miljön baserat på dator
def setup_environment():
    """Konfigurerar miljön baserat på om det är jobbdator eller hemdator."""
    # Lägg till projektets rot i Python-sökvägen
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    sys.path.insert(0, project_root)
    
    logger.info(f"Datornamn: {socket.gethostname()}")
    logger.info(f"Operativsystem: {platform.system()}")
    
    if is_work_computer():
        logger.info("Detekterad miljö: JOBBDATOR")
        # Specifika inställningar för jobbdator om det behövs
    elif is_home_computer():
        logger.info("Detekterad miljö: HEMDATOR")
        # Specifika inställningar för hemdator om det behövs
    else:
        logger.info("Detekterad miljö: OKÄND")


# Konfigurera loggning
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def test_rest_api(client):
    """Testa REST API-funktioner."""
    logger.info("=== Testar REST API ===")
    
    # Hämta ticker
    logger.info("Hämtar ticker för tBTCUSD...")
    ticker_result = client.get_ticker("tBTCUSD")
    if ticker_result["status"] == "success":
        logger.info(f"Ticker: {ticker_result['ticker']}")
    else:
        logger.error(f"Fel vid hämtning av ticker: {ticker_result['message']}")
    
    # Hämta orderbok
    logger.info("Hämtar orderbok för tBTCUSD...")
    book_result = client.get_order_book("tBTCUSD")
    if book_result["status"] == "success":
        logger.info(f"Orderbok (första 3 nivåer): {book_result['book'][:3]}")
    else:
        logger.error(f"Fel vid hämtning av orderbok: {book_result['message']}")
    
    # Om API-nycklar finns, testa autentiserade anrop
    if client.api_key and client.api_secret:
        # Hämta plånbokssaldon
        logger.info("Hämtar plånbokssaldon...")
        balances_result = client.get_wallet_balances()
        if balances_result["status"] == "success":
            logger.info(f"Plånbokssaldon: {balances_result['balances']}")
        else:
            error_msg = balances_result['message']
            logger.error(f"Fel vid hämtning av plånbokssaldon: {error_msg}")
        
        # Hämta aktiva positioner
        logger.info("Hämtar aktiva positioner...")
        positions_result = client.get_positions()
        if positions_result["status"] == "success":
            logger.info(f"Aktiva positioner: {positions_result['positions']}")
        else:
            error_msg = positions_result['message']
            logger.error(f"Fel vid hämtning av positioner: {error_msg}")
        
        # Hämta aktiva order
        logger.info("Hämtar aktiva order...")
        orders_result = client.get_active_orders()
        if orders_result["status"] == "success":
            logger.info(f"Aktiva order: {orders_result['orders']}")
        else:
            error_msg = orders_result['message']
            logger.error(f"Fel vid hämtning av aktiva order: {error_msg}")


def handle_ticker_update(ticker_data):
    """Hantera ticker-uppdateringar från WebSocket."""
    logger.info(f"Ticker-uppdatering: {ticker_data}")


def test_websocket(client):
    """Testa WebSocket-funktioner."""
    logger.info("=== Testar WebSocket ===")
    
    # Anslut till WebSocket
    logger.info("Ansluter till WebSocket...")
    connected = client.connect_websocket()
    if not connected:
        logger.error("Kunde inte ansluta till WebSocket")
        return
    
    logger.info(f"WebSocket ansluten: {client.is_ws_connected}")
    logger.info(f"WebSocket autentiserad: {client.is_ws_authenticated}")
    
    # Registrera en callback för ticker-uppdateringar
    logger.info("Registrerar callback för ticker-uppdateringar...")
    client.register_ws_callback("ticker", handle_ticker_update)
    
    # Prenumerera på ticker-kanalen för BTC/USD
    logger.info("Prenumererar på ticker för tBTCUSD...")
    client.subscribe_to_channel("ticker", "tBTCUSD")
    
    # Vänta på uppdateringar
    logger.info("Väntar på uppdateringar i 10 sekunder...")
    time.sleep(10)
    
    # Koppla från WebSocket
    logger.info("Kopplar från WebSocket...")
    client.disconnect_websocket()


def main():
    """Huvudfunktion."""
    # Konfigurera miljön
    setup_environment()
    
    # Importera efter att sökvägen är uppdaterad
    from backend.services.bitfinex_client_wrapper import BitfinexClientWrapper

    # Hämta API-nycklar från miljövariabler
    api_key = os.environ.get("BITFINEX_API_KEY", "")
    api_secret = os.environ.get("BITFINEX_API_SECRET", "")
    
    if not api_key or not api_secret:
        logger.warning(
            "API-nycklar saknas i miljövariabler. "
            "Endast publika API-anrop kommer att fungera."
        )
    
    # Skapa klient
    client = BitfinexClientWrapper(
        api_key=api_key,
        api_secret=api_secret,
        use_rest_auth=bool(api_key and api_secret)
    )
    
    # Testa REST API
    test_rest_api(client)
    
    # Testa WebSocket
    test_websocket(client)
    
    logger.info("Tester slutförda.")


if __name__ == "__main__":
    main() 