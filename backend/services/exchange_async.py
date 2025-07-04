"""
Async exchange service for cryptocurrency trading API endpoints.

This module provides asynchronous wrapper functions around the ExchangeService.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

from backend.services.exchange import ExchangeService, ExchangeError

logger = logging.getLogger(__name__)

# Global exchange instance
_exchange_instance = None


async def init_exchange_async() -> None:
    """
    Initialize the exchange service asynchronously.
    
    This function creates a global exchange instance that can be used
    by other async functions in this module.
    """
    global _exchange_instance
    
    try:
        logger.info("🚀 Initializing exchange service asynchronously...")
        
        # Create exchange service
        # This is a placeholder for now - in the future we might want to
        # use a truly async exchange client like ccxt.async_support
        _exchange_instance = ExchangeService(
            exchange_id="bitfinex",
            api_key="",
            api_secret=""
        )
        
        logger.info("✅ Exchange service initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize exchange service: {str(e)}")
        # Create a mock exchange service as fallback
        _exchange_instance = create_mock_exchange_service()
        logger.warning("⚠️ Using mock exchange service as fallback")


async def fetch_balance_async(exchange: ExchangeService) -> Dict[str, Any]:
    """
    Fetch account balance asynchronously.
    
    Args:
        exchange: ExchangeService instance
        
    Returns:
        Dict containing balance information
        
    Raises:
        ExchangeError: If balance fetching fails
    """
    try:
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: exchange.fetch_balance()
        )
    except Exception as e:
        raise ExchangeError(f"Failed to fetch balance asynchronously: {str(e)}")


async def fetch_ohlcv_async(
    exchange: ExchangeService, symbol: str, timeframe: str = "5m", limit: int = 100
) -> List[List[float]]:
    """
    Fetch OHLCV data asynchronously.
    
    Args:
        exchange: ExchangeService instance
        symbol: Trading pair symbol
        timeframe: Timeframe for the OHLCV data
        limit: Number of candles to fetch
        
    Returns:
        List of OHLCV candles
        
    Raises:
        ExchangeError: If fetching OHLCV data fails
    """
    try:
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: exchange.fetch_ohlcv(symbol, timeframe, limit)
        )
    except Exception as e:
        raise ExchangeError(f"Failed to fetch OHLCV data: {str(e)}")


async def fetch_order_book_async(
    exchange: ExchangeService, symbol: str, limit: int = 20
) -> Dict[str, Any]:
    """
    Fetch order book asynchronously.
    
    Args:
        exchange: ExchangeService instance
        symbol: Trading pair symbol
        limit: Number of levels per side
        
    Returns:
        Order book data
        
    Raises:
        ExchangeError: If fetching order book fails
    """
    try:
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: exchange.fetch_order_book(symbol, limit)
        )
    except Exception as e:
        raise ExchangeError(f"Failed to fetch order book: {str(e)}")


async def fetch_ticker_async(
    exchange: ExchangeService, symbol: str
) -> Dict[str, Any]:
    """
    Fetch ticker data asynchronously.
    
    Args:
        exchange: ExchangeService instance
        symbol: Trading pair symbol
        
    Returns:
        Ticker data
        
    Raises:
        ExchangeError: If fetching ticker fails
    """
    try:
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: exchange.fetch_ticker(symbol)
        )
    except Exception as e:
        raise ExchangeError(f"Failed to fetch ticker: {str(e)}")


async def fetch_recent_trades_async(
    exchange: ExchangeService, symbol: str, limit: int = 50
) -> List[Dict[str, Any]]:
    """
    Fetch recent trades asynchronously.
    
    Args:
        exchange: ExchangeService instance
        symbol: Trading pair symbol
        limit: Number of trades to fetch
        
    Returns:
        List of recent trades
        
    Raises:
        ExchangeError: If fetching trades fails
    """
    try:
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: exchange.fetch_recent_trades(symbol, limit)
        )
    except Exception as e:
        raise ExchangeError(f"Failed to fetch recent trades: {str(e)}")


async def get_markets_async(
    exchange: ExchangeService
) -> Dict[str, Any]:
    """
    Fetch available markets asynchronously.
    
    Args:
        exchange: ExchangeService instance
        
    Returns:
        Dictionary of available markets
        
    Raises:
        ExchangeError: If fetching markets fails
    """
    try:
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: exchange.get_markets()
        )
    except Exception as e:
        raise ExchangeError(f"Failed to fetch markets: {str(e)}")


async def get_exchange_status_async(
    exchange: ExchangeService
) -> Dict[str, Any]:
    """
    Check exchange status asynchronously.
    
    Args:
        exchange: ExchangeService instance
        
    Returns:
        Dictionary with exchange status information
        
    Raises:
        ExchangeError: If checking status fails
    """
    try:
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        # Använd exchange.exchange.fetchStatus() istället för get_status
        return await loop.run_in_executor(
            None, lambda: exchange.exchange.fetchStatus()
        )
    except Exception as e:
        msg = f"Failed to check exchange status: {str(e)}"
        raise ExchangeError(msg)


async def create_order_async(
    exchange: ExchangeService,
    symbol: str,
    order_type: str,
    side: str,
    amount: float,
    price: Optional[float] = None,
    position_type: str = "spot",
) -> Dict[str, Any]:
    """
    Create a new order asynchronously.
    
    Args:
        exchange: ExchangeService instance
        symbol: Trading pair (e.g. 'BTC/USD')
        order_type: 'market' or 'limit'
        side: 'buy' or 'sell'
        amount: Order size
        price: Required for limit orders
        position_type: 'margin' or 'spot'
        
    Returns:
        Dict containing order details
        
    Raises:
        ExchangeError: If order creation fails
    """
    try:
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            lambda: exchange.create_order(
                symbol=symbol,
                order_type=order_type,
                side=side,
                amount=amount,
                price=price,
                position_type=position_type
            )
        )
    except Exception as e:
        raise ExchangeError(f"Failed to create order asynchronously: {str(e)}")


async def fetch_order_async(
    exchange: ExchangeService, order_id: str, symbol: str
) -> Dict[str, Any]:
    """
    Fetch order details asynchronously.
    
    Args:
        exchange: ExchangeService instance
        order_id: Exchange order ID
        symbol: Trading pair
        
    Returns:
        Dict containing order details
        
    Raises:
        ExchangeError: If order fetch fails
    """
    try:
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: exchange.fetch_order(order_id, symbol)
        )
    except Exception as e:
        raise ExchangeError(f"Failed to fetch order asynchronously: {str(e)}")


async def cancel_order_async(
    exchange: ExchangeService, order_id: str, symbol: Optional[str] = None
) -> bool:
    """
    Cancel an order asynchronously.
    
    Args:
        exchange: ExchangeService instance
        order_id: Exchange order ID
        symbol: Trading pair (optional)
        
    Returns:
        True if order was cancelled successfully
        
    Raises:
        ExchangeError: If order cancellation fails
    """
    try:
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: exchange.cancel_order(order_id, symbol)
        )
    except Exception as e:
        raise ExchangeError(f"Failed to cancel order asynchronously: {str(e)}")


async def fetch_open_orders_async(
    exchange: ExchangeService, symbol: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Fetch open orders asynchronously.
    
    Args:
        exchange: ExchangeService instance
        symbol: Trading pair (optional)
        
    Returns:
        List of open orders
        
    Raises:
        ExchangeError: If fetching open orders fails
    """
    try:
        # Run the synchronous method in a thread pool
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: exchange.fetch_open_orders(symbol)
        )
    except Exception as e:
        raise ExchangeError(f"Failed to fetch open orders asynchronously: {str(e)}")


def create_mock_exchange_service() -> MagicMock:
    """
    Create a mock exchange service for development and testing.
    
    Returns:
        MagicMock: A mocked ExchangeService
    """
    mock = MagicMock()
    mock.name = "bitfinex-mock"
    
    # Konfigurera mock-svar för vanliga metoder
    mock.fetch_ohlcv.return_value = [
        [1625097600000, 35000.0, 35100.0, 34900.0, 35050.0, 10.5]
    ]
    mock.fetch_order_book.return_value = {
        "bids": [[35000.0, 1.5], [34900.0, 2.3]], 
        "asks": [[35100.0, 1.2], [35200.0, 3.4]]
    }
    mock.fetch_ticker.return_value = {
        "symbol": "tBTCUSD",
        "bid": 35000.0,
        "ask": 35100.0,
        "last": 35050.0,
        "volume": 1000.5
    }
    mock.fetch_recent_trades.return_value = [
        {"id": 1, "price": 35050.0, "amount": 0.1, "timestamp": 1625097600000}
    ]
    mock.get_markets.return_value = {
        "tBTCUSD": {"symbol": "tBTCUSD", "base": "BTC", "quote": "USD"}
    }
    # Skapa en nested mock för exchange-attributet
    mock.exchange = MagicMock()
    mock.exchange.fetchStatus.return_value = {"status": "ok", "timestamp": 1625097600000}
    
    return mock 