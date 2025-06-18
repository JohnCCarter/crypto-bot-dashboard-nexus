"""Backtesting API endpoints."""

from typing import Any, Dict

import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request

from backend.services.backtest import BacktestEngine
from backend.services.monitor import AlertLevel, Monitor
from backend.strategies.rsi_strategy import run_rsi_strategy
from backend.strategies.sample_strategy import run_strategy
from backend.strategies.fvg_strategy import run_strategy_with_params
from backend.strategies.ema_crossover_strategy import run_strategy as run_ema_crossover_strategy

# Create blueprint
backtest_bp = Blueprint("backtest", __name__)

# Initialize services
backtest_engine = BacktestEngine()
monitor = Monitor()

def run_ema_crossover_with_params(data, params):
    result = run_ema_crossover_strategy(
        data,
        fast_period=params.get("fast_period", 9),
        slow_period=params.get("slow_period", 21),
        min_gap=params.get("min_gap"),
        direction=params.get("direction", "both"),
        lookback=params.get("lookback", 3),
    )
    # result är nu ett dict med 'result', 'ema_fast', 'ema_slow', 'signals'
    return result

# Strategy mapping
STRATEGIES = {
    "sample": run_strategy,
    "rsi": run_rsi_strategy,
    "fvg": run_strategy_with_params,
    "ema_crossover": run_ema_crossover_with_params,
}


@backtest_bp.route("/api/backtest/run", methods=["POST"])
def run_backtest():
    """
    Run backtest for a trading strategy.

    Request body:
    {
        "strategy": "strategy_name",
        "data": {
            "timestamp": [...],
            "open": [...],
            "high": [...],
            "low": [...],
            "close": [...],
            "volume": [...]
        },
        "parameters": {
            "initial_capital": float,
            "commission": float,
            "slippage": float,
            "risk_params": {
                "max_position_size": float,
                "stop_loss_pct": float,
                "take_profit_pct": float
            }
        }
    }
    """
    try:
        # Get request data
        if not request.is_json:
            print("❌ DEBUG: Content-Type is not application/json")
            return jsonify({"error": "Content-Type must be application/json"}), 400
        try:
            data = request.get_json()
            print(f"🔍 DEBUG: Received data keys: {list(data.keys()) if data else 'None'}")
            if data and 'data' in data:
                print(f"🔍 DEBUG: Data sub-keys: {list(data['data'].keys()) if data['data'] else 'None'}")
                if data['data'] and 'timestamp' in data['data']:
                    print(f"🔍 DEBUG: Timestamp count: {len(data['data']['timestamp'])}")
        except Exception as e:
            print(f"❌ DEBUG: JSON parsing error: {e}")
            return jsonify({"error": "Invalid JSON"}), 400

        # Validate required fields
        if not all(k in data for k in ["strategy", "data"]):
            print(f"❌ DEBUG: Missing required fields. Has: {list(data.keys())}")
            return jsonify({"error": "Missing required fields"}), 400

        # Get strategy
        strategy_name = data["strategy"]
        if strategy_name not in STRATEGIES:
            return jsonify({"error": f"Unknown strategy: {strategy_name}"}), 400

        strategy = STRATEGIES[strategy_name]

        # Convert data to DataFrame
        df = pd.DataFrame(data["data"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        # Get parameters
        parameters = data.get("parameters", {})
        initial_capital = parameters.get("initial_capital", 10000.0)
        commission = parameters.get("commission", 0.001)
        slippage = parameters.get("slippage", 0.0005)
        risk_params = parameters.get("risk_params", {})

        # Create backtest engine with parameters
        engine = BacktestEngine(
            initial_capital=initial_capital, commission=commission, slippage=slippage
        )

        # Run backtest
        try:
            result = engine.run_backtest(df, strategy, risk_params)
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400

        # Om strategin är ema_crossover, hämta ema-linjer och signaler
        extra = {}
        if strategy_name == "ema_crossover":
            strat_result = strategy(df, risk_params)
            extra = {
                "ema_fast": strat_result.get("ema_fast", []),
                "ema_slow": strat_result.get("ema_slow", []),
                "signals": strat_result.get("signals", []),
                "signal_result": strat_result.get("result")
            }

        # Convert result to dict
        def to_builtin(val):
            if isinstance(val, np.generic):
                return val.item()
            return val

        result_dict = {
            "total_trades": to_builtin(result.total_trades),
            "winning_trades": to_builtin(result.winning_trades),
            "losing_trades": to_builtin(result.losing_trades),
            "win_rate": to_builtin(result.win_rate),
            "total_pnl": to_builtin(result.total_pnl),
            "max_drawdown": to_builtin(result.max_drawdown),
            "sharpe_ratio": to_builtin(result.sharpe_ratio),
            "trade_history": result.trade_history,
            "equity_curve": {str(k): float(v) for k, v in result.equity_curve.items()},
            **extra
        }

        return jsonify(result_dict)

    except Exception as e:
        monitor.create_alert(AlertLevel.ERROR, f"Backtest failed: {str(e)}")
        return jsonify({"error": str(e)}), 500


@backtest_bp.route("/api/backtest/optimize", methods=["POST"])
def optimize_parameters():
    """
    Optimize strategy parameters using grid search.

    Request body:
    {
        "strategy": "strategy_name",
        "data": {
            "timestamp": [...],
            "open": [...],
            "high": [...],
            "low": [...],
            "close": [...],
            "volume": [...]
        },
        "param_grid": {
            "param1": [value1, value2, ...],
            "param2": [value1, value2, ...]
        }
    }
    """
    try:
        # Get request data
        data = request.get_json()

        # Validate required fields
        if not all(k in data for k in ["strategy", "data", "param_grid"]):
            return jsonify({"error": "Missing required fields"}), 400

        # Get strategy
        strategy_name = data["strategy"]
        if strategy_name not in STRATEGIES:
            return jsonify({"error": f"Unknown strategy: {strategy_name}"}), 400

        strategy = STRATEGIES[strategy_name]

        # Convert data to DataFrame
        df = pd.DataFrame(data["data"])
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df.set_index("timestamp", inplace=True)

        # Get parameter grid
        param_grid = data["param_grid"]

        # Run optimization
        try:
            result = backtest_engine.optimize_parameters(df, strategy, param_grid)

            # Konvertera numpy-typer och nycklar
            def to_builtin(val):
                if isinstance(val, np.generic):
                    return val.item()
                return val

            result = {
                "parameters": (
                    {str(k): to_builtin(v) for k, v in result["parameters"].items()}
                    if result["parameters"]
                    else {}
                ),
                "performance": {
                    str(k): to_builtin(v) for k, v in result["performance"].items()
                },
            }
        except ValueError as ve:
            return jsonify({"error": str(ve)}), 400

        return jsonify(result)

    except Exception as e:
        monitor.create_alert(
            AlertLevel.ERROR, f"Parameter optimization failed: {str(e)}"
        )
        return jsonify({"error": str(e)}), 500
