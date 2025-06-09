"""Trading strategy interface implementation."""

from typing import Any, Dict, NamedTuple, Optional

import pandas as pd


class TradeSignal(NamedTuple):
    """
    Represents a trading signal result.

    Attributes:
        action: 'buy', 'sell', or 'hold'
        confidence: Confidence level between 0.0 and 1.0
        position_size: Size of position as fraction of portfolio (0.0-1.0)
        metadata: Additional strategy-specific data
    """

    action: str
    confidence: float
    position_size: float = 0.0
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        """Validate signal attributes."""
        if self.action not in ["buy", "sell", "hold"]:
            raise ValueError("Action must be 'buy', 'sell', or 'hold'")
        if not 0 <= self.confidence <= 1:
            raise ValueError("Confidence must be between 0 and 1")
        if not 0 <= self.position_size <= 1:
            raise ValueError("Position size must be between 0 and 1")


def run_strategy(data: pd.DataFrame) -> TradeSignal:
    """
    Run the trading strategy logic on input price DataFrame.

    Args:
        data: Historical price/time data as pandas DataFrame

    Returns:
        TradeSignal: Trading signal with action and confidence
    """
    # This is now just a base class - use specific strategy implementations
    return TradeSignal(action="hold", confidence=0.0)
