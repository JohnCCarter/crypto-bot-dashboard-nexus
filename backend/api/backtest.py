"""
Backtest API endpoints.
"""

from typing import Any, Dict

from fastapi import APIRouter, Body, HTTPException, status

# Create router
router = APIRouter(
    prefix="/api",
    tags=["backtest"],
)


@router.get("/backtest/strategies")
async def get_strategies() -> Dict[str, Any]:
    """
    Get all available strategies for backtesting.

    This is a placeholder that will be connected to the actual service.
    """
    # TODO: Implement connection to the backtest service
    return {
        "strategies": [
            {
                "id": "ema_crossover",
                "name": "EMA Crossover",
                "description": "Strategy based on EMA crossover signals",
            },
            {
                "id": "rsi_strategy",
                "name": "RSI Strategy",
                "description": "Strategy based on RSI overbought/oversold signals",
            },
            {
                "id": "fvg_strategy",
                "name": "Fair Value Gap Strategy",
                "description": "Strategy based on fair value gaps in the market",
            },
        ]
    }


@router.post("/backtest/run")
async def run_backtest(
    backtest_config: Dict[str, Any] = Body(..., description="Backtest configuration")
) -> Dict[str, Any]:
    """
    Run a backtest with the given configuration.

    This is a placeholder that will be connected to the actual service.
    """
    # TODO: Implement connection to the backtest service
    # Basic validation
    required_fields = ["strategy_id", "symbol", "timeframe", "start_date", "end_date"]
    for field in required_fields:
        if field not in backtest_config:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required field: {field}",
            )

    # Mock successful backtest run
    return {
        "id": "bt_12345",
        "strategy": backtest_config["strategy_id"],
        "symbol": backtest_config["symbol"],
        "timeframe": backtest_config["timeframe"],
        "start_date": backtest_config["start_date"],
        "end_date": backtest_config["end_date"],
        "status": "completed",
        "results": {
            "total_trades": 24,
            "winning_trades": 15,
            "losing_trades": 9,
            "win_rate": 0.625,
            "profit_factor": 1.8,
            "max_drawdown": 0.12,
            "net_profit": 0.35,
            "sharpe_ratio": 1.2,
        },
    }


@router.get("/backtest/{backtest_id}")
async def get_backtest_results(backtest_id: str) -> Dict[str, Any]:
    """
    Get results for a specific backtest.

    This is a placeholder that will be connected to the actual service.
    """
    # TODO: Implement connection to the backtest service
    # Mock data for demonstration
    if backtest_id == "bt_12345":
        return {
            "id": "bt_12345",
            "strategy": "ema_crossover",
            "symbol": "BTC/USD",
            "timeframe": "1h",
            "start_date": "2025-01-01T00:00:00Z",
            "end_date": "2025-06-30T23:59:59Z",
            "status": "completed",
            "results": {
                "total_trades": 24,
                "winning_trades": 15,
                "losing_trades": 9,
                "win_rate": 0.625,
                "profit_factor": 1.8,
                "max_drawdown": 0.12,
                "net_profit": 0.35,
                "sharpe_ratio": 1.2,
            },
            "trades": [
                {
                    "id": 1,
                    "timestamp": "2025-01-15T08:00:00Z",
                    "type": "buy",
                    "price": 45000.0,
                    "amount": 0.1,
                    "profit": None,
                },
                {
                    "id": 2,
                    "timestamp": "2025-01-17T14:00:00Z",
                    "type": "sell",
                    "price": 48000.0,
                    "amount": 0.1,
                    "profit": 0.067,
                },
            ],
        }

    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=f"Backtest with ID {backtest_id} not found",
    )
