"""Integration tests for backtesting API endpoints."""

import json

import pandas as pd
import pytest

from backend.app import app


@pytest.fixture
def client():
    """Create a test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_data():
    """Create sample price data for testing."""
    dates = pd.date_range(start="2024-01-01", periods=100, freq="1h")
    data = {
        "timestamp": dates.strftime("%Y-%m-%d %H:%M:%S").tolist(),
        "open": [100.0] * 100,
        "high": [101.0] * 100,
        "low": [99.0] * 100,
        "close": [100.0] * 100,
        "volume": [1000.0] * 100,
    }
    return data


def test_run_backtest_endpoint(client, sample_data):
    """Test the run backtest endpoint."""
    # Test with valid data
    response = client.post(
        "/api/backtest/run",
        json={
            "strategy": "sample",
            "data": sample_data,
            "parameters": {
                "initial_capital": 10000.0,
                "commission": 0.001,
                "slippage": 0.0005,
            },
        },
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "total_trades" in data
    assert "win_rate" in data
    assert "total_pnl" in data

    # Test with invalid strategy
    response = client.post(
        "/api/backtest/run", json={"strategy": "invalid", "data": sample_data}
    )
    assert response.status_code == 400

    # Test with missing data
    response = client.post("/api/backtest/run", json={"strategy": "sample"})
    assert response.status_code == 400


def test_optimize_parameters_endpoint(client, sample_data):
    """Test the optimize parameters endpoint."""
    # Test with valid data
    response = client.post(
        "/api/backtest/optimize",
        json={
            "strategy": "sample",
            "data": sample_data,
            "param_grid": {
                "rsi_period": [14, 21],
                "overbought": [70, 80],
                "oversold": [20, 30],
            },
        },
    )

    assert response.status_code == 200
    data = json.loads(response.data)
    assert "parameters" in data
    assert "performance" in data

    # Test with invalid strategy
    response = client.post(
        "/api/backtest/optimize",
        json={"strategy": "invalid", "data": sample_data, "param_grid": {}},
    )
    assert response.status_code == 400

    # Test with missing data
    response = client.post("/api/backtest/optimize", json={"strategy": "sample"})
    assert response.status_code == 400


def test_optimize_fvg_strategy(client, sample_data):
    """Testa optimering av FVG-strategin via API."""
    response = client.post(
        "/api/backtest/optimize",
        json={
            "strategy": "fvg",
            "data": sample_data,
            "param_grid": {
                "min_gap_size": [5, 10],
                "direction": ["bullish", "bearish"],
                "position_size": [0.05, 0.1],
                "lookback": [3, 5],
            },
        },
    )
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "parameters" in data
    assert "performance" in data


def test_error_handling(client):
    """Test error handling in endpoints."""
    # Test with invalid JSON
    response = client.post("/api/backtest/run", data="invalid json")
    assert response.status_code == 400

    # Test with empty data
    response = client.post(
        "/api/backtest/run",
        json={
            "strategy": "sample",
            "data": {
                "timestamp": [],
                "open": [],
                "high": [],
                "low": [],
                "close": [],
                "volume": [],
            },
        },
    )
    assert response.status_code == 400
