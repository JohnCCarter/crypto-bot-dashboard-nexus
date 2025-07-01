"""
Market data API endpoints for FastAPI.

These endpoints provide access to live market data from the exchange.
"""

import logging
import traceback
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Path

from backend.api.models import (
    ErrorResponse,
    OHLCVResponse,
    OrderBook,
    Ticker,
    TradesResponse
)
from backend.api.dependencies import get_market_data, MarketDataDependency
from backend.services.exchange import ExchangeError

# Create logger
logger = logging.getLogger(__name__)

# Create router
router = APIRouter(
    prefix="/api/market",
    tags=["market-data"],
)


@router.get(
    "/ohlcv/{symbol}",
    response_model=OHLCVResponse,
    responses={
        503: {"model": ErrorResponse, "description": "Exchange service not available"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_live_ohlcv(
    symbol: str = Path(..., description="Trading pair symbol"),
    timeframe: str = Query("5m", description="Timeframe ('1m', '5m', '15m', '1h', '1d')"),
    limit: int = Query(100, le=1000, description="Number of candles (max: 1000)"),
    market_data: MarketDataDependency = Depends(get_market_data)
):
    """
    Get live OHLCV data from the exchange.
    
    Parameters:
    -----------
    symbol: str
        Trading pair symbol
    timeframe: str
        Timeframe for OHLCV data ('1m', '5m', '15m', '1h', '1d')
    limit: int
        Number of candles to fetch (max: 1000)
        
    Returns:
    --------
    OHLCVResponse
        OHLCV data from the exchange
    """
    logger.info(f"📊 [Market] Live OHLCV request for {symbol}")
    
    try:
        # Format symbol if needed
        if "/" not in symbol and len(symbol) >= 6:
            # Convert BTCUSD to BTC/USD format
            if symbol.endswith("USD"):
                base = symbol[:-3]
                quote = symbol[-3:]
                formatted_symbol = f"{base}/{quote}"
            else:
                formatted_symbol = symbol
        else:
            formatted_symbol = symbol
        
        logger.info(
            f"📊 [Market] Fetching {limit} {timeframe} candles for {formatted_symbol}"
        )
        
        # Fetch OHLCV data
        ohlcv_data = await market_data.fetch_ohlcv(
            formatted_symbol, timeframe, limit
        )
        
        logger.info(
            f"✅ [Market] Successfully fetched {len(ohlcv_data)} candles"
        )
        
        return {"data": ohlcv_data}
    
    except ExchangeError as e:
        logger.error(f"❌ [Market] Exchange error: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": f"Exchange error: {str(e)}",
                "message": "Live market data unavailable"
            }
        )
    except Exception as e:
        logger.error(f"❌ [Market] Failed to fetch OHLCV: {str(e)}")
        logger.error(f"❌ [Market] Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch OHLCV data: {str(e)}"
        )


@router.get(
    "/orderbook/{symbol}",
    response_model=OrderBook,
    responses={
        503: {"model": ErrorResponse, "description": "Exchange service not available"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_live_orderbook(
    symbol: str = Path(..., description="Trading pair symbol"),
    limit: int = Query(20, le=100, description="Number of levels per side (max: 100)"),
    market_data: MarketDataDependency = Depends(get_market_data)
):
    """
    Get live order book from the exchange.
    
    Parameters:
    -----------
    symbol: str
        Trading pair symbol
    limit: int
        Number of levels per side (max: 100)
        
    Returns:
    --------
    OrderBook
        Order book data from the exchange
    """
    logger.info(f"📋 [Market] Live orderbook request for {symbol}")
    
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
            f"📋 [Market] Fetching orderbook for {formatted_symbol} with limit {limit}"
        )
        
        # Fetch order book
        orderbook = await market_data.fetch_order_book(formatted_symbol, limit)
        
        logger.info(
            f"✅ [Market] Successfully fetched orderbook with "
            f"{len(orderbook['bids'])} bids, {len(orderbook['asks'])} asks"
        )
        
        return orderbook
    
    except ExchangeError as e:
        logger.error(f"❌ [Market] Exchange error for orderbook: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": f"Exchange error: {str(e)}",
                "message": "Live orderbook unavailable - no fallback data"
            }
        )
    except Exception as e:
        logger.error(f"❌ [Market] Failed to fetch orderbook: {str(e)}")
        logger.error(f"❌ [Market] Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Failed to fetch orderbook: {str(e)}",
                "message": "Live orderbook unavailable"
            }
        )


@router.get(
    "/ticker/{symbol}",
    response_model=Dict[str, Any],  # Using Dict instead of Ticker because exchange returns custom format
    responses={
        503: {"model": ErrorResponse, "description": "Exchange service not available"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_live_ticker(
    symbol: str = Path(..., description="Trading pair symbol"),
    market_data: MarketDataDependency = Depends(get_market_data)
):
    """
    Get live ticker data from the exchange.
    
    Parameters:
    -----------
    symbol: str
        Trading pair symbol
        
    Returns:
    --------
    Dict[str, Any]
        Ticker data from the exchange
    """
    logger.info(f"💰 [Market] Live ticker request for {symbol}")
    
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
            f"💰 [Market] Fetching ticker for {formatted_symbol}"
        )
        
        # Fetch ticker
        ticker = await market_data.fetch_ticker(formatted_symbol)
        
        logger.info(
            f"✅ [Market] Successfully fetched ticker for {formatted_symbol}"
        )
        
        return ticker
    
    except ExchangeError as e:
        logger.error(f"❌ [Market] Exchange error for ticker: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": f"Exchange error: {str(e)}",
                "message": "Live ticker unavailable"
            }
        )
    except Exception as e:
        logger.error(f"❌ [Market] Failed to fetch ticker: {str(e)}")
        logger.error(f"❌ [Market] Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Failed to fetch ticker: {str(e)}",
                "message": "Live ticker unavailable"
            }
        )


@router.get(
    "/trades/{symbol}",
    response_model=List[Dict[str, Any]],  # Using List[Dict] instead of TradesResponse because exchange returns custom format
    responses={
        503: {"model": ErrorResponse, "description": "Exchange service not available"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_recent_trades(
    symbol: str = Path(..., description="Trading pair symbol"),
    limit: int = Query(50, le=1000, description="Number of trades (max: 1000)"),
    market_data: MarketDataDependency = Depends(get_market_data)
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
        
        logger.info(
            f"✅ [Market] Successfully fetched {len(trades)} trades"
        )
        
        return trades
    
    except ExchangeError as e:
        logger.error(f"❌ [Market] Exchange error for recent trades: {str(e)}")
        raise HTTPException(
            status_code=503,
            detail={
                "error": f"Exchange error: {str(e)}",
                "message": "Live trades unavailable"
            }
        )
    except Exception as e:
        logger.error(f"❌ [Market] Failed to fetch recent trades: {str(e)}")
        logger.error(f"❌ [Market] Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Failed to fetch recent trades: {str(e)}",
                "message": "Live trades unavailable"
            }
        )


@router.get(
    "/markets",
    response_model=Dict[str, Any],  # Using Dict instead of MarketsResponse because exchange returns custom format
    responses={
        503: {"model": ErrorResponse, "description": "Exchange service not available"},
        500: {"model": ErrorResponse, "description": "Server error"}
    }
)
async def get_available_markets(
    market_data: MarketDataDependency = Depends(get_market_data)
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
                "message": "Markets unavailable"
            }
        )
    except Exception as e:
        logger.error(f"❌ [Market] Failed to fetch markets: {str(e)}")
        logger.error(f"❌ [Market] Stack trace: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": f"Failed to fetch markets: {str(e)}",
                "message": "Markets unavailable"
            }
        ) 