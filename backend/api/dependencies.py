"""
Dependency injection for FastAPI.

This module provides dependencies for FastAPI dependency injection system.
"""

from typing import Callable, Dict, Any, Optional

from fastapi import Depends, Request, HTTPException, status
from unittest.mock import MagicMock, AsyncMock

from backend.services.config_service import ConfigService
from backend.services.bot_manager_async import BotManagerAsync, get_bot_manager_async
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
    RiskParameters
)
from backend.services.portfolio_manager_async import (
    get_portfolio_manager_async,
    PortfolioManagerAsync,
    StrategyWeight
)
# Använd bara fetch_positions_async från positions_service_async
from backend.services.positions_service_async import fetch_positions_async

import logging
import os
import asyncio
from functools import lru_cache

logger = logging.getLogger(__name__)


# Service instances
config_service = ConfigService()


# Exchange service
def get_exchange_service() -> Optional[ExchangeService]:
    """
    Get the exchange service.
    
    Returns:
    --------
    Optional[ExchangeService]: The exchange service instance or None if not available
    """
    # Import här för att undvika circular import
    from backend.fastapi_app import exchange_service
    return exchange_service


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
    Callable: The fetch_positions_async function
    """
    return fetch_positions_async


# Bot manager dependencies
class BotManagerDependency:
    """Bot manager dependency provider."""
    
    def __init__(self, bot_manager: BotManagerAsync):
        """
        Initialize the bot manager dependency.
        
        Args:
            bot_manager: BotManagerAsync instance
        """
        self.bot_manager = bot_manager
    
    async def get_status(self) -> Dict[str, Any]:
        """
        Get the bot status.
        
        Returns:
        --------
        Dict[str, Any]: The bot status
        
        Raises:
        -------
        HTTPException: If there's an error getting the status
        """
        try:
            status_result = await self.bot_manager.get_status()
            logger.debug(f"Bot status retrieved: {status_result.get('status', 'unknown')}")
            return status_result
        except Exception as e:
            logger.error(f"Error getting bot status: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get bot status: {str(e)}"
            )
    
    async def start_bot(self) -> Dict[str, Any]:
        """
        Start the bot.
        
        Returns:
        --------
        Dict[str, Any]: The result of the start operation
        
        Raises:
        -------
        HTTPException: If there's an error starting the bot
        """
        try:
            result = await self.bot_manager.start_bot()
            logger.info(f"Bot start attempt: {result}")
            return result
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start bot: {str(e)}"
            )
    
    async def stop_bot(self) -> Dict[str, Any]:
        """
        Stop the bot.
        
        Returns:
        --------
        Dict[str, Any]: The result of the stop operation
        
        Raises:
        -------
        HTTPException: If there's an error stopping the bot
        """
        try:
            result = await self.bot_manager.stop_bot()
            logger.info(f"Bot stop attempt: {result}")
            return result
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to stop bot: {str(e)}"
            )
    
    @property
    def dev_mode(self) -> bool:
        """
        Check if the bot is running in development mode.
        
        Returns:
        --------
        bool: True if in development mode, False otherwise
        """
        return self.bot_manager.dev_mode


# Bot manager dependency provider with caching
@lru_cache(maxsize=1)
def get_cached_bot_manager_dependency(dev_mode: bool = False) -> BotManagerDependency:
    """
    Get a cached BotManagerDependency instance.
    This helps avoid creating multiple instances during the request lifecycle.
    
    Args:
        dev_mode: Whether to run in development mode
        
    Returns:
    --------
    BotManagerDependency: The cached bot manager dependency
    """
    # Använd asyncio.run för att anropa den asynkrona funktionen i en synkron kontext
    # Detta används bara vid uppstart/cache-miss
    bot_manager = asyncio.run(get_bot_manager_async(dev_mode=dev_mode))
    return BotManagerDependency(bot_manager)


# Skapa en asynkron mock för bot manager
async def create_mock_bot_manager() -> AsyncMock:
    """
    Skapa en mock för BotManagerAsync som kan användas i utvecklingsläge.
    
    Returns:
    --------
    AsyncMock: En mock av BotManagerAsync
    """
    mock_bot_manager = AsyncMock(spec=BotManagerAsync)
    mock_bot_manager.dev_mode = True
    
    # Konfigurera mock-funktioner
    async def mock_get_status():
        return {
            "status": "mocked",
            "uptime": 0.0,
            "message": "Mocked bot manager in development mode",
            "thread_alive": False,
            "cycle_count": 0,
            "dev_mode": True
        }
    
    async def mock_start_bot():
        return {
            "success": True,
            "message": "Mock bot started in development mode",
            "status": "running"
        }
    
    async def mock_stop_bot():
        return {
            "success": True,
            "message": "Mock bot stopped in development mode",
            "status": "stopped"
        }
    
    # Sätt mock-funktioner
    mock_bot_manager.get_status = mock_get_status
    mock_bot_manager.start_bot = mock_start_bot
    mock_bot_manager.stop_bot = mock_stop_bot
    
    return mock_bot_manager


# Bot manager dependency provider
async def get_bot_manager() -> BotManagerDependency:
    """
    Get the bot manager dependency.
    
    Returns:
    --------
    BotManagerDependency: The bot manager dependency
    """
    # Kontrollera om vi är i utvecklingsläge
    dev_mode = os.environ.get("FASTAPI_DEV_MODE", "false").lower() == "true"
    
    try:
        # Skapa bot manager med dev_mode
        bot_manager = await get_bot_manager_async(dev_mode=dev_mode)
        logger.debug(f"BotManagerAsync created with dev_mode={dev_mode}")
        return BotManagerDependency(bot_manager)
    except Exception as e:
        logger.error(f"Failed to create BotManagerAsync: {e}")
        # Fallback till en mock i utvecklingsläge
        if dev_mode:
            logger.warning("Using mock BotManagerAsync in development mode due to error")
            mock_bot_manager = await create_mock_bot_manager()
            return BotManagerDependency(mock_bot_manager)
        # I produktionsläge, propagera felet
        raise


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
    
    # strategy_config är en dict, så den har items()-metoden
    # men strategy_weights är en lista utan items()-metod
    if isinstance(strategy_config, dict):
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


# Risk manager (legacy function name, renamed to avoid conflict)
def get_risk_manager_legacy() -> RiskManagerAsync:
    """
    Get an instance of the RiskManagerAsync.
    
    Returns:
    --------
    RiskManagerAsync: A risk manager instance
    """
    # Använd parametrar för att lösa lint-felet
    risk_params = RiskParameters(
        max_position_size=0.2,
        max_leverage=5.0,
        stop_loss_pct=0.05,
        take_profit_pct=0.1,
        max_daily_loss=0.05,
        max_open_positions=10
    )
    return RiskManagerAsync(risk_params)


# Nonce monitoring service dependency provider
def get_nonce_monitoring_service_dependency() -> EnhancedNonceMonitoringService:
    """
    Get the nonce monitoring service dependency.
    
    Returns:
    --------
    EnhancedNonceMonitoringService: The nonce monitoring service
    """
    return get_nonce_monitoring_service()


# Cache service dependency provider
def get_cache_service_dependency() -> EnhancedCacheService:
    """
    Get the cache service dependency.
    
    Returns:
    --------
    EnhancedCacheService: The cache service
    """
    return get_cache_service()


# Positions service async dependency provider
def get_positions_service_async() -> Callable:
    """
    Get the async positions service function.
    
    Returns:
    --------
    Callable: The fetch_positions_async function from positions_service_async
    """
    return fetch_positions_async