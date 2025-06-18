"""FVG (Fair Value Gap) trading strategy implementation."""

from typing import Any, Dict, Optional
import pandas as pd
from backend.strategies.indicators import find_fvg_zones
from backend.strategies.sample_strategy import TradeSignal


class FVGStrategy:
    """Strategi baserad på Fair Value Gap-zoner."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initiera FVG-strategi med konfiguration.
        Args:
            config: Strategikonfiguration (dict)
        """
        self.config = config or {}
        self.min_gap_size = self.config.get("min_gap_size", 0.0)
        self.direction = self.config.get("direction", "both")
        self.position_size = self.config.get("position_size", 0.1)
        self.lookback = self.config.get("lookback", 5)

    def calculate_position_size(self, confidence: float) -> float:
        """
        Beräkna positionsstorlek baserat på signalens styrka.
        """
        return self.position_size * confidence

    def run_strategy(self, data: pd.DataFrame) -> TradeSignal:
        """
        Kör FVG-strategin på indata och returnerar en TradeSignal.
        """
        fvg_zones = find_fvg_zones(
            data,
            min_gap_size=self.min_gap_size,
            direction=self.direction
        )
        # Kontrollera om senaste priset återbesöker en FVG-zon
        last_close = data['close'].iloc[-1]
        recent_fvg = [
            z for z in fvg_zones
            if z['index'] >= len(data) - self.lookback - 1
        ]
        for zone in recent_fvg:
            if zone['gap_low'] <= last_close <= zone['gap_high']:
                action = "buy" if zone['direction'] == "bullish" else "sell"
                return TradeSignal(
                    action=action,
                    confidence=1.0,
                    position_size=self.position_size,
                    metadata={"fvg_zone": zone}
                )
        return TradeSignal(action="hold", confidence=0.0)


def run_fvg_strategy(data: pd.DataFrame) -> TradeSignal:
    """Kör FVG-strategin via FVGStrategy-klassen."""
    strategy = FVGStrategy()
    return strategy.run_strategy(data)


def run_strategy(data: pd.DataFrame, params: dict) -> TradeSignal:
    """
    Kör FVG-strategin och returnerar TradeSignal med sannolikheter för buy, sell, hold.
    Args:
        data (pd.DataFrame): Prisdata med open, high, low, close.
        params (dict): Parametrar, t.ex. direction ('buy', 'sell', 'both'), lookback.
    Returns:
        TradeSignal: Signalobjekt med action, confidence, position_size och metadata.
    """
    lookback = params.get('lookback', 3)
    position_size = params.get('position_size', 1.0)
    # Dummy FVG-logik: Om close[-1] > open[-lookback] => buy, annars sell, annars hold
    if len(data) < lookback:
        return TradeSignal(
            action="hold",
            confidence=0.0,
            position_size=position_size,
            metadata={
                "probability_buy": 0.33,
                "probability_sell": 0.33,
                "probability_hold": 0.34
            }
        )
    if data['close'].iloc[-1] > data['open'].iloc[-lookback]:
        action = "buy"
        prob_buy = 0.7
        prob_sell = 0.1
        prob_hold = 0.2
    elif data['close'].iloc[-1] < data['open'].iloc[-lookback]:
        action = "sell"
        prob_buy = 0.1
        prob_sell = 0.7
        prob_hold = 0.2
    else:
        action = "hold"
        prob_buy = 0.2
        prob_sell = 0.2
        prob_hold = 0.6
    return TradeSignal(
        action=action,
        confidence=max(
            prob_buy, prob_sell
        ),
        position_size=position_size,
        metadata={
            "probability_buy": prob_buy,
            "probability_sell": prob_sell,
            "probability_hold": prob_hold
        }
    )


def run_strategy_with_params(data: pd.DataFrame, params: dict) -> TradeSignal:
    """Wrapper för optimerings-API: kör FVG-strategi med parametrar."""
    strategy = FVGStrategy(params)
    return strategy.run_strategy(data) 