"""Stateless pure functions for trading indicators."""

import numpy as np
import pandas as pd


def ema(series, length):
    """Stub för EMA-indikator. Ska kasta NotImplementedError enligt test."""
    raise NotImplementedError("EMA-indikatorn är inte implementerad.")


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
