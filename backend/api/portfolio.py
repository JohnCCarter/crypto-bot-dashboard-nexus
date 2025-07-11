"""
Portfolio management API endpoints for FastAPI.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from backend.api.dependencies import get_portfolio_manager, get_risk_manager
from backend.api.models import (AllocationItem, PortfolioAllocationRequest,
                                PortfolioAllocationResponse, ResponseStatus,
                                RiskProfile, SignalData, StrategySignalRequest,
                                StrategySignalResponse)
from backend.services.live_portfolio_service_async import \
    LivePortfolioServiceAsync
from backend.services.portfolio_manager_async import PortfolioManagerAsync
from backend.services.risk_manager_async import RiskManagerAsync

# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/portfolio",
    tags=["portfolio"],
)


def get_live_portfolio_service() -> LivePortfolioServiceAsync:
    """
    Dependency for LivePortfolioServiceAsync.

    Returns:
        LivePortfolioServiceAsync instance
    """
    return LivePortfolioServiceAsync()


@router.post("/allocate", response_model=PortfolioAllocationResponse)
async def allocate_portfolio(
    request: PortfolioAllocationRequest,
    portfolio_manager: PortfolioManagerAsync = Depends(get_portfolio_manager),
    risk_manager: RiskManagerAsync = Depends(get_risk_manager),
) -> Dict[str, Any]:
    """
    Calculate optimal portfolio allocation based on strategy signals and risk profile.

    Parameters:
    -----------
    request: Portfolio allocation request with signals and risk parameters

    Returns:
    --------
    PortfolioAllocationResponse: Portfolio allocation details
    """
    try:
        # Convert SignalData to Dict format expected by portfolio_manager
        signal_dicts = [signal.dict() for signal in request.signals]
        allocations = await portfolio_manager.calculate_allocations(
            signal_dicts, request.risk_profile.value, request.max_allocation_percent
        )

        # Calculate risk assessment for the allocations
        risk_assessment = await risk_manager.assess_portfolio_risk(
            {}
        )  # Empty dict as we don't have actual positions here

        return {
            "status": ResponseStatus.SUCCESS,
            "message": f"Calculated portfolio allocation for {len(allocations)} assets",
            "allocations": allocations,
            "timestamp": datetime.now(),
        }

    except ValidationError as e:
        logger.error(f"Validation error in allocate_portfolio: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to calculate portfolio allocation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate portfolio allocation: {str(e)}",
        )


@router.post("/process-signals", response_model=StrategySignalResponse)
async def process_strategy_signals(
    request: StrategySignalRequest,
    portfolio_manager: PortfolioManagerAsync = Depends(get_portfolio_manager),
) -> Dict[str, Any]:
    """
    Process strategy signals to determine trading actions.

    Parameters:
    -----------
    request: Strategy signal request with signals from various strategies

    Returns:
    --------
    StrategySignalResponse: Recommended trading actions
    """
    try:
        # Convert SignalData to Dict format expected by portfolio_manager
        signal_dicts = [signal.dict() for signal in request.signals]
        actions = await portfolio_manager.process_signals(signal_dicts)

        return {
            "status": ResponseStatus.SUCCESS,
            "message": f"Processed {len(request.signals)} strategy signals",
            "actions": actions,
            "timestamp": datetime.now(),
        }

    except ValidationError as e:
        logger.error(f"Validation error in process_strategy_signals: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to process strategy signals: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process strategy signals: {str(e)}",
        )


@router.get("/status")
async def get_portfolio_status(
    portfolio_manager: PortfolioManagerAsync = Depends(get_portfolio_manager),
) -> Dict[str, Any]:
    """
    Get current portfolio status with allocations and metrics.

    Returns:
    --------
    Dict: Portfolio status with allocations and metrics
    """
    try:
        portfolio_status = await portfolio_manager.get_portfolio_status()

        return {
            "status": ResponseStatus.SUCCESS,
            "portfolio_status": portfolio_status,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get portfolio status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio status: {str(e)}",
        )


@router.post("/rebalance")
async def rebalance_portfolio(
    target_allocations: List[AllocationItem],
    portfolio_manager: PortfolioManagerAsync = Depends(get_portfolio_manager),
) -> Dict[str, Any]:
    """
    Rebalance portfolio to match target allocations.

    Parameters:
    -----------
    target_allocations: Target allocations for rebalancing

    Returns:
    --------
    Dict: Rebalancing results
    """
    try:
        # Konvertera target_allocations till dictionary-format som förväntas av portfolio_manager
        allocations_dict = [allocation.dict() for allocation in target_allocations]

        rebalance_results = await portfolio_manager.rebalance_portfolio(
            allocations_dict
        )

        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Portfolio rebalanced successfully",
            "rebalance_results": rebalance_results,
            "timestamp": datetime.now().isoformat(),
        }

    except ValidationError as e:
        logger.error(f"Validation error in rebalance_portfolio: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to rebalance portfolio: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rebalance portfolio: {str(e)}",
        )


@router.get("/live/snapshot")
async def get_live_portfolio_snapshot(
    symbols: Optional[List[str]] = None,
    live_portfolio: LivePortfolioServiceAsync = Depends(get_live_portfolio_service),
) -> Dict[str, Any]:
    """
    Get live portfolio snapshot with current market prices.

    Parameters:
    -----------
    symbols: Optional list of symbols to include in the snapshot

    Returns:
    --------
    Dict: Live portfolio snapshot data
    """
    try:
        snapshot = await live_portfolio.get_live_portfolio_snapshot(symbols)

        # Convert to serializable format
        positions = []
        for position in snapshot.positions:
            positions.append(
                {
                    "symbol": position.symbol,
                    "amount": position.amount,
                    "entry_price": position.entry_price,
                    "current_price": position.current_price,
                    "unrealized_pnl": position.unrealized_pnl,
                    "unrealized_pnl_pct": position.unrealized_pnl_pct,
                    "market_value": position.market_value,
                    "timestamp": position.timestamp.isoformat(),
                }
            )

        result = {
            "total_value": snapshot.total_value,
            "available_balance": snapshot.available_balance,
            "positions": positions,
            "total_unrealized_pnl": snapshot.total_unrealized_pnl,
            "total_unrealized_pnl_pct": snapshot.total_unrealized_pnl_pct,
            "timestamp": snapshot.timestamp.isoformat(),
            "market_data_quality": snapshot.market_data_quality,
        }

        return {
            "status": ResponseStatus.SUCCESS,
            "snapshot": result,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get live portfolio snapshot: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get live portfolio snapshot: {str(e)}",
        )


@router.get("/live/performance")
async def get_live_portfolio_performance(
    timeframe: str = "24h",
    live_portfolio: LivePortfolioServiceAsync = Depends(get_live_portfolio_service),
) -> Dict[str, Any]:
    """
    Get live portfolio performance metrics.

    Parameters:
    -----------
    timeframe: Timeframe for performance metrics (e.g. "24h", "7d", "30d")

    Returns:
    --------
    Dict: Performance metrics
    """
    try:
        metrics = await live_portfolio.get_portfolio_performance(timeframe)

        # Convert to serializable format
        metrics_data = []
        for metric in metrics:
            metrics_data.append(
                {
                    "name": metric.name,
                    "value": metric.value,
                    "unit": metric.unit,
                    "timestamp": metric.timestamp.isoformat(),
                }
            )

        return {
            "status": ResponseStatus.SUCCESS,
            "timeframe": timeframe,
            "performance_metrics": metrics_data,
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Failed to get portfolio performance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get portfolio performance: {str(e)}",
        )


@router.post("/live/validate-trade")
async def validate_live_trade(
    symbol: str,
    amount: float,
    trade_type: str,
    live_portfolio: LivePortfolioServiceAsync = Depends(get_live_portfolio_service),
) -> Dict[str, Any]:
    """
    Validate a potential trade against available balance and position limits.

    Parameters:
    -----------
    symbol: Trading symbol
    amount: Trade amount
    trade_type: Type of trade (buy/sell)

    Returns:
    --------
    Dict: Trade validation result
    """
    try:
        # Validate trade_type
        if trade_type not in ["buy", "sell", "long", "short"]:
            raise ValueError(f"Invalid trade type: {trade_type}")

        validation = await live_portfolio.validate_trade(symbol, amount, trade_type)

        # Convert to serializable format
        result = {
            "is_valid": validation.is_valid,
            "message": validation.message,
            "available_balance": validation.available_balance,
            "required_balance": validation.required_balance,
            "max_trade_size": validation.max_trade_size,
            "timestamp": validation.timestamp.isoformat(),
        }

        return {
            "status": ResponseStatus.SUCCESS,
            "validation": result,
            "timestamp": datetime.now().isoformat(),
        }

    except ValueError as e:
        logger.error(f"Validation error in validate_live_trade: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to validate trade: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate trade: {str(e)}",
        )
