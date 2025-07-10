"""
Asynchronous trading window implementation.

This module provides an asynchronous implementation of the trading window functionality
with thread-safe state management using asyncio locks.
"""

import asyncio
import datetime
from typing import Dict


class TradingWindowAsync:
    def __init__(self, config: dict):
        """
        Initialize the async trading window with the given configuration.

        Args:
            config: Dictionary containing trading window configuration:
                - start_hour: Hour of day to start trading (default: 0)
                - end_hour: Hour of day to stop trading (default: 24)
                - max_trades_per_day: Maximum trades allowed per day (default: 5)
        """
        self.start_hour = config.get("start_hour", 0)
        self.end_hour = config.get("end_hour", 24)
        self.max_trades_per_day = config.get("max_trades_per_day", 5)
        self._state = {"trades_today": 0, "last_trade_date": None}
        self._lock = asyncio.Lock()

    async def is_within_window(self) -> bool:
        """
        Check if the current time is within the configured trading window.

        Returns:
            bool: True if within trading hours, False otherwise
        """
        now = datetime.datetime.now()
        return self.start_hour <= now.hour < self.end_hour

    async def can_trade(self) -> bool:
        """
        Check if trading is allowed based on daily trade limits.
        Updates internal counters if date has changed.

        Returns:
            bool: True if trading is allowed, False otherwise
        """
        async with self._lock:
            today = datetime.date.today()
            if self._state["last_trade_date"] != today:
                self._state["trades_today"] = 0
                self._state["last_trade_date"] = today
            return self._state["trades_today"] < self.max_trades_per_day

    async def register_trade(self) -> None:
        """
        Register a trade execution, incrementing the daily counter.
        Resets counter if date has changed.
        """
        async with self._lock:
            today = datetime.date.today()
            if self._state["last_trade_date"] != today:
                self._state["trades_today"] = 0
                self._state["last_trade_date"] = today
            self._state["trades_today"] += 1

    async def get_remaining_trades(self) -> int:
        """
        Get the number of remaining trades allowed for today.

        Returns:
            int: Number of remaining trades for today
        """
        async with self._lock:
            today = datetime.date.today()
            if self._state["last_trade_date"] != today:
                return self.max_trades_per_day
            return max(0, self.max_trades_per_day - self._state["trades_today"])

    async def get_state(self) -> Dict:
        """
        Get the current state of the trading window.

        Returns:
            Dict: Current trading window state
        """
        async with self._lock:
            return {
                "within_window": await self.is_within_window(),
                "can_trade": self._state["trades_today"] < self.max_trades_per_day,
                "trades_today": self._state["trades_today"],
                "max_trades_per_day": self.max_trades_per_day,
                "remaining_trades": max(
                    0, self.max_trades_per_day - self._state["trades_today"]
                ),
                "trading_hours": f"{self.start_hour}:00 - {self.end_hour}:00",
                "last_trade_date": self._state["last_trade_date"],
            }


async def get_trading_window_async(config: dict = None) -> TradingWindowAsync:
    """
    Factory function to create and return a TradingWindowAsync instance.

    Args:
        config: Optional configuration dictionary (default: empty dict)

    Returns:
        TradingWindowAsync: Configured trading window instance
    """
    if config is None:
        config = {}
    return TradingWindowAsync(config)
