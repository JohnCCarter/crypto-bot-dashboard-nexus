"""
Orders API endpoints.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, status

from backend.api.dependencies import get_order_service
from backend.api.models import OrderCreateModel
from backend.services.order_service_async import OrderServiceAsync

# Create router
router = APIRouter(
    prefix="/api",
    tags=["orders"],
)


@router.get("/orders", response_model=Dict[str, List[Dict[str, Any]]])
async def get_orders(
    symbol: Optional[str] = Query(None, description="Filter orders by symbol"),
    status_filter: Optional[str] = Query(
        None, description="Filter orders by status", alias="status"
    ),
    limit: int = Query(50, description="Maximum number of orders to return"),
    order_service: OrderServiceAsync = Depends(get_order_service),
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Get all orders with optional filtering.

    Args:
        symbol: Filter orders by symbol
        status_filter: Filter orders by status
        limit: Maximum number of orders to return
        order_service: Order service dependency

    Returns:
        Dict with orders list
    """
    # Get open orders from the service
    open_orders = await order_service.get_open_orders(symbol)

    # Apply status filter if provided
    if status_filter:
        open_orders = [
            order for order in open_orders if order["status"] == status_filter
        ]

    # Apply limit
    open_orders = open_orders[:limit]

    return {"orders": open_orders}


@router.get("/orders/{order_id}", response_model=Dict[str, Any])
async def get_order_by_id(
    order_id: str,
    symbol: Optional[str] = Query(None, description="Order symbol"),
    order_service: OrderServiceAsync = Depends(get_order_service),
) -> Dict[str, Any]:
    """
    Get a specific order by ID.

    Args:
        order_id: Order ID
        symbol: Order symbol (optional)
        order_service: Order service dependency

    Returns:
        Order details

    Raises:
        HTTPException: If order not found
    """
    order = await order_service.get_order_status(order_id)

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found",
        )

    # order är nu garanterat Dict[str, Any] och inte None
    return dict(order)


@router.post(
    "/orders", status_code=status.HTTP_201_CREATED, response_model=Dict[str, Any]
)
async def place_order(
    order_data: OrderCreateModel = Body(..., description="Order details"),
    order_service: OrderServiceAsync = Depends(get_order_service),
) -> Dict[str, Any]:
    """
    Place a new order.

    Args:
        order_data: Order details
        order_service: Order service dependency

    Returns:
        Created order details

    Raises:
        HTTPException: If order creation fails
    """
    try:
        # Convert Pydantic model to dict
        order_dict = order_data.dict()
        # Rename type to order_type as expected by the service
        if "type" in order_dict:
            order_dict["order_type"] = order_dict.pop("type")

        result = await order_service.place_order(order_dict)
        return result

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to place order: {str(e)}",
        )


@router.delete("/orders/{order_id}", response_model=Dict[str, Any])
async def cancel_order(
    order_id: str,
    symbol: str = Query(..., description="Order symbol"),
    order_service: OrderServiceAsync = Depends(get_order_service),
) -> Dict[str, Any]:
    """
    Cancel an existing order.

    Args:
        order_id: Order ID
        symbol: Order symbol
        order_service: Order service dependency

    Returns:
        Cancellation result

    Raises:
        HTTPException: If cancellation fails
    """
    result = await order_service.cancel_order(order_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found or cannot be cancelled",
        )

    order = await order_service.get_order_status(order_id)
    if not order:
        # Om detta händer har något gått fel, men ordern har ändå lyckats avbrytas
        return {
            "id": order_id,
            "status": "cancelled",
            "cancelled_at": datetime.utcnow().isoformat(),
        }

    return dict(order)
