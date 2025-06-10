"""EMA crossover strategy stub implementation."""

import pandas as pd
from typing import Optional, Dict, Any
from backend.strategies.sample_strategy import TradeSignal
from backend.strategies.indicators import ema


def run_strategy(
    data: pd.DataFrame,
    fast_period: int = 9,
    slow_period: int = 21,
    min_gap: Optional[float] = None,
    direction: str = "both",
    lookback: int = 3
) -> Dict[str, Any]:
    """
    Kör EMA-crossover-strategi och returnerar signal, EMA-linjer och
    signalpunkter.

    Args:
        data (pd.DataFrame): DataFrame med minst kolumnen 'close'.
        fast_period (int): Period för snabb EMA.
        slow_period (int): Period för långsam EMA.
        min_gap (Optional[float]): Minsta skillnad mellan EMA:erna för signal.
        direction (str): "bullish", "bearish" eller "both" (default).
        lookback (int): Antal senaste punkter att leta crossover på (default 3).

    Returns:
        dict: {
            'result': TradeSignal,
            'ema_fast': list[float],
            'ema_slow': list[float],
            'signals': list[dict]  # [{index, type}]
        }
    """
    if 'close' not in data:
        raise ValueError(
            "Data måste innehålla kolumnen 'close'"
        )
    if fast_period >= slow_period:
        raise ValueError(
            "fast_period måste vara mindre än slow_period"
        )
    if len(data) < slow_period + 2:
        return {
            'result': TradeSignal(
                action="hold",
                confidence=0.0,
                position_size=0.0,
                metadata={}
            ),
            'ema_fast': [],
            'ema_slow': [],
            'signals': []
        }
    close = data['close']
    ema_fast = ema(close, fast_period)
    ema_slow = ema(close, slow_period)
    signals = []
    # Leta crossover i hela serien
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
    # Hitta senaste signal i lookback-fönstret
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
        position_size = 1.0
    else:
        action = "hold"
        confidence = 0.0
        position_size = 0.0
    result = TradeSignal(
        action=action,
        confidence=confidence,
        position_size=position_size,
        metadata={
            "ema_fast": float(ema_fast.iloc[-1]),
            "ema_slow": float(ema_slow.iloc[-1]),
            "signals": signals[-lookback:] if lookback > 0 else signals
        }
    )
    return {
        'result': result,
        'ema_fast': [float(x) for x in ema_fast],
        'ema_slow': [float(x) for x in ema_slow],
        'signals': signals
    }
