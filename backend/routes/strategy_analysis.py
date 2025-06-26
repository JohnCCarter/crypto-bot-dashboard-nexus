"""API routes for strategy analysis and probability data."""

from datetime import datetime

import pandas as pd
from flask import Blueprint, current_app, jsonify, request

from backend.services.portfolio_manager import PortfolioManager, StrategyWeight
from backend.services.risk_manager import RiskManager, RiskParameters

# Import strategies
from backend.strategies import (
    ema_crossover_strategy,
    fvg_strategy,
    rsi_strategy,
    sample_strategy,
)

strategy_analysis_bp = Blueprint("strategy_analysis", __name__)

# Available strategies mapping
AVAILABLE_STRATEGIES = {
    "ema_crossover": ema_crossover_strategy,
    "rsi": rsi_strategy,
    "fvg": fvg_strategy,
    "sample": sample_strategy,
}


def get_services():
    """Get services from application context."""
    if not hasattr(current_app, "_services"):
        return None
    return current_app._services


@strategy_analysis_bp.route("/api/strategy/analyze", methods=["POST"])
def analyze_strategies():
    """
    Analyze multiple strategies and return probability data.

    Expected JSON payload:
    {
        "symbol": "BTC/USD",
        "timeframe": "1h",
        "data": [...],  // OHLC data
        "strategies": {
            "ema_crossover": {"fast_period": 12, "slow_period": 26},
            "rsi": {"rsi_period": 14, "overbought": 70, "oversold": 30}
        }
    }

    Returns:
    {
        "symbol": "BTC/USD",
        "analysis_timestamp": "...",
        "individual_signals": {...},
        "combined_signal": {...},
        "risk_assessment": {...}
    }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No JSON data provided"}), 400

        symbol = data.get("symbol", "UNKNOWN")
        timeframe = data.get("timeframe", "1h")
        price_data = data.get("data", [])
        strategy_configs = data.get("strategies", {})

        if not price_data:
            return jsonify({"error": "No price data provided"}), 400

        # Convert to DataFrame
        df = pd.DataFrame(price_data)
        required_columns = ["open", "high", "low", "close"]

        if not all(col in df.columns for col in required_columns):
            return (
                jsonify({"error": f"Data must contain columns: {required_columns}"}),
                400,
            )

        # Run individual strategy analyses
        individual_signals = {}

        for strategy_name, params in strategy_configs.items():
            if strategy_name not in AVAILABLE_STRATEGIES:
                continue

            try:
                strategy_module = AVAILABLE_STRATEGIES[strategy_name]

                # Add symbol and timeframe to params
                params.update({"symbol": symbol, "timeframe": timeframe})

                signal = strategy_module.run_strategy(df, params)

                individual_signals[strategy_name] = {
                    "action": signal.action,
                    "confidence": signal.confidence,
                    "position_size": signal.position_size,
                    "metadata": signal.metadata,
                }

            except Exception as e:
                individual_signals[strategy_name] = {
                    "error": str(e),
                    "action": "hold",
                    "confidence": 0.0,
                }

        # Get current price (last close)
        current_price = float(df["close"].iloc[-1]) if len(df) > 0 else 0.0

        # Create portfolio manager for signal combination
        strategy_weights = [
            StrategyWeight("ema_crossover", 0.4, 0.6),
            StrategyWeight("rsi", 0.3, 0.5),
            StrategyWeight("fvg", 0.2, 0.5),
            StrategyWeight("sample", 0.1, 0.3),
        ]

        # Create risk manager
        risk_params = RiskParameters(
            max_position_size=0.1,
            max_leverage=2.0,
            stop_loss_pct=0.05,
            take_profit_pct=0.1,
            max_daily_loss=0.02,
            max_open_positions=5,
            min_signal_confidence=0.6,
        )
        risk_manager = RiskManager(risk_params)
        portfolio_manager = PortfolioManager(risk_manager, strategy_weights)

        # Convert individual signals to TradeSignal objects for combination
        from backend.strategies.sample_strategy import TradeSignal

        trade_signals = {}

        for name, signal_data in individual_signals.items():
            if "error" not in signal_data:
                trade_signals[name] = TradeSignal(
                    action=signal_data["action"],
                    confidence=signal_data["confidence"],
                    position_size=signal_data["position_size"],
                    metadata=signal_data["metadata"],
                )

        # Combine signals
        combined_signal = portfolio_manager.combine_strategy_signals(
            trade_signals, symbol, current_price
        )

        # Get portfolio summary (empty positions for analysis)
        portfolio_summary = portfolio_manager.get_portfolio_summary({})

        response = {
            "symbol": symbol,
            "timeframe": timeframe,
            "current_price": current_price,
            "analysis_timestamp": datetime.now().isoformat(),
            "individual_signals": individual_signals,
            "combined_signal": {
                "action": combined_signal.action,
                "combined_confidence": combined_signal.combined_confidence,
                "probabilities": {
                    "buy": combined_signal.combined_probabilities.probability_buy,
                    "sell": combined_signal.combined_probabilities.probability_sell,
                    "hold": combined_signal.combined_probabilities.probability_hold,
                },
                "risk_score": combined_signal.combined_probabilities.get_risk_score(),
                "metadata": combined_signal.metadata,
            },
            "portfolio_summary": portfolio_summary,
            "strategies_analyzed": len(individual_signals),
            "valid_signals": len(trade_signals),
        }

        return jsonify(response), 200

    except Exception as e:
        return jsonify({"error": f"Strategy analysis failed: {str(e)}"}), 500


@strategy_analysis_bp.route("/api/strategy/available", methods=["GET"])
def get_available_strategies():
    """
    Get list of available strategies with their parameter schemas.

    Returns:
    {
        "strategies": {
            "ema_crossover": {
                "name": "EMA Crossover",
                "description": "...",
                "parameters": {...}
            }
        }
    }
    """
    try:
        strategies_info = {
            "ema_crossover": {
                "name": "EMA Crossover Strategy",
                "description": "Exponential Moving Average crossover signals with probability analysis",
                "parameters": {
                    "fast_period": {"type": "int", "default": 12, "min": 5, "max": 50},
                    "slow_period": {
                        "type": "int",
                        "default": 26,
                        "min": 10,
                        "max": 100,
                    },
                    "buy_threshold": {
                        "type": "float",
                        "default": 0.0,
                        "description": "Threshold for buy signals",
                    },
                    "sell_threshold": {
                        "type": "float",
                        "default": 0.0,
                        "description": "Threshold for sell signals",
                    },
                    "position_size": {
                        "type": "float",
                        "default": 1.0,
                        "min": 0.1,
                        "max": 1.0,
                    },
                },
            },
            "rsi": {
                "name": "RSI Strategy",
                "description": "Relative Strength Index strategy with probability analysis",
                "parameters": {
                    "rsi_period": {"type": "int", "default": 14, "min": 5, "max": 50},
                    "overbought": {
                        "type": "float",
                        "default": 70,
                        "min": 50,
                        "max": 90,
                    },
                    "oversold": {"type": "float", "default": 30, "min": 10, "max": 50},
                    "position_size": {
                        "type": "float",
                        "default": 1.0,
                        "min": 0.1,
                        "max": 1.0,
                    },
                },
            },
            "fvg": {
                "name": "Fair Value Gap Strategy",
                "description": "Fair Value Gap detection with probability analysis",
                "parameters": {
                    "lookback": {"type": "int", "default": 3, "min": 1, "max": 10},
                    "position_size": {
                        "type": "float",
                        "default": 1.0,
                        "min": 0.1,
                        "max": 1.0,
                    },
                },
            },
            "sample": {
                "name": "Sample Strategy",
                "description": "Template strategy demonstrating probability framework",
                "parameters": {
                    "position_size": {
                        "type": "float",
                        "default": 1.0,
                        "min": 0.1,
                        "max": 1.0,
                    },
                    "indicator_value": {"type": "float", "default": 0.0},
                    "buy_threshold": {"type": "float", "default": 1.0},
                    "sell_threshold": {"type": "float", "default": -1.0},
                },
            },
        }

        return (
            jsonify(
                {
                    "strategies": strategies_info,
                    "total_strategies": len(strategies_info),
                    "framework_version": "probability_based_v1.0",
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Failed to get strategies: {str(e)}"}), 500


@strategy_analysis_bp.route("/api/strategy/backtest", methods=["POST"])
def backtest_strategy():
    """
    Backtest a strategy with probability analysis.

    Expected JSON:
    {
        "strategy": "ema_crossover",
        "parameters": {...},
        "data": [...],  // Historical OHLC data
        "initial_balance": 10000
    }

    Returns backtest results with probability metrics.
    """
    try:
        data = request.get_json()

        strategy_name = data.get("strategy")
        params = data.get("parameters", {})
        price_data = data.get("data", [])
        initial_balance = data.get("initial_balance", 10000)

        if strategy_name not in AVAILABLE_STRATEGIES:
            return jsonify({"error": f"Unknown strategy: {strategy_name}"}), 400

        if not price_data:
            return jsonify({"error": "No price data provided"}), 400

        # Convert to DataFrame
        df = pd.DataFrame(price_data)

        # Simple backtest simulation
        strategy_module = AVAILABLE_STRATEGIES[strategy_name]
        balance = initial_balance
        positions = []
        trades = []

        # Rolling window backtest
        window_size = 50  # Minimum data points needed

        for i in range(window_size, len(df)):
            window_df = df.iloc[i - window_size : i]

            try:
                signal = strategy_module.run_strategy(window_df, params)
                current_price = float(df.iloc[i]["close"])

                trade_record = {
                    "timestamp": i,
                    "price": current_price,
                    "action": signal.action,
                    "confidence": signal.confidence,
                    "probabilities": {
                        "buy": signal.metadata.get("probability_buy", 0.33),
                        "sell": signal.metadata.get("probability_sell", 0.33),
                        "hold": signal.metadata.get("probability_hold", 0.34),
                    },
                    "balance_before": balance,
                }

                # Simple execution logic
                if signal.action == "buy" and signal.confidence > 0.6:
                    position_size = (
                        balance * signal.position_size * 0.1
                    )  # Max 10% per trade
                    positions.append(
                        {
                            "type": "buy",
                            "size": position_size / current_price,
                            "entry_price": current_price,
                            "timestamp": i,
                        }
                    )
                    balance -= position_size

                elif signal.action == "sell" and positions:
                    # Close oldest position
                    if positions:
                        position = positions.pop(0)
                        profit = (current_price - position["entry_price"]) * position[
                            "size"
                        ]
                        balance += position["size"] * current_price

                        trades.append(
                            {
                                "entry_price": position["entry_price"],
                                "exit_price": current_price,
                                "profit": profit,
                                "duration": i - position["timestamp"],
                            }
                        )

                trade_record["balance_after"] = balance

            except Exception as e:
                trade_record = {
                    "timestamp": i,
                    "error": str(e),
                    "balance_before": balance,
                    "balance_after": balance,
                }

        # Calculate performance metrics
        total_trades = len(trades)
        profitable_trades = len([t for t in trades if t["profit"] > 0])
        total_profit = sum(t["profit"] for t in trades)
        final_balance = balance + sum(
            pos["size"] * df.iloc[-1]["close"] for pos in positions
        )

        win_rate = (profitable_trades / total_trades) if total_trades > 0 else 0
        total_return = ((final_balance - initial_balance) / initial_balance) * 100

        return (
            jsonify(
                {
                    "strategy": strategy_name,
                    "parameters": params,
                    "initial_balance": initial_balance,
                    "final_balance": final_balance,
                    "total_return_pct": total_return,
                    "total_trades": total_trades,
                    "profitable_trades": profitable_trades,
                    "win_rate": win_rate,
                    "total_profit": total_profit,
                    "avg_trade_profit": (
                        total_profit / total_trades if total_trades > 0 else 0
                    ),
                    "open_positions": len(positions),
                    "backtest_period": len(df) - window_size,
                    "probability_framework": "enabled",
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Backtest failed: {str(e)}"}), 500


@strategy_analysis_bp.route("/api/strategy/portfolio-risk", methods=["POST"])
def assess_portfolio_risk():
    """
    Assess portfolio risk using probability data.

    Expected JSON:
    {
        "positions": {
            "BTC/USD": {
                "size": 1.0,
                "entry_price": 50000,
                "probability_data": {...}
            }
        }
    }

    Returns risk assessment with recommendations.
    """
    try:
        data = request.get_json()
        positions = data.get("positions", {})

        # Create risk manager
        risk_params = RiskParameters(
            max_position_size=0.1,
            max_leverage=2.0,
            stop_loss_pct=0.05,
            take_profit_pct=0.1,
            max_daily_loss=0.02,
            max_open_positions=5,
        )
        risk_manager = RiskManager(risk_params)

        # Assess portfolio risk
        risk_assessment = risk_manager.assess_portfolio_risk(positions)

        return (
            jsonify(
                {
                    "portfolio_risk_assessment": risk_assessment,
                    "assessment_timestamp": datetime.now().isoformat(),
                    "framework_version": "probability_based_v1.0",
                }
            ),
            200,
        )

    except Exception as e:
        return jsonify({"error": f"Risk assessment failed: {str(e)}"}), 500
