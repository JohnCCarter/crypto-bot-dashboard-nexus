"""
Orderbook API endpoints with live Bitfinex data - NO MOCK DATA.
"""

from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from backend.api.models import OrderBook
from backend.api.dependencies import get_market_data
from backend.services.exchange import ExchangeError
from backend.strategies.indicators import find_fvg_zones

router = APIRouter(prefix="/api", tags=["orderbook"])


class FVGRequest(BaseModel):
    """Request model for FVG calculation."""
    
    data: List[Dict[str, float]]
    min_gap_size: float = Field(default=0.0)
    direction: str = Field(default="both")


class FVGZone(BaseModel):
    """FVG zone model."""
    
    index: int
    gap_high: float
    gap_low: float
    size: float
    direction: str


@router.get("/orderbook/{symbol}", response_model=OrderBook)
async def get_orderbook(
    symbol: str,
    limit: int = Query(
        20, description="Number of levels per side", ge=1, le=100
    ),
    market_data=Depends(get_market_data),
):
    """
    Get live orderbook from Bitfinex (NO MOCK DATA).
    
    Args:
        symbol: Trading pair symbol
        limit: Number of levels per side (default: 20, max: 100)
        market_data: Market data dependency
        
    Returns:
        OrderBook: Live orderbook data
        
    Raises:
        HTTPException: If exchange service is not available or other error occurs
    """
    try:
        # Convert symbol format if needed (BTCUSD -> BTC/USD)
        if "/" not in symbol and len(symbol) >= 6:
            if symbol.endswith("USD"):
                base = symbol[:-3]
                quote = symbol[-3:]
                formatted_symbol = f"{base}/{quote}"
            else:
                formatted_symbol = symbol
        else:
            formatted_symbol = symbol
            
        orderbook = await market_data.fetch_order_book(formatted_symbol, limit)
        return orderbook
        
    except ExchangeError as e:
        detail = {
            "error": f"Exchange error: {str(e)}",
            "message": "Live orderbook unavailable - no fallback data"
        }
        raise HTTPException(status_code=503, detail=detail)
    except Exception as e:
        detail = {
            "error": f"Failed to fetch orderbook: {str(e)}",
            "message": "Live orderbook unavailable"
        }
        raise HTTPException(status_code=500, detail=detail)


@router.post("/indicators/fvg", response_model=List[FVGZone])
async def get_fvg_zones(request: FVGRequest):
    """
    Get FVG zones for given OHLCV data.
    
    Args:
        request: FVG request with OHLCV data and parameters
        
    Returns:
        List[FVGZone]: List of FVG zones
        
    Raises:
        HTTPException: If invalid input or other error occurs
    """
    try:
        import pandas as pd
        
        df = pd.DataFrame(request.data)
        zones = find_fvg_zones(
            df, 
            min_gap_size=request.min_gap_size, 
            direction=request.direction
        )
        
        return zones
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate FVG zones: {str(e)}"
        ) 