"""Stateless pure functions for trading indicators."""

import pandas as pd


def ema(data: pd.Series, length: int) -> pd.Series:
    """
    Exponential moving average (EMA).

    :param data: Series of price values.
    :param length: EMA window length.
    :return: Series of EMA values.
    """
    raise NotImplementedError("EMA indicator not implemented")


def rsi(data: pd.Series, period: int) -> pd.Series:
    """
    Relative Strength Index (RSI).

    :param data: Series of price values.
    :param period: RSI period length.
    :return: Series of RSI values.
    """
    raise NotImplementedError("RSI indicator not implemented")