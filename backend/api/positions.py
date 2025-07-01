"""
Positions API endpoints for fetching live positions from Bitfinex.
"""

from typing import Dict, Any, List, Optional

from fastapi import APIRouter, HTTPException, status

from backend.api.models import PositionsResponse
from backend.services.positions_service import fetch_live_positions_async
from backend.services.exchange import ExchangeError
from backend.services.event_logger import (
    event_logger, should_suppress_routine_log, EventType
)

# Create router
router = APIRouter(
    prefix="/api",
    tags=["positions"],
)


@router.get("/positions", response_model=PositionsResponse)
async def get_positions(symbols: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Fetch current positions from Bitfinex.

    Returns live positions if API keys are configured,
    otherwise returns empty list (no mock data for live trading).
    
    Parameters:
    -----------
    symbols: Optional list of symbols to filter by
    
    Returns:
    --------
    PositionsResponse: List of live positions from Bitfinex
    """
    try:
        # Attempt to fetch live positions from Bitfinex using async function
        positions = await fetch_live_positions_async(symbols)

        # Endast logga om det INTE är routine polling
        if not should_suppress_routine_log("/api/positions", "GET"):
            event_logger.log_event(
                EventType.API_ERROR,  # Using available type
                f"Positions fetched: {len(positions)} positions"
            )

        return {"positions": positions}

    except ExchangeError as e:
        # FEL ska alltid loggas - de är meningsfulla
        event_logger.log_exchange_error("fetch_positions", str(e))
        
        # Return empty list rather than mock data for safety
        return {"positions": []}

    except Exception as e:
        # Kritiska fel ska alltid loggas
        event_logger.log_api_error("/api/positions", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 