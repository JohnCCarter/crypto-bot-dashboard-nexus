"""
FastAPI application entry point.
This module provides the FastAPI application instance and configuration.
"""

import os
import sys
import logging
from typing import Dict, Any
from contextlib import asynccontextmanager

# Lägg till projektroten i Python-sökvägen för att kunna importera backend-modulen
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Request, status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from dotenv import load_dotenv

from backend.api import status as status_api
from backend.api import balances as balances_api
from backend.api import orders as orders_api
from backend.api import backtest as backtest_api
from backend.api import positions as positions_api
from backend.api import config as config_api
from backend.api import bot_control as bot_control_api
from backend.api import monitoring as monitoring_api
from backend.api import portfolio as portfolio_api
from backend.api import risk_management as risk_management_api
from backend.api import market_data as market_data_api
from backend.api import websocket as websocket_api
from backend.api import orderbook as orderbook_api
from backend.api import trading_limitations as trading_limitations_api

from backend.services.exchange import ExchangeService
from backend.services.exchange_async import create_mock_exchange_service
from backend.services.global_nonce_manager import get_global_nonce_manager

# Konfigurera loggning
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ladda miljövariabler från .env-fil om den finns
env_file = os.environ.get('FASTAPI_ENV_FILE', None)
if env_file and os.path.exists(env_file):
    load_dotenv(env_file)
else:
    load_dotenv()  # Ladda standardfilen .env om den finns

# Global variabel för exchange_service som används i dependencies.py
exchange_service = None

# Kontrollera utvecklingsläge
dev_mode = os.environ.get("FASTAPI_DEV_MODE", "false").lower() == "true"
if dev_mode:
    logger.info("🔧 Kör i UTVECKLINGSLÄGE med reducerad funktionalitet")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager för FastAPI-applikationen.
    
    Initierar tjänster vid uppstart och stänger ner dem vid avstängning.
    """
    global exchange_service
    
    # Kontrollera om WebSockets ska inaktiveras
    disable_websockets = os.environ.get("FASTAPI_DISABLE_WEBSOCKETS", "false").lower() == "true"
    if disable_websockets:
        logger.info("⚠️ WebSockets är inaktiverade i denna konfiguration")
    
    # Kontrollera om GlobalNonceManager ska inaktiveras
    disable_nonce_manager = os.environ.get("FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER", "false").lower() == "true"
    if disable_nonce_manager:
        logger.info("⚠️ GlobalNonceManager är inaktiverad i denna konfiguration")
    
    # Skapa mock exchange service för utveckling
    logger.info("🔧 Använder mock exchange ")
    exchange_service = create_mock_exchange_service()
    
    # Initiera GlobalNonceManager om den inte är inaktiverad
    if not disable_nonce_manager:
        # get_global_nonce_manager är inte awaitable, så vi kallar den direkt
        gnm = get_global_nonce_manager(dev_mode=dev_mode)
        logger.info(f"🔐 Enhanced GlobalNonceManager initialized")
    
    # Initiera BotManagerAsync för att förbereda för API-anrop
    # Denna import görs här för att undvika cirkulära imports
    from backend.services.bot_manager_async import get_bot_manager_async
    bot_manager = await get_bot_manager_async(dev_mode=dev_mode)
    logger.info(f"🤖 BotManagerAsync initialized{' in development mode' if dev_mode else ''}")
    
    # Initiera WebSocket-tjänster om de inte är inaktiverade
    if not disable_websockets:
        # Importera här för att undvika cirkelberoenden
        from backend.services.websocket_market_service import get_websocket_client
        
        # Initiera WebSocket-tjänster
        ws_market = get_websocket_client()
        logger.info("🔌 WebSocket Market tjänst initierad")
        
        try:
            # Importera och initiera WebSocket User Data om tillgänglig
            from backend.services.websocket_user_data_service import get_websocket_user_data_service
            ws_user = await get_websocket_user_data_service()
            logger.info("🔌 WebSocket User Data tjänst initierad")
        except ImportError:
            logger.warning("⚠️ WebSocket User Data tjänst kunde inte initieras (modulen saknas)")
    
    yield
    
    # Stoppa BotManagerAsync om den är igång
    try:
        from backend.services.bot_manager_async import get_bot_manager_async
        bot_manager = await get_bot_manager_async(dev_mode=dev_mode)
        status = await bot_manager.get_status()
        if status.get("status") == "running":
            logger.info("🤖 Stopping BotManagerAsync")
            await bot_manager.stop_bot()
    except Exception as e:
        logger.error(f"Error stopping BotManagerAsync: {e}")
    
    # Stäng ner WebSocket-tjänster vid avstängning
    if not disable_websockets:
        try:
            # Importera här för att undvika cirkelberoenden
            from backend.services.websocket_market_service import stop_websocket_service
            await stop_websocket_service()
            logger.info("🔌 WebSocket Market tjänst stängd")
            
            # Stäng WebSocket User Data om tillgänglig
            try:
                from backend.services.websocket_user_data_service import get_websocket_user_data_service
                ws_user = await get_websocket_user_data_service()
                await ws_user.close()
                logger.info("🔌 WebSocket User Data tjänst stängd")
            except ImportError:
                pass
        except Exception as e:
            logger.error(f"Error stopping WebSocket services: {e}")


# Skapa FastAPI-applikationen
app = FastAPI(
    title="Crypto Bot Dashboard API",
    description="API för Crypto Bot Dashboard",
    version="0.1.0",
    lifespan=lifespan
)

# Lägg till CORS-middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tillåt alla ursprung i utvecklingsläge
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lägg till API-routers
app.include_router(status_api.router)
app.include_router(balances_api.router)
app.include_router(orders_api.router)
app.include_router(backtest_api.router)
app.include_router(positions_api.router)
app.include_router(config_api.router)
app.include_router(bot_control_api.router)
app.include_router(monitoring_api.router)
app.include_router(portfolio_api.router)
app.include_router(risk_management_api.router)
app.include_router(market_data_api.router)
app.include_router(orderbook_api.router)
app.include_router(trading_limitations_api.router)

# Lägg till WebSocket-router om den inte är inaktiverad
if os.environ.get("FASTAPI_DISABLE_WEBSOCKETS", "false").lower() != "true":
    app.include_router(websocket_api.router)


@app.get("/", include_in_schema=False)
async def root():
    """Omdirigera rotvägen till API-dokumentationen."""
    return RedirectResponse(url="/docs")


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler för att hantera alla oväntade fel.
    """
    logger.error(f"Oväntat fel: {exc}", exc_info=True)
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": f"Internt serverfel: {str(exc)}"}
    )


if __name__ == "__main__":
    import uvicorn
    
    # Kontrollera om hot reload ska inaktiveras
    reload = os.environ.get("FASTAPI_NO_RELOAD", "false").lower() != "true"
    
    # Kör FastAPI-servern
    uvicorn.run("backend.fastapi_app:app", host="0.0.0.0", port=8001, reload=reload) 