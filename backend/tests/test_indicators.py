"""Unit tests for indicator functions in backend/strategies/indicators.py."""

import pandas as pd
import pytest

from backend.strategies.indicators import ema, find_fvg_zones


def test_ema_simple_case():
    """Testar EMA mot känd output (jämför med pandas ewm direkt)."""
    data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
    length = 3
    expected = data.ewm(span=length, adjust=False).mean()
    result = ema(data, length=length)
    pd.testing.assert_series_equal(result, expected)


def test_ema_invalid_type():
    """Testar att TypeError kastas om input inte är en pd.Series."""
    with pytest.raises(TypeError):
        ema([1, 2, 3, 4], length=3)


def test_ema_invalid_length():
    """Testar att ValueError kastas om length <= 0."""
    data = pd.Series([1, 2, 3, 4], dtype=float)
    with pytest.raises(ValueError):
        ema(data, length=0)
    with pytest.raises(ValueError):
        ema(data, length=-5)


def test_find_fvg_zones_bullish_and_bearish():
    data = pd.DataFrame(
        {
            "open": [100, 110, 120, 130, 140],
            "high": [110, 120, 130, 140, 150],
            "low": [90, 100, 110, 120, 130],
            "close": [105, 115, 125, 135, 145],
        }
    )
    # Skapa en bullish FVG mellan index 0 och 2 (prev_high < next_low)
    data.loc[0, "high"] = 110
    data.loc[2, "low"] = 125  # next_low
    # Skapa en bearish FVG mellan index 1 och 3 (prev_low > next_high)
    data.loc[1, "low"] = 120
    data.loc[3, "high"] = 115  # next_high

    # Testa bullish
    bullish = find_fvg_zones(data, direction="bullish")
    assert any(z["direction"] == "bullish" for z in bullish)
    # Testa bearish
    bearish = find_fvg_zones(data, direction="bearish")
    assert any(z["direction"] == "bearish" for z in bearish)
    # Testa both
    both = find_fvg_zones(data, direction="both")
    assert any(z["direction"] == "bullish" for z in both)
    assert any(z["direction"] == "bearish" for z in both)


def test_find_fvg_zones_min_gap_size():
    data = pd.DataFrame(
        {
            "open": [100, 110, 120],
            "high": [110, 120, 130],
            "low": [90, 100, 120],
            "close": [105, 115, 125],
        }
    )
    # Skapa en bullish FVG med gap 10
    data.loc[0, "high"] = 110
    data.loc[2, "low"] = 120  # next_low
    # min_gap_size större än gapet
    result = find_fvg_zones(data, min_gap_size=15)
    assert len(result) == 0
    # min_gap_size mindre än gapet
    result = find_fvg_zones(data, min_gap_size=5)
    assert len(result) > 0


def test_find_fvg_zones_no_gaps():
    data = pd.DataFrame(
        {
            "open": [100, 110, 120],
            "high": [110, 120, 130],
            "low": [90, 100, 110],
            "close": [105, 115, 125],
        }
    )
    # Inga FVG ska hittas
    result = find_fvg_zones(data)
    assert result == []
