"""Stateless pure functions for trading indicators."""

import pandas as pd


def ema(series: pd.Series, length: int) -> pd.Series:
    """
    Beräknar Exponential Moving Average (EMA) för en pandas Series.

    Args:
        series (pd.Series): Prisdata eller annan numerisk serie
        length (int): Periodlängd för EMA

    Returns:
        pd.Series: EMA-värden
    """
    if not isinstance(series, pd.Series):
        raise TypeError("series måste vara en pandas Series")
    if length <= 0:
        raise ValueError("length måste vara > 0")
    return series.ewm(span=length, adjust=False).mean()


def rsi(series, length=None, period=None):
    """Beräknar Relative Strength Index (RSI) för en pandas Series.
    Args:
        series (pd.Series): Prisdata (t.ex. stängningspriser)
        length (int, optional): Periodlängd för RSI (default 14)
        period (int, optional): Alternativt namn för periodlängd
    Returns:
        pd.Series: RSI-värden
    """
    n = length if length is not None else period if period is not None else 14
    delta = series.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)
    avg_gain = gain.rolling(window=n, min_periods=n).mean()
    avg_loss = loss.rolling(window=n, min_periods=n).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi = rsi.fillna(0)
    return rsi


def macd(
    data: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    Calculate Moving Average Convergence Divergence (MACD).

    Args:
        data (pd.Series): Price data series
        fast_period (int): Fast EMA period
        slow_period (int): Slow EMA period
        signal_period (int): Signal line period

    Returns:
        tuple: (MACD line, Signal line, Histogram)

    Example:
        >>> prices = pd.Series([10, 11, 12, 13, 14])
        >>> macd_line, signal_line, histogram = macd(prices)
    """
    fast_ema = ema(data, fast_period)
    slow_ema = ema(data, slow_period)
    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def find_fvg_zones(
    data: pd.DataFrame, min_gap_size: float = 0.0, direction: str = "both"
) -> list[dict]:
    """
    Identifierar Fair Value Gap (FVG) zoner i OHLCV-data (klassisk 3-candle gap).

    Args:
        data (pd.DataFrame): DataFrame med kolumnerna ['open', 'high', 'low', 'close']
        min_gap_size (float): Minsta gap-storlek (absolut, i pris) för att inkluderas
        direction (str): "bullish", "bearish" eller "both" (default)

    Returns:
        list[dict]: Lista av FVG-zoner med index, gap-storlek och riktning

    Exempel på output:
        [
            {"index": 10, "gap_high": 25000, "gap_low": 24900, "size": 100,
             "direction": "bullish"},
            ...
        ]
    """
    fvg_zones = []
    for i in range(1, len(data) - 1):
        prev_low = data["low"].iloc[i - 1]
        prev_high = data["high"].iloc[i - 1]
        next_high = data["high"].iloc[i + 1]
        next_low = data["low"].iloc[i + 1]

        # Bullish FVG: prev_high < next_low (gap up)
        if direction in ("bullish", "both"):
            if prev_high < next_low:
                gap_size = next_low - prev_high
                if gap_size >= min_gap_size:
                    fvg_zones.append(
                        {
                            "index": i,
                            "gap_high": next_low,
                            "gap_low": prev_high,
                            "size": gap_size,
                            "direction": "bullish",
                        }
                    )
        # Bearish FVG: prev_low > next_high (gap down)
        if direction in ("bearish", "both"):
            if prev_low > next_high:
                gap_size = prev_low - next_high
                if gap_size >= min_gap_size:
                    fvg_zones.append(
                        {
                            "index": i,
                            "gap_high": prev_low,
                            "gap_low": next_high,
                            "size": gap_size,
                            "direction": "bearish",
                        }
                    )
    return fvg_zones


def calculate_signal_probabilities(
    indicator_value: float, buy_threshold: float, sell_threshold: float
) -> tuple[float, float, float]:
    """
    Beräknar sannolikheter för buy, sell och hold baserat på indikatorvärde och trösklar.
    Args:
        indicator_value (float): Värde från indikator (t.ex. RSI, EMA-diff).
        buy_threshold (float): Tröskel för köp.
        sell_threshold (float): Tröskel för sälj.
    Returns:
        tuple: (probability_buy, probability_sell, probability_hold)
    """
    if indicator_value >= buy_threshold:
        prob_buy = 0.7
        prob_sell = 0.1
        prob_hold = 0.2
    elif indicator_value <= sell_threshold:
        prob_buy = 0.1
        prob_sell = 0.7
        prob_hold = 0.2
    else:
        prob_buy = 0.2
        prob_sell = 0.2
        prob_hold = 0.6
    return prob_buy, prob_sell, prob_hold
