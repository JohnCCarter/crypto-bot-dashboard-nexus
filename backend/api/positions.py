"""
Positions API endpoints for FastAPI.
"""

from typing import Dict, Any, List

from fastapi import APIRouter, HTTPException, Depends, status

from backend.services.exchange import ExchangeError
from backend.services.positions_service import fetch_live_positions_async
from backend.api.models import ResponseStatus


# Create router
router = APIRouter(
    prefix="/api/positions",
    tags=["positions"],
)


@router.get("")
async def get_positions() -> Dict[str, Any]:
    """
    Fetch current positions from Bitfinex.

    Returns live positions if API keys are configured,
    otherwise returns empty list (no mock data for live trading).

    Returns:
        Dict: List of positions and metadata
    """
    try:
        # Attempt to fetch live positions from Bitfinex
        positions = await fetch_live_positions_async()

        return {
            "status": ResponseStatus.SUCCESS,
            "positions": positions,
            "count": len(positions),
            "timestamp": positions[0].get("timestamp") if positions else None,
        }

    except ExchangeError as e:
        # For exchange errors, return empty list rather than mock data for safety
        return {
            "status": ResponseStatus.WARNING,
            "positions": [],
            "count": 0,
            "message": f"Exchange error: {str(e)}",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch positions: {str(e)}"
        ) 