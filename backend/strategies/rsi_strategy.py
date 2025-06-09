"""RSI trading strategy implementation."""

from typing import Any, Dict

import pandas as pd

from backend.strategies.indicators import rsi
from backend.strategies.sample_strategy import TradeSignal


class RSIStrategy:
    """RSI-based trading strategy with risk management."""

    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize RSI strategy with configuration.

        Args:
            config: Strategy configuration dictionary
        """
        self.config = config or {}
        self.rsi_period = self.config.get("rsi_period", 14)
        self.overbought = self.config.get("overbought", 70)
        self.oversold = self.config.get("oversold", 30)
        self.position_size = self.config.get("position_size", 0.1)  # 10% of portfolio

    def calculate_position_size(self, confidence: float) -> float:
        """
        Calculate position size based on signal confidence.

        Args:
            confidence: Signal confidence (0-1)

        Returns:
            float: Position size as fraction of portfolio
        """
        return self.position_size * confidence

    def run_strategy(self, data: pd.DataFrame) -> TradeSignal:
        """Kör RSI-strategin på indata och returnerar en TradeSignal."""
        rsi_values = rsi(data["close"], self.rsi_period)
        last_rsi = rsi_values.iloc[-1] if not rsi_values.empty else None
        if last_rsi is not None and last_rsi < self.oversold:
            return TradeSignal("buy", 1.0)
        elif last_rsi is not None and last_rsi > self.overbought:
            return TradeSignal("sell", 1.0)
        else:
            return TradeSignal("hold", 0.0)


def run_rsi_strategy(data: pd.DataFrame) -> TradeSignal:
    """Kör RSI-strategin via RSIStrategy-klassen."""
    strategy = RSIStrategy()
    return strategy.run_strategy(data)


def run_strategy(data: pd.DataFrame) -> TradeSignal:
    """Interface-funktion för strategi-tester. Anropar run_rsi_strategy."""
    return run_rsi_strategy(data)
