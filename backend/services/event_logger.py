#!/usr/bin/env python3
"""
🎯 Event-Driven Logging Service

Detta ersätter massa teknisk loggning med fokus på verkliga användaraktioner:
- Trades och order
- Bot start/stop
- Parameter ändringar
- Valuta byten
- Fel och varningar

INTE rutinmässig polling av marknadsdata, balancer etc.
"""

import logging
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types that should be logged"""

    # User actions
    TRADE_PLACED = "trade_placed"
    ORDER_CREATED = "order_created"
    ORDER_CANCELLED = "order_cancelled"

    # Bot management
    BOT_STARTED = "bot_started"
    BOT_STOPPED = "bot_stopped"
    BOT_ERROR = "bot_error"

    # Configuration changes
    PARAMETER_CHANGED = "parameter_changed"
    STRATEGY_CHANGED = "strategy_changed"
    CURRENCY_CHANGED = "currency_changed"

    # System events
    API_ERROR = "api_error"
    EXCHANGE_ERROR = "exchange_error"
    CRITICAL_ERROR = "critical_error"

    # Backtest runs (user initiated)
    BACKTEST_STARTED = "backtest_started"
    BACKTEST_COMPLETED = "backtest_completed"


class EventLogger:
    """
    Event-driven logger som endast loggar meningsfulla händelser
    """

    def __init__(self):
        self.logger = logging.getLogger("event_logger")

    def log_event(
        self,
        event_type: EventType,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ):
        """
        Logga en meningsfull händelse

        Args:
            event_type: Typ av händelse
            message: Huvudmeddelande
            details: Extra detaljer
            user_id: Användar-ID om tillämpligt
        """
        timestamp = datetime.now().isoformat()

        # Format: [TIMESTAMP] EVENT_TYPE: MESSAGE | details
        log_message = f"🎯 [{timestamp}] {event_type.value.upper()}: " f"{message}"

        if details:
            detail_str = " | ".join([f"{k}: {v}" for k, v in details.items()])
            log_message += f" | {detail_str}"

        if user_id:
            log_message += f" | user: {user_id}"

        # Använd WARNING för alla events för att undvika spam
        # Endast verkligt viktiga events ska loggas nu
        self.logger.warning(log_message)

    def log_trade(
        self,
        symbol: str,
        side: str,
        amount: float,
        price: float,
        order_id: str,
        strategy: Optional[str] = None,
    ):
        """Logga trade execution"""
        details = {
            "symbol": symbol,
            "side": side,
            "amount": str(amount),
            "price": str(price),
            "order_id": order_id,
        }
        if strategy:
            details["strategy"] = strategy

        self.log_event(
            EventType.TRADE_PLACED,
            f"{side.upper()} {amount} {symbol} @ ${price}",
            details,
        )

    def log_order_creation(
        self, symbol: str, side: str, amount: float, price: float, order_type: str
    ):
        """Logga order creation"""
        message = f"Created {order_type} {side} order: " f"{amount} {symbol} @ ${price}"
        self.log_event(
            EventType.ORDER_CREATED,
            message,
            {
                "symbol": symbol,
                "side": side,
                "amount": str(amount),
                "price": str(price),
                "type": order_type,
            },
        )

    def log_bot_action(self, action: str, details: Optional[Dict[str, Any]] = None):
        """Logga bot start/stop"""
        event_type = (
            EventType.BOT_STARTED if action == "start" else EventType.BOT_STOPPED
        )
        self.log_event(event_type, f"Trading bot {action}ed", details)

    def log_parameter_change(self, parameter: str, old_value: Any, new_value: Any):
        """Logga parameter ändringar"""
        message = f"Parameter '{parameter}' changed: " f"{old_value} -> {new_value}"
        self.log_event(
            EventType.PARAMETER_CHANGED,
            message,
            {"parameter": parameter, "old": str(old_value), "new": str(new_value)},
        )

    def log_strategy_change(self, old_strategy: str, new_strategy: str):
        """Logga strategy ändringar"""
        message = f"Strategy changed: {old_strategy} -> {new_strategy}"
        self.log_event(
            EventType.STRATEGY_CHANGED,
            message,
            {"old_strategy": old_strategy, "new_strategy": new_strategy},
        )

    def log_currency_change(self, old_symbol: str, new_symbol: str):
        """Logga valuta byten"""
        message = f"Trading pair changed: {old_symbol} -> {new_symbol}"
        self.log_event(
            EventType.CURRENCY_CHANGED,
            message,
            {"old_symbol": old_symbol, "new_symbol": new_symbol},
        )

    def log_backtest(self, strategy: str, symbol: str, result: Dict[str, Any]):
        """Logga backtest körning"""
        self.log_event(
            EventType.BACKTEST_COMPLETED,
            f"Backtest completed: {strategy} on {symbol}",
            {
                "strategy": strategy,
                "symbol": symbol,
                "total_trades": str(result.get("total_trades", 0)),
                "win_rate": str(result.get("win_rate", 0)),
                "total_pnl": str(result.get("total_pnl", 0)),
            },
        )

    def log_api_error(
        self, endpoint: str, error: str, retry_count: Optional[int] = None
    ):
        """Logga API fel"""
        details = {"endpoint": endpoint, "error": error}
        if retry_count is not None:
            details["retry_count"] = str(retry_count)

        self.log_event(
            EventType.API_ERROR, f"API error on {endpoint}: {error}", details
        )

    def log_exchange_error(self, operation: str, error: str):
        """Logga exchange fel"""
        message = f"Exchange error during {operation}: {error}"
        self.log_event(
            EventType.EXCHANGE_ERROR, message, {"operation": operation, "error": error}
        )


# Global instance
event_logger = EventLogger()


def should_suppress_routine_log(endpoint: str, method: str) -> bool:
    """
    Bestäm om en routine API-anrop ska undertryckas från loggning

    Returns True om det är routine polling som inte behöver loggas
    """
    routine_endpoints = [
        "/api/market/ohlcv",
        "/api/market/orderbook",
        "/api/market/ticker",
        "/api/balances",
        "/api/positions",
        "/api/bot-status",
        "/api/orders/history",  # Order history is routine polling
        "/api/orders",  # GET orders is routine polling
    ]

    # GET requests to these endpoints are routine polling
    if method == "GET":
        return any(endpoint.startswith(ep) for ep in routine_endpoints)

    return False


def log_user_action_only(
    endpoint: str, method: str, message: str, details: Optional[Dict[str, Any]] = None
):
    """
    Logga endast om det INTE är routine polling

    Usage:
        log_user_action_only("/api/orders", "POST", "Order created", {...})
        log_user_action_only("/api/balances", "GET", "Balance fetched")
        # ^ Suppressed
    """
    if not should_suppress_routine_log(endpoint, method):
        event_type = EventType.TRADE_PLACED if method == "POST" else EventType.API_ERROR
        event_logger.log_event(event_type, message, details)
