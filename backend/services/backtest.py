"""Backtesting service for trading strategies."""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union

import numpy as np
import pandas as pd

from backend.services.monitor import AlertLevel, Monitor
from backend.strategies.sample_strategy import TradeSignal


@dataclass
class BacktestResult:
    """Backtesting results."""

    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    trade_history: List[Dict[str, Any]]
    equity_curve: pd.Series


class BacktestEngine:
    """Engine for backtesting trading strategies."""

    def __init__(
        self,
        initial_capital: float = 10000.0,
        commission: float = 0.001,  # 0.1%
        slippage: float = 0.0005,  # 0.05%
    ):
        """
        Initialize backtest engine.

        Args:
            initial_capital: Starting capital
            commission: Trading commission as decimal
            slippage: Price slippage as decimal
        """
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.monitor = Monitor()

    def run_backtest(
        self,
        data: pd.DataFrame,
        strategy: Union[
            Callable[[pd.DataFrame], TradeSignal],
            Callable[[pd.DataFrame, Dict[str, Any]], TradeSignal],
        ],
        risk_params: Optional[Dict[str, Any]] = None,
    ) -> BacktestResult:
        """
        Run backtest on historical data.

        Args:
            data: Historical price data
            strategy: Strategy function to test
            risk_params: Optional risk parameters

        Returns:
            BacktestResult containing performance metrics
        """
        import inspect

        # Kontrollera att data inte är tom
        if data is None or len(data) < 2:
            raise ValueError("Data for backtest must contain at least 2 rows.")

        # Initialize tracking variables
        capital = self.initial_capital
        position = 0.0
        entry_price = 0.0
        trades = []
        equity = [capital]

        # Set default risk parameters
        risk_params = risk_params or {
            "max_position_size": 0.1,
            "stop_loss_pct": 0.02,
            "take_profit_pct": 0.04,
        }

        # Check strategy signature to determine how to call it
        sig = inspect.signature(strategy)
        strategy_expects_params = len(sig.parameters) >= 2

        # Iterate through data
        for i in range(len(data)):
            current_data = data.iloc[: i + 1]
            current_price = current_data["close"].iloc[-1]

            # Get strategy signal
            if strategy_expects_params:
                signal = strategy(current_data, risk_params)
            else:
                signal = strategy(current_data)

            # Calculate position size
            if signal.action != "hold":
                position_size = (
                    capital * risk_params["max_position_size"] * signal.confidence
                )
            else:
                position_size = 0.0

            # Handle existing position
            if position != 0:
                # Check stop loss
                stop_loss = (
                    entry_price * (1 - risk_params["stop_loss_pct"])
                    if position > 0
                    else entry_price * (1 + risk_params["stop_loss_pct"])
                )

                # Check take profit
                take_profit = (
                    entry_price * (1 + risk_params["take_profit_pct"])
                    if position > 0
                    else entry_price * (1 - risk_params["take_profit_pct"])
                )

                # Close position if conditions met
                if (
                    (position > 0 and current_price <= stop_loss)
                    or (position < 0 and current_price >= stop_loss)
                    or (position > 0 and current_price >= take_profit)
                    or (position < 0 and current_price <= take_profit)
                ):
                    # Calculate PnL
                    pnl = position * (current_price - entry_price)
                    commission_cost = abs(position * current_price * self.commission)
                    slippage_cost = abs(position * current_price * self.slippage)
                    net_pnl = pnl - commission_cost - slippage_cost

                    # Update capital
                    capital += net_pnl

                    # Record trade
                    trade = {
                        "entry_time": current_data.index[-1],
                        "exit_time": current_data.index[-1],
                        "entry_price": entry_price,
                        "exit_price": current_price,
                        "position": position,
                        "pnl": net_pnl,
                        "commission": commission_cost,
                        "slippage": slippage_cost,
                    }
                    trades.append(trade)

                    # Reset position
                    position = 0.0
                    entry_price = 0.0

            # Handle new position
            if position == 0 and signal.action != "hold":
                # Calculate entry price with slippage
                entry_price = (
                    current_price * (1 + self.slippage)
                    if signal.action == "buy"
                    else current_price * (1 - self.slippage)
                )

                # Set position
                position = (
                    position_size / entry_price
                    if signal.action == "buy"
                    else -position_size / entry_price
                )

            # Update equity curve
            current_equity = capital
            if position != 0:
                unrealized_pnl = position * (current_price - entry_price)
                current_equity += unrealized_pnl
            equity.append(current_equity)

        # Efter loopen, se till att equity och data.index har samma längd
        if len(equity) > len(data.index):
            equity = equity[: len(data.index)]
        elif len(equity) < len(data.index):
            # Om equity är för kort, fyll på med sista värdet
            equity += [equity[-1]] * (len(data.index) - len(equity))

        equity_series = pd.Series(equity, index=data.index)
        returns = equity_series.pct_change().dropna()

        # Calculate performance metrics
        total_trades = len(trades)
        winning_trades = len([t for t in trades if t["pnl"] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0.0

        total_pnl = float(sum(t["pnl"] for t in trades))

        # Calculate drawdown
        rolling_max = equity_series.expanding().max()
        drawdowns = (equity_series - rolling_max) / rolling_max
        max_drawdown = float(abs(drawdowns.min()))

        # Calculate Sharpe ratio
        if len(returns) > 0:
            sharpe_ratio = (
                float(np.sqrt(252) * returns.mean() / returns.std())
                if returns.std() != 0
                else 0.0
            )
        else:
            sharpe_ratio = 0.0

        # Create result
        result = BacktestResult(
            total_trades=total_trades,
            winning_trades=winning_trades,
            losing_trades=losing_trades,
            win_rate=win_rate,
            total_pnl=total_pnl,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trade_history=trades,
            equity_curve=equity_series,
        )

        # Log results
        self.monitor.create_alert(
            AlertLevel.INFO,
            "Backtest completed",
            {
                "total_trades": total_trades,
                "win_rate": win_rate,
                "total_pnl": total_pnl,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio,
            },
        )

        return result

    def optimize_parameters(
        self,
        data: pd.DataFrame,
        strategy: Union[
            Callable[[pd.DataFrame], TradeSignal],
            Callable[[pd.DataFrame, Dict[str, Any]], TradeSignal],
        ],
        param_grid: Dict[str, List[Any]],
    ) -> Dict[str, Any]:
        """
        Optimize strategy parameters using grid search.

        Args:
            data: Historical price data
            strategy: Strategy function to optimize
            param_grid: Parameter grid for optimization

        Returns:
            Dict containing best parameters and performance
        """
        import inspect

        best_result = None
        best_sharpe = float("-inf")
        best_params = None

        # Generate parameter combinations
        param_combinations = [
            dict(zip(param_grid.keys(), v))
            for v in np.array(np.meshgrid(*param_grid.values())).T.reshape(
                -1, len(param_grid)
            )
        ]

        for idx, params in enumerate(param_combinations):
            # Kontrollera om strategin accepterar två argument
            sig = inspect.signature(strategy)
            if len(sig.parameters) == 2:

                def create_strategy_wrapper(p):
                    def strategy_wrapper(df):
                        return strategy(df, p)

                    return strategy_wrapper

                strategy_func = create_strategy_wrapper(params)

            else:

                def strategy_func(df):
                    return strategy(df)

            # Run backtest
            result = self.run_backtest(data, strategy_func)

            # Update best result
            if result.sharpe_ratio > best_sharpe:
                best_sharpe = result.sharpe_ratio
                best_result = result
                best_params = params

        return {
            "parameters": best_params,
            "performance": {
                "sharpe_ratio": best_sharpe,
                "total_pnl": best_result.total_pnl,
                "win_rate": best_result.win_rate,
                "max_drawdown": best_result.max_drawdown,
            },
        }
