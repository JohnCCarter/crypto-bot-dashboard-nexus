"""Unit tests for indicator functions in backend/strategies/indicators.py."""

import pandas as pd
import pytest

from backend.strategies.indicators import ema, rsi


def test_ema_indicator_not_implemented():
    """EMA indicator should raise NotImplementedError in stub."""
    data = pd.Series([1.0, 2.0, 3.0, 4.0])
    with pytest.raises(NotImplementedError):
        ema(data, length=3)


def test_rsi_indicator_not_implemented():
    """RSI indicator should raise NotImplementedError in stub."""
    data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
    with pytest.raises(NotImplementedError):
        rsi(data, period=14)