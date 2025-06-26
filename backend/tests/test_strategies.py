"""Unit tests for trading strategy interface implementations."""

import importlib
import os

import pandas as pd
import pytest

from backend.strategies import ema_crossover_strategy
from backend.strategies.fvg_strategy import FVGStrategy

STRATEGY_DIR = os.path.join(os.path.dirname(__file__), "..", "strategies")
STRATEGY_MODULES = [
    f[:-3]
    for f in os.listdir(STRATEGY_DIR)
    if f.endswith("_strategy.py") and not f.startswith("__")
]


@pytest.mark.parametrize("mod_name", STRATEGY_MODULES)
def test_run_strategy_interface(mod_name):
    """Each strategy must implement run_strategy and return a valid TradeSignal."""
    module = importlib.import_module(f"backend.strategies.{mod_name}")
    assert hasattr(module, "run_strategy"), f"{mod_name} missing run_strategy"
    assert hasattr(module, "TradeSignal"), f"{mod_name} missing TradeSignal"
    if mod_name == "fvg_strategy":
        df = pd.DataFrame(
            {
                "open": [1.0, 2.0, 3.0, 2.5, 2.8],
                "high": [1.2, 2.2, 3.2, 2.7, 2.9],
                "low": [0.8, 1.8, 2.8, 2.3, 2.6],
                "close": [1.0, 2.0, 3.0, 2.5, 2.8],
            }
        )
        params = {"direction": "both", "lookback": 3}
    elif mod_name == "ema_crossover_strategy":
        df = pd.DataFrame({"close": [1.0, 2.0, 3.0, 2.5, 2.8]})
        params = {"fast_period": 3, "slow_period": 5}
    else:
        df = pd.DataFrame({"close": [1.0, 2.0, 3.0, 2.5, 2.8]})
        params = {}
    signal = module.run_strategy(df, params)
    assert isinstance(signal, module.TradeSignal)
    assert hasattr(signal, "action") and hasattr(signal, "confidence")
    assert signal.action in ("buy", "sell", "hold")
    assert isinstance(signal.confidence, float)
    assert 0.0 <= signal.confidence <= 1.0


def test_fvg_strategy_buy_signal():
    data = pd.DataFrame(
        {
            "open": [100, 110, 120, 130, 140],
            "high": [110, 120, 130, 140, 150],
            "low": [90, 100, 110, 120, 130],
            "close": [105, 115, 125, 135, 125],  # Sista close återbesöker bullish FVG
        }
    )
    # Skapa bullish FVG
    data.loc[0, "high"] = 110
    data.loc[2, "low"] = 125
    strategy = FVGStrategy({"direction": "bullish", "lookback": 5})
    signal = strategy.run_strategy(data)
    assert signal.action == "buy"
    assert signal.confidence == 1.0


def test_fvg_strategy_sell_signal():
    data = pd.DataFrame(
        {
            "open": [100, 110, 120, 130, 140],
            "high": [110, 120, 115, 140, 150],
            "low": [90, 120, 110, 120, 130],
            "close": [105, 125, 115, 135, 120],  # Sista close återbesöker bearish FVG
        }
    )
    # Skapa bearish FVG
    data.loc[1, "low"] = 120
    data.loc[3, "high"] = 115
    strategy = FVGStrategy({"direction": "bearish", "lookback": 5})
    signal = strategy.run_strategy(data)
    assert signal.action == "sell"
    assert signal.confidence == 1.0


def test_fvg_strategy_hold_signal():
    data = pd.DataFrame(
        {
            "open": [100, 110, 120, 130, 140],
            "high": [110, 120, 130, 140, 150],
            "low": [90, 100, 110, 120, 130],
            "close": [105, 115, 125, 135, 145],  # Ingen återbesök av FVG
        }
    )
    strategy = FVGStrategy({"direction": "both", "lookback": 5})
    signal = strategy.run_strategy(data)
    assert signal.action == "hold"
    assert signal.confidence == 0.0


def test_fvg_strategy_min_gap_size():
    data = pd.DataFrame(
        {
            "open": [100, 110, 120],
            "high": [110, 120, 130],
            "low": [90, 100, 120],
            "close": [105, 115, 120],
        }
    )
    data.loc[0, "high"] = 110
    data.loc[2, "low"] = 120
    # min_gap_size större än gapet
    strategy = FVGStrategy({"min_gap_size": 15})
    signal = strategy.run_strategy(data)
    assert signal.action == "hold"


def test_ema_crossover_bullish():
    # Skapa data där snabb EMA korsar upp över långsam EMA mellan sista punkterna
    data = pd.DataFrame({"close": [1] * 10 + [16] * 5})
    params = {"fast_period": 3, "slow_period": 5, "lookback": 5}
    signal = ema_crossover_strategy.run_strategy(data, params)
    assert signal.action == "buy"
    assert 0.0 < signal.confidence <= 1.0


def test_ema_crossover_bearish():
    # Skapa data där snabb EMA korsar ner under långsam EMA mellan sista punkterna
    data = pd.DataFrame({"close": [16] * 10 + [1] * 5})
    params = {"fast_period": 3, "slow_period": 5, "lookback": 5}
    signal = ema_crossover_strategy.run_strategy(data, params)
    assert signal.action == "sell"
    assert 0.0 < signal.confidence <= 1.0


def test_ema_crossover_hold():
    # Skapa data där ingen crossover sker
    data = pd.DataFrame({"close": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]})
    params = {"fast_period": 3, "slow_period": 5}
    signal = ema_crossover_strategy.run_strategy(data, params)
    assert signal.action == "hold"
    assert signal.confidence == 0.0


def test_ema_crossover_too_little_data():
    # För kort serie för att avgöra crossover
    data = pd.DataFrame({"close": [1, 2, 3, 4]})
    params = {"fast_period": 2, "slow_period": 3}
    signal = ema_crossover_strategy.run_strategy(data, params)
    assert signal.action == "hold"


def test_ema_crossover_invalid_params():
    data = pd.DataFrame({"close": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
    with pytest.raises(ValueError):
        params = {"fast_period": 5, "slow_period": 3}
        ema_crossover_strategy.run_strategy(data, params)
    with pytest.raises(ValueError):
        params = {"fast_period": 3, "slow_period": 3}
        ema_crossover_strategy.run_strategy(data, params)


def test_ema_crossover_min_gap():
    # Skapa crossover men med litet gap
    data = pd.DataFrame({"close": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]})
    params = {"fast_period": 3, "slow_period": 5, "min_gap": 100}
    signal = ema_crossover_strategy.run_strategy(data, params)
    assert signal.action == "hold"


def test_ema_crossover_direction_filter():
    # Data med bullish crossover
    data = pd.DataFrame({"close": [1] * 10 + [16] * 5})
    params = {"fast_period": 3, "slow_period": 5, "direction": "bullish", "lookback": 5}
    signal = ema_crossover_strategy.run_strategy(data, params)
    assert signal.action == "buy"
    # Endast bearish tillåts
    data = pd.DataFrame({"close": [16] * 10 + [1] * 5})
    params = {"fast_period": 3, "slow_period": 5, "direction": "bearish", "lookback": 5}
    signal = ema_crossover_strategy.run_strategy(data, params)
    assert signal.action == "sell"
