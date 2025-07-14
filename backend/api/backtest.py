"""
Backtest API Routes för FastAPI
Exponerar endpoints för att köra backtests av trading strategier
"""

import logging
from typing import Any, Dict, List

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.api.models import BacktestRequest, BacktestResponse
from backend.services.backtest import BacktestEngine

# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/backtest",
    tags=["backtest"],
)

# Initialize backtest engine
backtest_engine = BacktestEngine()


@router.get("/strategies")
async def get_available_strategies():
    """
    Get available backtest strategies.

    Returns:
        List of available strategies
    """
    strategies = [
        {
            "name": "ema_crossover",
            "description": "EMA Crossover Strategy",
            "parameters": {
                "fast_period": {"type": "int", "default": 12, "min": 1, "max": 50},
                "slow_period": {"type": "int", "default": 26, "min": 1, "max": 100},
                "lookback": {"type": "int", "default": 100, "min": 10, "max": 1000},
            },
        },
        {
            "name": "rsi_strategy",
            "description": "RSI Strategy",
            "parameters": {
                "period": {"type": "int", "default": 14, "min": 1, "max": 50},
                "overbought": {"type": "float", "default": 70, "min": 50, "max": 100},
                "oversold": {"type": "float", "default": 30, "min": 0, "max": 50},
            },
        },
    ]
    return {"strategies": strategies}


@router.post("/run", response_model=BacktestResponse)
async def run_backtest(request: BacktestRequest):
    """
    Run a backtest with the specified strategy and parameters.

    Args:
        request: Backtest request with strategy, data, and parameters

    Returns:
        BacktestResponse: Results of the backtest
    """
    try:
        logger.info(f"Starting backtest for strategy: {request.strategy}")

        # Convert data to DataFrame format expected by backtest engine
        import pandas as pd

        # Create DataFrame from the data
        df = pd.DataFrame(
            {
                "timestamp": request.data["timestamp"],
                "open": request.data["open"],
                "high": request.data["high"],
                "low": request.data["low"],
                "close": request.data["close"],
                "volume": request.data["volume"],
            }
        )

        # Set timestamp as index
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df.set_index("timestamp", inplace=True)

        # Define strategy function based on request
        def strategy_func(data: pd.DataFrame) -> Dict[str, Any]:
            if request.strategy == "ema_crossover":
                return run_ema_crossover_strategy(data, request.parameters)
            elif request.strategy == "rsi_strategy":
                return run_rsi_strategy(data, request.parameters)
            else:
                raise ValueError(f"Unknown strategy: {request.strategy}")

        # Run backtest
        result = backtest_engine.run_backtest(df, strategy_func)

        # Convert result to response format
        response = BacktestResponse(
            id=f"backtest_{int(pd.Timestamp.now().timestamp())}",
            strategy=request.strategy,
            timeframe=request.timeframe,
            start_date=request.start_date,
            end_date=request.end_date,
            status="completed",
            results=result,
            trades=[],  # TODO: Add trade history
        )

        logger.info(f"Backtest completed successfully: {response.id}")
        return response

    except Exception as e:
        logger.error(f"Backtest failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")


def run_ema_crossover_strategy(
    data: pd.DataFrame, parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Run EMA crossover strategy."""
    try:
        from backend.strategies.ema_crossover import run_strategy

        fast_period = parameters.get("fast_period", 12)
        slow_period = parameters.get("slow_period", 26)
        lookback = parameters.get("lookback", 100)

        # Run strategy
        signals = run_strategy(data, fast_period=fast_period, slow_period=slow_period)

        return {
            "strategy": "ema_crossover",
            "signals": signals,
            "parameters": parameters,
        }
    except Exception as e:
        raise ValueError(f"EMA crossover strategy failed: {str(e)}")


def run_rsi_strategy(data: pd.DataFrame, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Run RSI strategy."""
    try:
        from backend.strategies.rsi_strategy import run_strategy

        period = parameters.get("period", 14)
        overbought = parameters.get("overbought", 70)
        oversold = parameters.get("oversold", 30)

        # Run strategy
        signals = run_strategy(
            data, period=period, overbought=overbought, oversold=oversold
        )

        return {
            "strategy": "rsi_strategy",
            "signals": signals,
            "parameters": parameters,
        }
    except Exception as e:
        raise ValueError(f"RSI strategy failed: {str(e)}")


@router.get("/results/{backtest_id}")
async def get_backtest_results(backtest_id: str):
    """
    Get results for a specific backtest.

    Args:
        backtest_id: ID of the backtest

    Returns:
        Backtest results
    """
    # TODO: Implement backtest result storage and retrieval
    raise HTTPException(
        status_code=501, detail="Backtest result storage not implemented yet"
    )
