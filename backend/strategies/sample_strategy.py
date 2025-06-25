"""Trading strategy interface implementation."""

from typing import Any, Dict, NamedTuple, Optional

import pandas as pd
from backend.strategies.indicators import calculate_signal_probabilities


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


def run_strategy(data: pd.DataFrame, params: Optional[dict] = None) -> TradeSignal:
    """
    Exempelfunktion för strategi. Returnerar alltid 'hold' med confidence 0.5.
    Args:
        data (pd.DataFrame): Prisdata.
        params (dict): Parametrar (valfritt, används ej i denna dummy).
    Returns:
        TradeSignal: Signalobjekt med action, confidence, position_size och metadata.
    """
    if params is None:
        params = {}
    position_size = params.get("position_size", 1.0)
    # Dummy-värde och trösklar
    indicator_value = params.get("indicator_value", 0.0)
    buy_threshold = params.get("buy_threshold", 1.0)
    sell_threshold = params.get("sell_threshold", -1.0)
    prob_buy, prob_sell, prob_hold = calculate_signal_probabilities(
        indicator_value, buy_threshold, sell_threshold
    )
    return TradeSignal(
        action="hold",
        confidence=prob_hold,
        position_size=position_size,
        metadata={
            "info": "Sample strategy always holds",
            "indicator_value": indicator_value,
            "probability_buy": prob_buy,
            "probability_sell": prob_sell,
            "probability_hold": prob_hold,
        },
    )
