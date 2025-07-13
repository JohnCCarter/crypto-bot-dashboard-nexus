"""
Balances API endpoints for FastAPI.
"""

from fastapi import APIRouter, HTTPException
from backend.api.models import BalancesResponse, Balance
from typing import List

router = APIRouter(
    prefix="/api",
    tags=["balances"],
)

@router.get("/balances", response_model=BalancesResponse)
async def get_balances() -> BalancesResponse:
    """
    Get account balances.
    
    Returns:
        BalancesResponse: List of account balances
    """
    try:
        # Return empty balances for now - this is a placeholder
        # In a real implementation, this would fetch from exchange
        balances = []
        
        return BalancesResponse(balances=balances)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get balances: {str(e)}") 