"""
FastAPI application entry point.
This module provides the FastAPI application instance and configuration.
"""

import os
import logging
from typing import Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status as http_status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
from backend.services.exchange import ExchangeService, ExchangeError
from backend.services.exchange_async import create_mock_exchange_service

# Ladda miljövariabler
load_dotenv()

# Konfigurera loggning
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("fastapi_app")


# Livscykelhanterare
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Hantera applikationens livscykel (startup och shutdown).
    
    Args:
        app: FastAPI-applikation
    """
    # Startup-kod
    logger.info("Initializing services...")
    
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
        app.state = type("AppState", (), {})
    
    # Försök initialisera ExchangeService
    try:
        exchange_service = ExchangeService("bitfinex", api_key, api_secret)
        app.state.services = {"exchange": exchange_service}
        logger.info("Services initialized successfully")
    except ExchangeError as e:
        logger.error(f"Failed to initialize exchange service: {e}")
        # Använd vår fördefinierade mock ExchangeService för utveckling
        mock_exchange = create_mock_exchange_service()
        app.state.services = {"exchange": mock_exchange}
        logger.warning("Using mock exchange service for development")
    
    yield
    
    # Shutdown-kod
    logger.info("Shutting down services...")


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
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error", "details": str(exc)},
    )

# Grundläggande endpoints
@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint redirects to docs."""
    return {"message": "API is running. Visit /docs for documentation."}

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