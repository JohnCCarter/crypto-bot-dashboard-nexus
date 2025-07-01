"""
Async exchange service for cryptocurrency trading API endpoints.

This module provides asynchronous wrapper functions around the ExchangeService.
"""

import asyncio
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

from backend.services.exchange import ExchangeService, ExchangeError


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
        return await loop.run_in_executor(
            None, lambda: exchange.get_status()
        )
    except Exception as e:
        raise ExchangeError(f"Failed to check exchange status: {str(e)}")


def create_mock_exchange_service() -> MagicMock:
    """
    Create a mock exchange service for development and testing.
    
    Returns:
        MagicMock: A mocked ExchangeService
    """
    mock = MagicMock()
    mock.name = "bitfinex-mock"
    
    # Konfigurera mock-svar för vanliga metoder
    mock.fetch_ohlcv.return_value = [[1625097600000, 35000.0, 35100.0, 34900.0, 35050.0, 10.5]]
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
    mock.get_markets.return_value = {"tBTCUSD": {"symbol": "tBTCUSD", "base": "BTC", "quote": "USD"}}
    mock.get_status.return_value = {"status": "ok", "timestamp": 1625097600000}
    
    return mock 