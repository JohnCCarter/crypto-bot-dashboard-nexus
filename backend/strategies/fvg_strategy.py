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


def run_strategy(data: pd.DataFrame, params: Dict[str, Any]) -> TradeSignal:
    """
    Kör FVG-strategin med parametrar från config.

    Args:
        data (pd.DataFrame): DataFrame med minst kolumnen 'close'.
        params (dict): Parametrar från config, t.ex. {
            'min_gap_size': 10,
            'direction': 'both',
            'position_size': 0.1,
            'lookback': 5,
            'symbol': 'BTC/USD',
            'timeframe': '1h',
            ...
        }

    Returns:
        TradeSignal: Signalobjekt med action, confidence, position_size och metadata.
    """
    min_gap_size = params.get('min_gap_size', 0.0)
    direction = params.get('direction', 'both')
    position_size = params.get('position_size', 0.1)
    lookback = params.get('lookback', 5)
    if 'close' not in data:
        raise ValueError("Data måste innehålla kolumnen 'close'")
    fvg_zones = find_fvg_zones(
        data,
        min_gap_size=min_gap_size,
        direction=direction
    )
    last_close = data['close'].iloc[-1]
    recent_fvg = [
        z for z in fvg_zones
        if z['index'] >= len(data) - lookback - 1
    ]
    for zone in recent_fvg:
        if zone['gap_low'] <= last_close <= zone['gap_high']:
            action = "buy" if zone['direction'] == "bullish" else "sell"
            return TradeSignal(
                action=action,
                confidence=1.0,
                position_size=position_size,
                metadata={"fvg_zone": zone, "symbol": params.get('symbol'), "timeframe": params.get('timeframe')}
            )
    return TradeSignal(action="hold", confidence=0.0, position_size=0.0, metadata={"symbol": params.get('symbol'), "timeframe": params.get('timeframe')})


def run_strategy_with_params(data: pd.DataFrame, params: dict) -> TradeSignal:
    """Wrapper för optimerings-API: kör FVG-strategi med parametrar."""
    strategy = FVGStrategy(params)
    return strategy.run_strategy(data) 