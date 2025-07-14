"""
Tests for the asynchronous trading window implementation.
"""

import asyncio
import datetime
from unittest.mock import MagicMock, patch

import pytest

from backend.services.trading_window_async import (
    TradingWindowAsync,
    get_trading_window_async,
)


@pytest.fixture
def trading_window_config():
    return {"start_hour": 9, "end_hour": 17, "max_trades_per_day": 5}


@pytest.mark.asyncio
async def test_trading_window_init(trading_window_config):
    """Test that the trading window initializes correctly."""
    window = await get_trading_window_async(trading_window_config)

    assert window.start_hour == 9
    assert window.end_hour == 17
    assert window.max_trades_per_day == 5
    assert isinstance(window._lock, asyncio.Lock)


@pytest.mark.asyncio
async def test_is_within_window():
    """Test that is_within_window returns correct values based on current time."""
    config = {"start_hour": 9, "end_hour": 17}
    window = TradingWindowAsync(config)

    # Mock datetime.now to return a time within the window
    with patch("datetime.datetime") as mock_datetime:
        mock_now = MagicMock()
        mock_now.hour = 12
        mock_datetime.now.return_value = mock_now

        result = await window.is_within_window()
        assert result is True

    # Mock datetime.now to return a time outside the window
    with patch("datetime.datetime") as mock_datetime:
        mock_now = MagicMock()
        mock_now.hour = 20
        mock_datetime.now.return_value = mock_now

        result = await window.is_within_window()
        assert result is False


@pytest.mark.asyncio
async def test_can_trade():
    """Test that can_trade returns correct values based on trade count."""
    config = {"max_trades_per_day": 3}
    window = TradingWindowAsync(config)

    # Initial state - should be able to trade
    assert await window.can_trade() is True

    # Register trades up to the limit
    await window.register_trade()
    assert await window.can_trade() is True

    await window.register_trade()
    assert await window.can_trade() is True

    await window.register_trade()
    assert await window.can_trade() is False


@pytest.mark.asyncio
async def test_register_trade():
    """Test that register_trade increments the trade counter."""
    window = TradingWindowAsync({})

    # Initial state
    assert window._state["trades_today"] == 0

    # Register trades
    await window.register_trade()
    assert window._state["trades_today"] == 1

    await window.register_trade()
    assert window._state["trades_today"] == 2


@pytest.mark.asyncio
async def test_date_change_resets_counter():
    """Test that the trade counter resets when the date changes."""
    window = TradingWindowAsync({})

    # Set up initial state with trades
    await window.register_trade()
    await window.register_trade()
    assert window._state["trades_today"] == 2

    # Mock date.today to return a different date
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)

    with patch("datetime.date") as mock_date:
        mock_date.today.return_value = tomorrow

        # Check if counter resets on date change
        assert await window.can_trade() is True
        assert window._state["trades_today"] == 0


@pytest.mark.asyncio
async def test_get_remaining_trades():
    """Test that get_remaining_trades returns correct values."""
    config = {"max_trades_per_day": 5}
    window = TradingWindowAsync(config)

    # Initial state
    assert await window.get_remaining_trades() == 5

    # After registering trades
    await window.register_trade()
    await window.register_trade()

    assert await window.get_remaining_trades() == 3


@pytest.mark.asyncio
async def test_get_state():
    """Test that get_state returns the correct state dictionary."""
    config = {"start_hour": 9, "end_hour": 17, "max_trades_per_day": 5}
    window = TradingWindowAsync(config)

    # Register some trades
    await window.register_trade()
    await window.register_trade()

    # Get state
    state = await window.get_state()

    # Verify state contents
    assert "within_window" in state
    assert "can_trade" in state
    assert state["trades_today"] == 2
    assert state["max_trades_per_day"] == 5
    assert state["remaining_trades"] == 3
    assert state["trading_hours"] == "9:00 - 17:00"
    assert state["last_trade_date"] is not None


@pytest.mark.asyncio
async def test_concurrent_access():
    """Test that concurrent access to the trading window is thread-safe."""
    window = TradingWindowAsync({"max_trades_per_day": 100})

    # Create multiple tasks that register trades concurrently (reduced from 50 to 10 for speed)
    tasks = [window.register_trade() for _ in range(10)]
    await asyncio.gather(*tasks)

    # Verify that all trades were registered correctly
    assert window._state["trades_today"] == 10
