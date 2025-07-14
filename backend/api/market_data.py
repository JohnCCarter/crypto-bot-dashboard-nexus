"""
Market Data API Routes för FastAPI
Exponerar endpoints för att hämta marknadsdata från olika exchanges
"""

import logging
import traceback
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query

from backend.api.dependencies import MarketDataDependency, get_market_data
from backend.api.models import ErrorResponse, OrderBook
from backend.services.exchange import ExchangeError
from backend.services.live_data_service_async import (
    LiveDataServiceAsync,
    get_live_data_service_async,
)

# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/market-data",
    tags=["market-data"],
)


@router.get("/ohlcv/{symbol}")
async def get_ohlcv(
    symbol: str,
    timeframe: str = Query(
        "5m", description="Candlestick timeframe (1m, 5m, 15m, 1h, etc.)"
    ),
    limit: int = Query(100, description="Number of candles to fetch"),
    live_data_service: LiveDataServiceAsync = Depends(get_live_data_service_async),
):
    """
    Get OHLCV (Open, High, Low, Close, Volume) data for a symbol.

    Args:
        symbol: Trading pair symbol (e.g., BTC/USD)
        timeframe: Candlestick timeframe (1m, 5m, 15m, 1h, etc.)
        limit: Number of candles to fetch

    Returns:
        DataFrame with OHLCV data
    """
    try:
        df = await live_data_service.fetch_live_ohlcv(symbol, timeframe, limit)

        # Convert DataFrame to dict for JSON response
        result = {
            "symbol": symbol,
            "timeframe": timeframe,
            "candles": df.reset_index().to_dict(orient="records"),
        }

        return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch OHLCV data: {str(e)}"
        )


@router.get("/ticker/{symbol}")
async def get_ticker(
    symbol: str,
    live_data_service: LiveDataServiceAsync = Depends(get_live_data_service_async),
):
    """
    Get ticker data for a symbol.

    Args:
        symbol: Trading pair symbol (e.g., BTC/USD)

    Returns:
        Ticker data
    """
    try:
        ticker = await live_data_service.fetch_live_ticker(symbol)
        return ticker
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch ticker data: {str(e)}"
        )


@router.get("/orderbook/{symbol}")
async def get_orderbook(
    symbol: str,
    limit: int = Query(20, description="Number of levels per side"),
    live_data_service: LiveDataServiceAsync = Depends(get_live_data_service_async),
):
    """
    Get orderbook data for a symbol.

    Args:
        symbol: Trading pair symbol (e.g., BTC/USD)
        limit: Number of levels per side

    Returns:
        Orderbook data
    """
    try:
        orderbook = await live_data_service.fetch_live_orderbook(symbol, limit)
        return orderbook
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch orderbook data: {str(e)}"
        )


@router.get("/market-context/{symbol}")
async def get_market_context(
    symbol: str,
    timeframe: str = Query(
        "5m", description="Candlestick timeframe (1m, 5m, 15m, 1h, etc.)"
    ),
    limit: int = Query(100, description="Number of candles to fetch"),
    live_data_service: LiveDataServiceAsync = Depends(get_live_data_service_async),
):
    """
    Get comprehensive market context for a symbol.

    Args:
        symbol: Trading pair symbol (e.g., BTC/USD)
        timeframe: Candlestick timeframe
        limit: Number of candles to fetch

    Returns:
        Market context data
    """
    try:
        context = await live_data_service.get_live_market_context(
            symbol, timeframe, limit
        )

        # Convert DataFrame to dict for JSON response
        if "ohlcv_data" in context and hasattr(context["ohlcv_data"], "reset_index"):
            context["ohlcv_data"] = (
                context["ohlcv_data"].reset_index().to_dict(orient="records")
            )

        return context
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch market context: {str(e)}"
        )


@router.get("/validate-market/{symbol}")
async def validate_market(
    symbol: str,
    timeframe: str = Query(
        "5m", description="Candlestick timeframe (1m, 5m, 15m, 1h, etc.)"
    ),
    limit: int = Query(100, description="Number of candles to fetch"),
    live_data_service: LiveDataServiceAsync = Depends(get_live_data_service_async),
):
    """
    Validate market conditions for a symbol.

    Args:
        symbol: Trading pair symbol (e.g., BTC/USD)
        timeframe: Candlestick timeframe
        limit: Number of candles to fetch

    Returns:
        Validation result
    """
    try:
        # First get market context
        context = await live_data_service.get_live_market_context(
            symbol, timeframe, limit
        )

        # Then validate
        valid, reason = await live_data_service.validate_market_conditions(context)

        return {
            "symbol": symbol,
            "valid": valid,
            "reason": reason,
            "timestamp": context.get("timestamp"),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to validate market conditions: {str(e)}"
        )


@router.get(
    "/trades/{symbol}",
    response_model=List[
        Dict[str, Any]
    ],  # Using List[Dict] instead of TradesResponse because exchange returns custom format
    responses={
        503: {"model": ErrorResponse, "description": "Exchange service not available"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def get_recent_trades(
    symbol: str = Path(..., description="Trading pair symbol"),
    limit: int = Query(50, le=1000, description="Number of trades (max: 1000)"),
    market_data: MarketDataDependency = Depends(get_market_data),
):
    """
    Get recent trades from the exchange.

    Parameters:
    -----------
    symbol: str
        Trading pair symbol
    limit: int
        Number of trades to fetch (max: 1000)

    Returns:
    --------
    List[Dict[str, Any]]
        Recent trades from the exchange
    """
    logger.info(f"🔄 [Market] Recent trades request for {symbol}")

    try:
        # Format symbol if needed
        if "/" not in symbol and len(symbol) >= 6:
            if symbol.endswith("USD"):
                base = symbol[:-3]
                quote = symbol[-3:]
                formatted_symbol = f"{base}/{quote}"
            else:
                formatted_symbol = symbol
        else:
            formatted_symbol = symbol

        logger.info(
            f"🔄 [Market] Fetching {limit} recent trades for {formatted_symbol}"
        )

        # Fetch recent trades
        trades = await market_data.fetch_recent_trades(formatted_symbol, limit)

        logger.info(f"✅ [Market] Successfully fetched {len(trades)} trades")

        return trades

    except ExchangeError as e:
        logger.error(f"❌ [Market] Exchange error for recent trades: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": f"Exchange error: {str(e)}",
                "message": "Live trades unavailable",
            },
        )
    except Exception as e:
        logger.error(f"❌ [Market] Failed to fetch recent trades: {str(e)}")
        logger.error(f"❌ [Market] Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Failed to fetch recent trades: {str(e)}",
                "message": "Live trades unavailable",
            },
        )


@router.get(
    "/markets",
    response_model=Dict[
        str, Any
    ],  # Using Dict instead of MarketsResponse because exchange returns custom format
    responses={
        503: {"model": ErrorResponse, "description": "Exchange service not available"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def get_available_markets(
    market_data: MarketDataDependency = Depends(get_market_data),
):
    """
    Get available markets from the exchange.

    Returns:
    --------
    Dict[str, Any]
        Available markets from the exchange
    """
    logger.info("🌐 [Market] Available markets request")

    try:
        # Fetch markets
        markets = await market_data.get_markets()

        logger.info(
            f"✅ [Market] Successfully fetched {len(markets['markets']) if 'markets' in markets else 0} markets"
        )

        return markets

    except ExchangeError as e:
        logger.error(f"❌ [Market] Exchange error for markets: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": f"Exchange error: {str(e)}",
                "message": "Markets unavailable",
            },
        )
    except Exception as e:
        logger.error(f"❌ [Market] Failed to fetch markets: {str(e)}")
        logger.error(f"❌ [Market] Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Failed to fetch markets: {str(e)}",
                "message": "Markets unavailable",
            },
        )
