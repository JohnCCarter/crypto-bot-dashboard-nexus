"""Trading limitations API endpoints for FastAPI."""

from typing import Any, Dict

from fastapi import APIRouter, Depends

from backend.api.dependencies import get_exchange_service_async
from backend.services.exchange import ExchangeService

# Create router
router = APIRouter(prefix="/api", tags=["trading-limitations"])


@router.get("/trading-limitations")
async def get_trading_limitations(
    exchange_service: ExchangeService = Depends(get_exchange_service_async)
) -> Dict[str, Any]:
    """
    Get trading limitations for current account type.

    Returns:
        Dict: Trading limitations info
    """
    try:
        if not exchange_service:
            # Return safe defaults on error
            return {
                "is_paper_trading": False,
                "margin_trading_available": True,
                "supported_order_types": ["spot", "margin"],
                "limitations": [],
            }

        limitations = exchange_service.get_trading_limitations()
        return limitations

    except Exception:
        # Return safe defaults on error
        return {
            "is_paper_trading": False,
            "margin_trading_available": True,
            "supported_order_types": ["spot", "margin"],
            "limitations": [],
        } 