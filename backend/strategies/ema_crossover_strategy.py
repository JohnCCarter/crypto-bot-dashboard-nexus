"""EMA crossover strategy stub implementation."""

from typing import Any, Dict
import pandas as pd
from backend.strategies.indicators import ema
from backend.strategies.sample_strategy import TradeSignal


def run_strategy(data: pd.DataFrame, params: Dict[str, Any]) -> TradeSignal:
    """
    Kör EMA-crossover-strategi med parametrar från config.

    Args:
        data (pd.DataFrame): DataFrame med minst kolumnen 'close'.
        params (dict): Parametrar från config, t.ex. {
            'fast_period': 12,
            'slow_period': 26,
            'min_gap': 0.5,
            'direction': 'both',
            'lookback': 3,
            'symbol': 'BTC/USD',
            'timeframe': '1h',
            ...
        }

    Returns:
        TradeSignal: Signalobjekt med action, confidence, position_size och
        metadata.
    """
    fast_period = params.get('ema_fast') or params.get('fast_period')
    slow_period = params.get('ema_slow') or params.get('slow_period')
    min_gap = params.get('min_gap')
    direction = params.get('direction', 'both')
    lookback = params.get('lookback', 3)
    if 'close' not in data:
        raise ValueError(
            "Data måste innehålla kolumnen 'close'"
        )
    if fast_period is None or slow_period is None:
        raise ValueError(
            "Både fast_period och slow_period måste anges i config"
        )
    if fast_period >= slow_period:
        raise ValueError("fast_period måste vara mindre än slow_period")
    if len(data) < slow_period + 2:
        return TradeSignal(
            action="hold",
            confidence=0.0,
            position_size=0.0,
            metadata={
                'ema_fast': [],
                'ema_slow': [],
                'signals': []
            }
        )
    close = data['close']
    ema_fast = ema(close, fast_period)
    ema_slow = ema(close, slow_period)
    signals = []
    for i in range(1, len(data)):
        prev_fast = float(ema_fast.iloc[i-1])
        prev_slow = float(ema_slow.iloc[i-1])
        curr_fast = float(ema_fast.iloc[i])
        curr_slow = float(ema_slow.iloc[i])
        gap = abs(curr_fast - curr_slow)
        if min_gap is not None and gap < min_gap:
            continue
        bullish = prev_fast <= prev_slow and curr_fast > curr_slow
        bearish = prev_fast >= prev_slow and curr_fast < curr_slow
        if bullish and direction in ("both", "bullish"):
            signals.append({"index": int(i), "type": "buy"})
        elif bearish and direction in ("both", "bearish"):
            signals.append({"index": int(i), "type": "sell"})
    last_signal = None
    for s in reversed(signals):
        if s["index"] >= len(data) - lookback:
            last_signal = s
            break
    if last_signal:
        action = str(last_signal["type"])
        confidence = min(
            1.0,
            abs(float(ema_fast.iloc[-1]) - float(ema_slow.iloc[-1])) /
            (abs(float(ema_slow.iloc[-1])) + 1e-9)
        )
        position_size = params.get('position_size', 1.0)
    else:
        action = "hold"
        confidence = 0.0
        position_size = 0.0
    return TradeSignal(
        action=action,
        confidence=confidence,
        position_size=position_size,
        metadata={
            "ema_fast": float(ema_fast.iloc[-1]),
            "ema_slow": float(ema_slow.iloc[-1]),
            "ema_fast_series": [float(x) for x in ema_fast],
            "ema_slow_series": [float(x) for x in ema_slow],
            "signals": signals[-lookback:] if lookback > 0 else signals,
            "symbol": params.get('symbol'),
            "timeframe": params.get('timeframe')
        }
    )
