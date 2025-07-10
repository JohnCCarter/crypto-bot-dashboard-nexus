"""
API routes module for FastAPI.
"""

from fastapi import APIRouter

from backend.api import (
    backtest,
    bot_control,
    config,
    market_data,
    monitoring,
    orderbook,
    orders,
    portfolio,
    positions,
    risk_management,
    websocket,
)
from backend.api.balances import router as balances_router
from backend.api.status import router as status_router

# Create API router
api_router = APIRouter()

# Routers will be included after they are created
# Example: api_router.include_router(status_router)

# Include all routers
api_router.include_router(status_router)
api_router.include_router(balances_router)
api_router.include_router(orders.router)
api_router.include_router(backtest.router)
api_router.include_router(config.router)
api_router.include_router(positions.router)
api_router.include_router(bot_control.router)
api_router.include_router(market_data.router)
api_router.include_router(orderbook.router)
api_router.include_router(monitoring.router)
api_router.include_router(risk_management.router)
api_router.include_router(portfolio.router)
api_router.include_router(websocket.router)

__all__ = [
    "status",
    "balances",
    "orders",
    "backtest",
    "config",
    "positions",
    "bot_control",
    "market_data",
    "orderbook",
    "monitoring",
    "risk_management",
    "portfolio",
    "websocket",
]
