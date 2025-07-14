"""API routes for positions management with FastAPI."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException

from backend.api.dependencies import get_positions_service_async
from backend.api.models import PositionsResponse
from backend.services.event_logger import (
    EventType,
    event_logger,
    should_suppress_routine_log,
)
from backend.services.exchange import ExchangeError

# Create router
router = APIRouter(prefix="/api/positions", tags=["positions"])


@router.get("/", response_model=PositionsResponse)
async def get_positions(
    symbols: Optional[List[str]] = None,
    fetch_positions_async=Depends(get_positions_service_async),
):
    """
    Fetch current positions from Bitfinex.

    Returns live positions if API keys are configured,
    otherwise returns empty list (no mock data for live trading).

    Args:
        symbols: Optional list of symbols to filter by

    Returns:
        List of live positions
    """
    # Detta är routine polling - supprimerias enligt event_logger

    try:
        # Attempt to fetch live positions from Bitfinex using async service
        positions = await fetch_positions_async(symbols)

        # Endast logga om det INTE är routine polling
        if not should_suppress_routine_log("/api/positions", "GET"):
            event_logger.log_event(
                EventType.API_ERROR,  # Using available type
                f"Positions fetched: {len(positions)} positions",
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
        raise HTTPException(status_code=500, detail=str(e))
