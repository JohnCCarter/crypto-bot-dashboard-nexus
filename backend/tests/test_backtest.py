"""Unit tests for backtesting functionality."""

from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from backend.services.backtest import BacktestEngine, BacktestResult
from backend.strategies.sample_strategy import TradeSignal, run_strategy


@pytest.fixture
def sample_data():
    """Create sample price data for testing med tydlig variation och trend."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="1H")
    base = 100
    amplitude = 10
    trend = np.linspace(-5, 5, 100)
    noise = np.random.normal(0, 0.5, 100)
    close = base + amplitude * np.sin(np.linspace(0, 6 * np.pi, 100)) + trend + noise
    data = pd.DataFrame(
        {
            "open": close + np.random.normal(0, 0.2, 100),
            "high": close + np.random.normal(0.5, 0.2, 100),
            "low": close - np.random.normal(0.5, 0.2, 100),
            "close": close,
            "volume": np.random.normal(1000, 100, 100),
        },
        index=dates,
    )
    return data


@pytest.fixture
def backtest_engine():
    """Create a backtest engine instance."""
    return BacktestEngine(initial_capital=10000.0, commission=0.001, slippage=0.0005)


def test_backtest_engine_initialization():
    """Test backtest engine initialization."""
    engine = BacktestEngine()
    assert engine.initial_capital == 10000.0
    assert engine.commission == 0.001
    assert engine.slippage == 0.0005


def test_run_backtest(backtest_engine, sample_data):
    """Test running a backtest."""
    result = backtest_engine.run_backtest(sample_data, run_strategy)

    assert isinstance(result, BacktestResult)
    assert result.total_trades >= 0
    assert result.winning_trades >= 0
    assert result.losing_trades >= 0
    assert 0 <= result.win_rate <= 1
    assert isinstance(result.total_pnl, float)
    assert isinstance(result.max_drawdown, float)
    assert isinstance(result.sharpe_ratio, float)
    assert isinstance(result.trade_history, list)
    assert isinstance(result.equity_curve, pd.Series)


def test_optimize_parameters(backtest_engine, sample_data):
    """Test parameter optimization."""
    param_grid = {"rsi_period": [14, 21], "overbought": [70, 80], "oversold": [20, 30]}

    result = backtest_engine.optimize_parameters(sample_data, run_strategy, param_grid)

    assert isinstance(result, dict)
    assert "parameters" in result
    assert "performance" in result
    assert isinstance(result["performance"], dict)
    assert "sharpe_ratio" in result["performance"]


def always_trade_strategy(data):
    """Teststrategi som alltid genererar en trade (köp)."""
    from backend.strategies.sample_strategy import TradeSignal

    return TradeSignal(action="buy", confidence=1.0, position_size=1.0, metadata={})


def test_risk_parameters(backtest_engine, sample_data):
    """Test backtest med custom risk parameters och strategi som alltid handlar."""
    risk_params = {
        "max_position_size": 0.2,
        "stop_loss_pct": 0.03,
        "take_profit_pct": 0.06,
    }

    result = backtest_engine.run_backtest(
        sample_data, always_trade_strategy, risk_params
    )

    assert isinstance(result, BacktestResult)
    # Nu ska det alltid finnas trades
    assert len(result.trade_history) > 0


def test_edge_cases(backtest_engine):
    """Test backtest with edge cases."""
    # Empty data
    empty_data = pd.DataFrame()
    with pytest.raises(ValueError):
        backtest_engine.run_backtest(empty_data, run_strategy)

    # Single row data
    single_row = pd.DataFrame(
        {"open": [100], "high": [101], "low": [99], "close": [100], "volume": [1000]},
        index=[datetime.now()],
    )
    with pytest.raises(ValueError):
        backtest_engine.run_backtest(single_row, run_strategy)
