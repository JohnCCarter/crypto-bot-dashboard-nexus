"""Unit tests for trading strategy interface implementations."""

import importlib
import os

import pandas as pd
import pytest

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
    df = pd.DataFrame({"close": [1.0, 2.0, 3.0, 2.5, 2.8]})
    signal = module.run_strategy(df)
    assert isinstance(signal, module.TradeSignal)
    assert hasattr(signal, "action") and hasattr(signal, "confidence")
    assert signal.action in ("buy", "sell", "hold")
    assert isinstance(signal.confidence, float)
    assert 0.0 <= signal.confidence <= 1.0
