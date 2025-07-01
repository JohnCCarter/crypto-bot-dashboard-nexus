"""
Portfolio management API for FastAPI.

This module provides endpoints for portfolio management operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status

from backend.api.models import (
    ResponseStatus,
    StrategySignalRequest,
    PortfolioAllocationRequest,
    PortfolioAllocationResponse,
    StrategySignalResponse
)
from backend.api.dependencies import (
    get_portfolio_manager,
    get_exchange_service,
    get_order_service
)
from backend.services.portfolio_manager_async import PortfolioManagerAsync
from backend.services.exchange import ExchangeService
from backend.services.order_service_async import OrderServiceAsync

# Create router
router = APIRouter(
    prefix="/api/portfolio",
    tags=["portfolio"],
    responses={404: {"description": "Not found"}},
)


@router.post("/allocate", response_model=PortfolioAllocationResponse)
async def allocate_portfolio(
    allocation_request: PortfolioAllocationRequest,
    portfolio_manager: PortfolioManagerAsync = Depends(get_portfolio_manager),
    exchange_service: ExchangeService = Depends(get_exchange_service),
):
    """
    Calculate optimal portfolio allocation based on current market conditions
    and strategy signals.
    
    Args:
        allocation_request: Allocation request parameters
    
    Returns:
        PortfolioAllocationResponse: Optimal allocation data
    """
    try:
        # Get current balance data
        balance_data = await exchange_service.fetch_balance_async()
        
        # Calculate allocation
        allocation = await portfolio_manager.calculate_allocation(
            signals=allocation_request.signals,
            balance_data=balance_data,
            risk_profile=allocation_request.risk_profile,
            max_allocation_percent=allocation_request.max_allocation_percent
        )
        
        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Portfolio allocation calculated successfully",
            "allocations": allocation,
            "timestamp": allocation_request.timestamp
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to calculate portfolio allocation: {str(e)}"
        )


@router.post("/process-signals", response_model=StrategySignalResponse)
async def process_strategy_signals(
    signal_request: StrategySignalRequest,
    portfolio_manager: PortfolioManagerAsync = Depends(get_portfolio_manager),
    order_service: OrderServiceAsync = Depends(get_order_service),
):
    """
    Process strategy signals to determine trading actions.
    
    Args:
        signal_request: Strategy signals to process
    
    Returns:
        StrategySignalResponse: Trading actions based on signals
    """
    try:
        # Get current positions
        positions_resp = await order_service.get_positions()
        positions = positions_resp.get("positions", {})
        
        # Process signals
        actions = await portfolio_manager.process_strategy_signals(
            signals=signal_request.signals,
            current_positions=positions,
            timestamp=signal_request.timestamp
        )
        
        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Strategy signals processed successfully",
            "actions": actions,
            "timestamp": signal_request.timestamp
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process strategy signals: {str(e)}"
        )


@router.get("/status")
async def get_portfolio_status(
    portfolio_manager: PortfolioManagerAsync = Depends(get_portfolio_manager),
    exchange_service: ExchangeService = Depends(get_exchange_service),
    order_service: OrderServiceAsync = Depends(get_order_service),
):
    """
    Get current portfolio status including allocations, 
    performance metrics, and active positions.
    
    Returns:
        dict: Portfolio status information
    """
    try:
        # Get current positions
        positions_resp = await order_service.get_positions()
        positions = positions_resp.get("positions", {})
        
        # Get balance data
        balance_data = await exchange_service.fetch_balance_async()
        
        # Get open orders
        orders_resp = await order_service.get_open_orders()
        orders = orders_resp.get("orders", {})
        
        # Get portfolio status
        status = await portfolio_manager.get_portfolio_status(
            positions=positions,
            balance_data=balance_data,
            open_orders=orders
        )
        
        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Portfolio status retrieved successfully",
            "portfolio_status": status
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve portfolio status: {str(e)}"
        )


@router.post("/rebalance")
async def rebalance_portfolio(
    portfolio_manager: PortfolioManagerAsync = Depends(get_portfolio_manager),
    exchange_service: ExchangeService = Depends(get_exchange_service),
    order_service: OrderServiceAsync = Depends(get_order_service),
):
    """
    Rebalance the portfolio to match the target allocation.
    
    Returns:
        dict: Rebalance results
    """
    try:
        # Get current positions
        positions_resp = await order_service.get_positions()
        positions = positions_resp.get("positions", {})
        
        # Get balance data
        balance_data = await exchange_service.fetch_balance_async()
        
        # Rebalance portfolio
        rebalance_results = await portfolio_manager.rebalance_portfolio(
            current_positions=positions,
            balance_data=balance_data
        )
        
        return {
            "status": ResponseStatus.SUCCESS,
            "message": "Portfolio rebalanced successfully",
            "rebalance_results": rebalance_results
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to rebalance portfolio: {str(e)}"
        ) 