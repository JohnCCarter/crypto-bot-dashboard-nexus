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
from backend.api import config as config_api
from backend.api import positions as positions_api
from backend.api import bot_control as bot_control_api
from backend.api import market_data as market_data_api
from backend.api import orderbook as orderbook_api
from backend.api import monitoring as monitoring_api
from backend.api import risk_management as risk_management_api
from backend.api import portfolio as portfolio_api
from backend.api import websocket as websocket_api
from backend.services.exchange import ExchangeService, ExchangeError
from backend.services.exchange_async import create_mock_exchange_service, init_exchange_async
from backend.services.websocket_market_service import start_websocket_service, stop_websocket_service

# Ladda miljövariabler
# För utveckling - använd DOTENV_PATH om den är angiven
custom_env_path = os.getenv("DOTENV_PATH")
if custom_env_path and os.path.exists(custom_env_path):
    load_dotenv(custom_env_path)
    print(f"📝 Laddar anpassade inställningar från: {custom_env_path}")
else:
    load_dotenv()
    print("📝 Laddar standardinställningar från .env")

# Konfigurera loggning
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("fastapi_app")

# Konfigureringsalternativ
DISABLE_WEBSOCKET = os.getenv("DISABLE_WEBSOCKET", "").lower() == "true"
DISABLE_NONCE_MANAGER = os.getenv("DISABLE_NONCE_MANAGER", "").lower() == "true"
MOCK_EXCHANGE_SERVICE = os.getenv("MOCK_EXCHANGE_SERVICE", "").lower() == "true"

if DISABLE_WEBSOCKET:
    logger.info("⚠️ WebSockets är inaktiverade i denna konfiguration")
if DISABLE_NONCE_MANAGER:
    logger.info("⚠️ GlobalNonceManager är inaktiverad i denna konfiguration")
if MOCK_EXCHANGE_SERVICE:
    logger.info("🔧 Använder mock exchange service i denna konfiguration")


# Livscykelhanterare
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Hantera applikationens livscykel (startup och shutdown).
    
    Args:
        app: FastAPI-applikation
    """
    # Startup-kod
    logger.info("🚀 Starting FastAPI application...")
    
    # Hämta API-nyckel och hemlighet från miljövariabler
    api_key = os.getenv("BITFINEX_API_KEY", "")
    api_secret = os.getenv("BITFINEX_API_SECRET", "")
    
    if not api_key or not api_secret:
        logger.warning(
            "Bitfinex API key or secret not found in environment variables. "
            "Exchange service will be initialized with empty credentials."
        )
    
    # Initialisera services och lagra i app.state
    if not hasattr(app, "state"):
        app.state = {}  # Använd dict istället för type för att undvika lint-fel
    
    # Försök initialisera ExchangeService
    try:
        if MOCK_EXCHANGE_SERVICE:
            logger.info("Using mock exchange service as configured")
            mock_exchange = create_mock_exchange_service()
            app.state["services"] = {"exchange": mock_exchange}
        else:
            exchange_service = ExchangeService("bitfinex", api_key, api_secret)
            app.state["services"] = {"exchange": exchange_service}
            logger.info("Services initialized successfully")
    except ExchangeError as e:
        logger.error(f"Failed to initialize exchange service: {e}")
        # Använd vår fördefinierade mock ExchangeService för utveckling
        mock_exchange = create_mock_exchange_service()
        app.state["services"] = {"exchange": mock_exchange}
        logger.warning("Using mock exchange service for development")
    
    # Initialize exchange service
    await init_exchange_async()
    
    # Starta WebSocket-tjänsten för marknadsdata om den inte är inaktiverad
    if not DISABLE_WEBSOCKET:
        try:
            await start_websocket_service()
            logger.info("WebSocket market service started successfully")
        except Exception as e:
            logger.error(f"Failed to start WebSocket market service: {e}")
    
    logger.info("✅ FastAPI application startup complete")
    yield
    
    # Shutdown-kod
    logger.info("👋 Shutting down FastAPI application...")
    
    # Stoppa WebSocket-tjänsten om den är aktiverad
    if not DISABLE_WEBSOCKET:
        try:
            await stop_websocket_service()
            logger.info("WebSocket market service stopped successfully")
        except Exception as e:
            logger.error(f"Failed to stop WebSocket market service: {e}")
    
    # Stoppa GlobalNonceManager för att frigöra resurser om den är aktiverad
    if not DISABLE_NONCE_MANAGER:
        try:
            from backend.services.global_nonce_manager import get_global_nonce_manager
            nonce_manager = get_global_nonce_manager()
            nonce_manager.shutdown()
            logger.info("GlobalNonceManager shutdown complete")
        except Exception as e:
            logger.error(f"Failed to shutdown GlobalNonceManager: {e}")
    
    logger.info("✅ FastAPI application shutdown complete")


# Skapa FastAPI-applikation
app = FastAPI(
    title="Crypto Bot Dashboard API",
    description="API för Crypto Bot Dashboard",
    version="0.1.0",
    lifespan=lifespan,
)

# Konfigurera CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ändra till specifika origins i produktion
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware för loggning av requests
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and their processing time."""
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    return response

# Felhantering
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """Handle HTTP exceptions and return appropriate JSON response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail},
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    logger.error(f"Uncaught exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "details": str(exc)},
    )

# Grundläggande endpoints
@app.get("/", include_in_schema=False)
async def root():
    """Redirect to API documentation."""
    return RedirectResponse(url="/docs")

@app.get("/api/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}

@app.get("/api/status")
async def api_status() -> Dict[str, Any]:
    """Status endpoint, returns system status."""
    return {
        "status": "operational",
        "version": "0.1.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "websocket_enabled": not DISABLE_WEBSOCKET,
        "nonce_manager_enabled": not DISABLE_NONCE_MANAGER,
        "using_mock_exchange": MOCK_EXCHANGE_SERVICE
    }

# Inkludera API-routers
app.include_router(status_api.router)
app.include_router(balances_api.router)
app.include_router(orders_api.router)
app.include_router(backtest_api.router)
app.include_router(config_api.router)
app.include_router(positions_api.router)
app.include_router(bot_control_api.router)
app.include_router(market_data_api.router)
app.include_router(orderbook_api.router)
app.include_router(monitoring_api.router)
app.include_router(risk_management_api.router)
app.include_router(portfolio_api.router)
app.include_router(websocket_api.router)
logger.info("API routes loaded successfully")

# Om denna fil körs direkt, starta Uvicorn-server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.fastapi_app:app", 
        host="0.0.0.0", 
        port=int(os.getenv("FASTAPI_PORT", "8001")),
        reload=True
    )

# Startup message
logger.info("📡 FastAPI application configured with all endpoints")
logger.info("📚 API documentation available at /docs and /redoc")
logger.info("🔄 FastAPI server will run on port 8001 in parallel with Flask") 