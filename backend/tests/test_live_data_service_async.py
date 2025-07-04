"""
Test the async live data service.
"""

import pytest
import pandas as pd
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio

from backend.services.live_data_service_async import (
    LiveDataServiceAsync,
    get_live_data_service_async,
    close_live_data_service_async
)


@pytest.fixture
async def mock_live_data_service():
    """Create a mock live data service."""
    service = LiveDataServiceAsync()
    
    # Mock the exchange
    service.exchange = MagicMock()
    
    # Mock fetch_ohlcv
    mock_ohlcv_data = [
        [1625097600000, 35000.0, 35100.0, 34900.0, 35050.0, 10.5],
        [1625097900000, 35050.0, 35200.0, 35000.0, 35150.0, 15.2]
    ]
    service.exchange.fetch_ohlcv = AsyncMock(return_value=mock_ohlcv_data)
    
    # Mock fetch_ticker
    mock_ticker = {
        "symbol": "BTC/USD",
        "last": 35150.0,
        "baseVolume": 100.5,
        "change": 150.0,
        "percentage": 0.43
    }
    service.exchange.fetch_ticker = AsyncMock(return_value=mock_ticker)
    
    # Mock fetch_order_book
    mock_orderbook = {
        "bids": [[35000.0, 1.5], [34900.0, 2.3]],
        "asks": [[35200.0, 1.2], [35300.0, 3.4]]
    }
    service.exchange.fetch_order_book = AsyncMock(return_value=mock_orderbook)
    
    # Mock close method
    service.exchange.close = AsyncMock()
    
    yield service
    
    # Clean up
    if hasattr(service, 'exchange') and service.exchange:
        await service.close()


@pytest.mark.asyncio
async def test_fetch_live_ohlcv(mock_live_data_service):
    """Test fetching live OHLCV data."""
    # Call the method
    df = await mock_live_data_service.fetch_live_ohlcv("BTC/USD", "5m", 100)
    
    # Verify the exchange method was called
    mock_live_data_service.exchange.fetch_ohlcv.assert_called_once_with("BTC/USD", "5m", limit=100)
    
    # Verify the result is a DataFrame with the expected columns
    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert len(df) == 2


@pytest.mark.asyncio
async def test_fetch_live_ticker(mock_live_data_service):
    """Test fetching live ticker data."""
    # Call the method
    ticker = await mock_live_data_service.fetch_live_ticker("BTC/USD")
    
    # Verify the exchange method was called
    mock_live_data_service.exchange.fetch_ticker.assert_called_once_with("BTC/USD")
    
    # Verify the result is a dictionary with the expected keys
    assert isinstance(ticker, dict)
    assert ticker["symbol"] == "BTC/USD"
    assert ticker["last"] == 35150.0


@pytest.mark.asyncio
async def test_fetch_live_orderbook(mock_live_data_service):
    """Test fetching live orderbook data."""
    # Call the method
    orderbook = await mock_live_data_service.fetch_live_orderbook("BTC/USD", 20)
    
    # Verify the exchange method was called
    mock_live_data_service.exchange.fetch_order_book.assert_called_once_with("BTC/USD", 20)
    
    # Verify the result is a dictionary with the expected keys
    assert isinstance(orderbook, dict)
    assert "bids" in orderbook
    assert "asks" in orderbook
    assert len(orderbook["bids"]) == 2
    assert len(orderbook["asks"]) == 2


@pytest.mark.asyncio
async def test_get_live_market_context(mock_live_data_service):
    """Test getting live market context."""
    # Call the method
    context = await mock_live_data_service.get_live_market_context("BTC/USD", "5m", 100)
    
    # Verify the result is a dictionary with the expected keys
    assert isinstance(context, dict)
    assert context["symbol"] == "BTC/USD"
    assert "ohlcv_data" in context
    assert "ticker" in context
    assert "orderbook" in context
    assert "current_price" in context
    assert "best_bid" in context
    assert "best_ask" in context
    assert "spread" in context
    assert "volume_24h" in context
    assert "volatility_pct" in context


@pytest.mark.asyncio
async def test_validate_market_conditions(mock_live_data_service):
    """Test validating market conditions."""
    # Create a mock market context
    market_context = {
        "symbol": "BTC/USD",
        "current_price": 35150.0,
        "best_bid": 35000.0,
        "best_ask": 35200.0,
        "spread": 200.0,
        "volatility_pct": 5.0
    }
    
    # Call the method
    valid, reason = await mock_live_data_service.validate_market_conditions(market_context)
    
    # Verify the result
    assert valid is True
    assert reason == "Market conditions are suitable for trading"


@pytest.mark.asyncio
async def test_singleton_instance():
    """Test the singleton instance functionality."""
    # Get the first instance
    service1 = await get_live_data_service_async()
    
    # Get another instance (should be the same)
    service2 = await get_live_data_service_async()
    
    # Verify they are the same instance
    assert service1 is service2
    
    # Clean up
    await close_live_data_service_async()
    
    # Get a new instance (should be different)
    service3 = await get_live_data_service_async()
    
    # Verify it's a different instance
    assert service1 is not service3
    
    # Clean up
    await close_live_data_service_async() 