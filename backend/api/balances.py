"""
Balances API endpoints.
"""

from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status

from backend.api.models import Balance, BalancesResponse

# Create router
router = APIRouter(
    prefix="/api",
    tags=["balances"],
)


@router.get("/balances", response_model=BalancesResponse)
async def get_balances() -> Dict[str, Any]:
    """
    Get account balances.
    
    This is a placeholder that will be connected to the actual service.
    """
    # TODO: Implement connection to the balance service
    return {
        "balances": [
            {
                "currency": "BTC",
                "available": 1.23456789,
                "reserved": 0.1,
                "total": 1.33456789
            },
            {
                "currency": "USD",
                "available": 10000.50,
                "reserved": 500.25,
                "total": 10500.75
            }
        ]
    }


@router.get("/balances/{currency}", response_model=Balance)
async def get_balance_by_currency(currency: str) -> Dict[str, Any]:
    """
    Get balance for a specific currency.
    
    This is a placeholder that will be connected to the actual service.
    """
    # TODO: Implement connection to the balance service
    if currency.upper() not in ["BTC", "USD", "ETH"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Balance for currency {currency} not found"
        )
    
    # Mock data based on currency
    mock_data = {
        "BTC": {"available": 1.23456789, "reserved": 0.1, "total": 1.33456789},
        "USD": {"available": 10000.50, "reserved": 500.25, "total": 10500.75},
        "ETH": {"available": 15.5, "reserved": 2.5, "total": 18.0}
    }
    
    return {
        "currency": currency.upper(),
        **mock_data[currency.upper()]
    } 