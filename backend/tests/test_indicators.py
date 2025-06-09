"""Unit tests for indicator functions in backend/strategies/indicators.py."""

import pandas as pd
import pytest

from backend.strategies.indicators import ema


def test_ema_indicator_not_implemented():
    """EMA indicator should raise NotImplementedError in stub."""
    data = pd.Series([1.0, 2.0, 3.0, 4.0])
    with pytest.raises(NotImplementedError):
        ema(data, length=3)
