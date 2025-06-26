"""RSI trading strategy implementation."""

from typing import Any, Dict

import pandas as pd

from backend.strategies.indicators import calculate_signal_probabilities, rsi
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


def run_strategy(data: pd.DataFrame, params: Dict[str, Any]) -> TradeSignal:
    """
    Kör RSI-strategin med parametrar från config.

    Args:
        data (pd.DataFrame): DataFrame med minst kolumnen 'close'.
        params (dict): Parametrar från config, t.ex. {
            'rsi_period': 14,
            'overbought': 70,
            'oversold': 30,
            'position_size': 0.1,
            'symbol': 'BTC/USD',
            'timeframe': '1h',
            ...
        }

    Returns:
        TradeSignal: Signalobjekt med action, confidence, position_size och metadata.
    """
    rsi_period = params.get("rsi_period", 14)
    overbought = params.get("overbought", 70)
    oversold = params.get("oversold", 30)
    position_size = params.get("position_size", 1.0)
    symbol = params.get("symbol", None)
    timeframe = params.get("timeframe", None)
    if "close" not in data:
        raise ValueError("Data måste innehålla kolumnen 'close'")
    rsi_series = rsi(data["close"], length=rsi_period)
    rsi_value = float(rsi_series.iloc[-1])
    prob_buy, prob_sell, prob_hold = calculate_signal_probabilities(
        rsi_value, overbought, oversold
    )
    if rsi_value >= overbought:
        action = "sell"
        confidence = prob_sell
    elif rsi_value <= oversold:
        action = "buy"
        confidence = prob_buy
    else:
        action = "hold"
        confidence = prob_hold
    return TradeSignal(
        action=action,
        confidence=confidence,
        position_size=position_size,
        metadata={
            "rsi": rsi_value,
            "probability_buy": prob_buy,
            "probability_sell": prob_sell,
            "probability_hold": prob_hold,
            "symbol": symbol,
            "timeframe": timeframe,
        },
    )
