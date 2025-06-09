"""Risk management service for trading operations."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional


@dataclass
class RiskParameters:
    """Risk management parameters."""

    max_position_size: float  # Maximum position size as fraction of portfolio
    max_leverage: float  # Maximum allowed leverage
    stop_loss_pct: float  # Stop loss percentage
    take_profit_pct: float  # Take profit percentage
    max_daily_loss: float  # Maximum daily loss as fraction of portfolio
    max_open_positions: int  # Maximum number of open positions


class RiskManager:
    """Service for managing trading risk."""

    def __init__(self, risk_params: RiskParameters):
        """
        Initialize risk manager.

        Args:
            risk_params: Risk management parameters
        """
        self.params = risk_params
        self.daily_pnl = 0.0
        self.open_positions: Dict[str, Dict[str, Any]] = {}

    def validate_order(
        self,
        order_data: Dict[str, Any],
        portfolio_value: float,
        current_positions: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Validate order against risk parameters.

        Args:
            order_data: Order data dictionary
            portfolio_value: Current portfolio value
            current_positions: Current open positions

        Returns:
            Dict containing validation result and any errors

        Raises:
            ValueError: If order violates risk parameters
        """
        errors = []

        # Check position size
        position_value = float(order_data["amount"]) * float(order_data.get("price", 0))
        position_size_pct = position_value / portfolio_value

        if position_size_pct > self.params.max_position_size:
            errors.append(
                f"Position size {position_size_pct:.2%} exceeds maximum "
                f"{self.params.max_position_size:.2%}"
            )

        # Check leverage
        leverage = float(order_data.get("leverage", 1.0))
        if leverage > self.params.max_leverage:
            errors.append(
                f"Leverage {leverage}x exceeds maximum {self.params.max_leverage}x"
            )

        # Check number of open positions
        if len(current_positions) >= self.params.max_open_positions:
            errors.append(
                f"Maximum number of open positions ({self.params.max_open_positions}) "
                "exceeded"
            )

        # Check daily loss limit
        if self.daily_pnl < -self.params.max_daily_loss * portfolio_value:
            errors.append("Daily loss limit exceeded")

        return {"valid": len(errors) == 0, "errors": errors}

    def calculate_position_size(
        self,
        signal_confidence: float,
        portfolio_value: float,
        current_positions: Dict[str, Dict[str, Any]],
    ) -> float:
        """
        Calculate safe position size based on risk parameters.

        Args:
            signal_confidence: Strategy signal confidence (0-1)
            portfolio_value: Current portfolio value
            current_positions: Current open positions

        Returns:
            Safe position size in base currency
        """
        # Calculate available portfolio fraction
        used_capital = sum(
            pos["size"] * pos["entry_price"] for pos in current_positions.values()
        )
        available_capital = portfolio_value - used_capital

        # Calculate position size based on confidence and risk parameters
        max_position = available_capital * self.params.max_position_size
        position_size = max_position * signal_confidence

        return position_size

    def calculate_stop_loss(self, entry_price: float, side: str) -> float:
        """
        Calculate stop loss price.

        Args:
            entry_price: Position entry price
            side: 'buy' or 'sell'

        Returns:
            Stop loss price
        """
        if side == "buy":
            return entry_price * (1 - self.params.stop_loss_pct)
        else:
            return entry_price * (1 + self.params.stop_loss_pct)

    def calculate_take_profit(self, entry_price: float, side: str) -> float:
        """
        Calculate take profit price.

        Args:
            entry_price: Position entry price
            side: 'buy' or 'sell'

        Returns:
            Take profit price
        """
        if side == "buy":
            return entry_price * (1 + self.params.take_profit_pct)
        else:
            return entry_price * (1 - self.params.take_profit_pct)

    def update_daily_pnl(self, pnl: float):
        """
        Update daily profit/loss.

        Args:
            pnl: Profit/loss amount
        """
        self.daily_pnl += pnl

    def reset_daily_pnl(self):
        """Reset daily profit/loss at start of new day."""
        self.daily_pnl = 0.0
