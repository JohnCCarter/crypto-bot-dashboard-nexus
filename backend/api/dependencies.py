"""
Dependency injection for FastAPI.

This module provides dependencies for FastAPI dependency injection system.
"""

from typing import Callable, Dict, Any, Optional, List

from fastapi import Depends, Request

from backend.services.config_service import ConfigService
from backend.services.positions_service import fetch_live_positions_async
from backend.services.bot_manager import get_bot_status_async, start_bot_async, stop_bot_async
from backend.services.exchange import ExchangeService
from backend.services.exchange_async import (
    fetch_ohlcv_async,
    fetch_order_book_async,
    fetch_ticker_async,
    fetch_recent_trades_async,
    get_markets_async,
    get_exchange_status_async,
    create_mock_exchange_service
)
from backend.services.nonce_monitoring_service import (
    get_nonce_monitoring_service,
    EnhancedNonceMonitoringService
)
from backend.services.cache_service import (
    get_cache_service,
    EnhancedCacheService
)
from backend.services.global_nonce_manager import (
    get_global_nonce_manager,
    EnhancedGlobalNonceManager
)
from backend.services.order_service_async import (
    get_order_service_async,
    OrderServiceAsync
)
from backend.services.risk_manager_async import (
    get_risk_manager_async,
    RiskManagerAsync,
    RiskParameters,
    ProbabilityData
)
from backend.services.portfolio_manager_async import (
    get_portfolio_manager_async,
    PortfolioManagerAsync,
    StrategyWeight
)


# Service instances
config_service = ConfigService()


# Exchange service
def get_exchange_service(request: Request) -> Optional[ExchangeService]:
    """
    Get the exchange service from app state.
    
    Args:
        request: FastAPI request object with app state
    
    Returns:
    --------
    Optional[ExchangeService]: The exchange service instance or None if not available
    """
    if hasattr(request.app, "state"):
        if hasattr(request.app.state, "services"):
            return request.app.state.services.get("exchange")
    return None


# Config service dependencies
def get_config_service() -> ConfigService:
    """
    Get the config service instance.
    
    Returns:
    --------
    ConfigService: The config service instance
    """
    return config_service


# Positions service dependencies
async def get_positions_service() -> Callable:
    """
    Get the positions service function.
    
    Returns:
    --------
    Callable: The fetch_live_positions_async function
    """
    return fetch_live_positions_async


# Bot manager dependencies
class BotManagerDependency:
    """Bot manager dependency provider."""
    
    @staticmethod
    async def get_status() -> Dict[str, Any]:
        """
        Get the bot status.
        
        Returns:
        --------
        Dict[str, Any]: The bot status
        """
        return await get_bot_status_async()
    
    @staticmethod
    async def start_bot() -> Dict[str, Any]:
        """
        Start the bot.
        
        Returns:
        --------
        Dict[str, Any]: The result of the start operation
        """
        return await start_bot_async()
    
    @staticmethod
    async def stop_bot() -> Dict[str, Any]:
        """
        Stop the bot.
        
        Returns:
        --------
        Dict[str, Any]: The result of the stop operation
        """
        return await stop_bot_async()


# Bot manager dependency provider
def get_bot_manager() -> BotManagerDependency:
    """
    Get the bot manager dependency.
    
    Returns:
    --------
    BotManagerDependency: The bot manager dependency
    """
    return BotManagerDependency()


# Market data dependencies
class MarketDataDependency:
    """Market data dependency provider."""
    
    def __init__(self, exchange: ExchangeService):
        self.exchange = exchange
    
    async def fetch_ohlcv(self, symbol: str, timeframe: str = "5m", limit: int = 100):
        """
        Fetch OHLCV data.
        
        Args:
            symbol: Trading pair symbol
            timeframe: Timeframe for the OHLCV data
            limit: Number of candles to fetch
            
        Returns:
            List of OHLCV candles
        """
        return await fetch_ohlcv_async(self.exchange, symbol, timeframe, limit)
    
    async def fetch_order_book(self, symbol: str, limit: int = 20):
        """
        Fetch order book.
        
        Args:
            symbol: Trading pair symbol
            limit: Number of levels per side
            
        Returns:
            Order book data
        """
        return await fetch_order_book_async(self.exchange, symbol, limit)
    
    async def fetch_ticker(self, symbol: str):
        """
        Fetch ticker data.
        
        Args:
            symbol: Trading pair symbol
            
        Returns:
            Ticker data
        """
        return await fetch_ticker_async(self.exchange, symbol)
    
    async def fetch_recent_trades(self, symbol: str, limit: int = 50):
        """
        Fetch recent trades.
        
        Args:
            symbol: Trading pair symbol
            limit: Number of trades to fetch
            
        Returns:
            List of recent trades
        """
        return await fetch_recent_trades_async(self.exchange, symbol, limit)
    
    async def get_markets(self):
        """
        Fetch available markets.
        
        Returns:
            Dictionary of available markets
        """
        return await get_markets_async(self.exchange)
        
    async def get_status(self):
        """
        Get exchange status.
        
        Returns:
            Dictionary with status information
        """
        return await get_exchange_status_async(self.exchange)


# Market data dependency provider
def get_market_data(
    exchange: Optional[ExchangeService] = Depends(get_exchange_service)
) -> MarketDataDependency:
    """
    Get the market data dependency.
    
    Args:
        exchange: ExchangeService instance
        
    Returns:
    --------
    MarketDataDependency: The market data dependency
    """
    if exchange is None:
        # Skapa en mock om ingen riktig exchange-service finns tillgänglig
        exchange = create_mock_exchange_service()
    
    return MarketDataDependency(exchange)


# Monitoring dependencies
class MonitoringDependency:
    """Monitoring dependency provider."""
    
    @staticmethod
    def get_nonce_monitoring() -> EnhancedNonceMonitoringService:
        """
        Get nonce monitoring service.
        
        Returns:
            EnhancedNonceMonitoringService: The nonce monitoring service
        """
        return get_nonce_monitoring_service()
    
    @staticmethod
    def get_cache_service() -> EnhancedCacheService:
        """
        Get cache service.
        
        Returns:
            EnhancedCacheService: The cache service
        """
        return get_cache_service()
    
    @staticmethod
    def get_nonce_manager() -> EnhancedGlobalNonceManager:
        """
        Get global nonce manager.
        
        Returns:
            EnhancedGlobalNonceManager: The global nonce manager
        """
        return get_global_nonce_manager()


# Monitoring dependency provider
def get_monitoring() -> MonitoringDependency:
    """
    Get the monitoring dependency.
    
    Returns:
    --------
    MonitoringDependency: The monitoring dependency
    """
    return MonitoringDependency()


# Order service dependencies
async def get_order_service(
    exchange: Optional[ExchangeService] = Depends(get_exchange_service)
) -> OrderServiceAsync:
    """
    Get the order service.
    
    Args:
        exchange: Exchange service
        
    Returns:
    --------
    OrderServiceAsync: The async order service
    """
    if exchange is None:
        # Skapa en mock om ingen riktig exchange-service finns tillgänglig
        exchange = create_mock_exchange_service()
        
    return await get_order_service_async(exchange)


# Risk manager dependency provider
async def get_risk_manager() -> RiskManagerAsync:
    """
    Get the risk manager dependency.
    
    Returns:
    --------
    RiskManagerAsync: The async risk manager instance
    """
    # Use default parameters
    return await get_risk_manager_async()


# Portfolio manager dependency provider
async def get_portfolio_manager(
    risk_manager: RiskManagerAsync = Depends(get_risk_manager),
    config: ConfigService = Depends(get_config_service),
) -> PortfolioManagerAsync:
    """
    Get the portfolio manager dependency.
    
    Args:
        risk_manager: RiskManagerAsync instance
        config: ConfigService instance for strategy weights
        
    Returns:
    --------
    PortfolioManagerAsync: The async portfolio manager instance
    """
    # Get strategy weights from config
    strategy_config = config.get_strategy_weights() or {}
    strategy_weights = []
    
    for name, details in strategy_config.items():
        strategy_weights.append(
            StrategyWeight(
                strategy_name=name,
                weight=float(details.get("weight", 1.0)),
                min_confidence=float(details.get("min_confidence", 0.5)),
                enabled=bool(details.get("enabled", True))
            )
        )
    
    # Use default weights if none found in config
    if not strategy_weights:
        strategy_weights = [StrategyWeight(strategy_name="default", weight=1.0)]
    
    return await get_portfolio_manager_async(risk_manager, strategy_weights) 