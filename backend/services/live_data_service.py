"""
Live Market Data Service för Trading Bot Automation
Använder ccxt för att hämta real-time data från Bitfinex
"""

import ccxt
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import asyncio
import json

logger = logging.getLogger(__name__)


class LiveDataService:
    """Service för att hämta live marknadsdata för trading bot"""

    def __init__(
        self, exchange_id: str = "bitfinex", api_key: str = None, api_secret: str = None
    ):
        """
        Initialize live data service

        Args:
            exchange_id: Exchange identifier (default: bitfinex)
            api_key: API key for authenticated requests (optional)
            api_secret: API secret for authenticated requests (optional)
        """
        self.exchange_id = exchange_id

        # Initialize exchange
        exchange_class = getattr(ccxt, exchange_id)
        self.exchange = exchange_class(
            {
                "apiKey": api_key,
                "secret": api_secret,
                "sandbox": False,  # Use live data
                "enableRateLimit": True,
                "timeout": 30000,
            }
        )

        logger.info(f"LiveDataService initialized with {exchange_id}")

    def fetch_live_ohlcv(
        self, symbol: str, timeframe: str = "5m", limit: int = 100
    ) -> pd.DataFrame:
        """
        Hämta live OHLCV data för trading strategies

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            timeframe: Candlestick timeframe (e.g., '1m', '5m', '1h')
            limit: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data
        """
        try:
            logger.info(
                f"🔴 [LiveData] Fetching live OHLCV: {symbol} {timeframe} (limit: {limit})"
            )

            # Fetch from exchange
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            if not ohlcv:
                raise ValueError(f"No OHLCV data received for {symbol}")

            # Convert to DataFrame
            df = pd.DataFrame(
                ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"]
            )

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
            df.set_index("timestamp", inplace=True)

            # Ensure numeric types
            for col in ["open", "high", "low", "close", "volume"]:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            logger.info(f"✅ [LiveData] Fetched {len(df)} candles for {symbol}")
            logger.info(f"✅ [LiveData] Latest price: ${df['close'].iloc[-1]:.2f}")
            logger.info(
                f"✅ [LiveData] Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}"
            )

            return df

        except Exception as e:
            logger.error(f"❌ [LiveData] Failed to fetch OHLCV for {symbol}: {e}")
            raise

    def fetch_live_ticker(self, symbol: str) -> Dict:
        """
        Hämta live ticker data

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')

        Returns:
            Dict with ticker information
        """
        try:
            logger.info(f"📊 [LiveData] Fetching live ticker: {symbol}")

            ticker = self.exchange.fetch_ticker(symbol)

            logger.info(
                f"✅ [LiveData] Ticker fetched - Price: ${ticker['last']:.2f}, Volume: {ticker['baseVolume']:.4f}"
            )

            return ticker

        except Exception as e:
            logger.error(f"❌ [LiveData] Failed to fetch ticker for {symbol}: {e}")
            raise

    def fetch_live_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """
        Hämta live orderbook

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            limit: Number of levels per side

        Returns:
            Dict with bids and asks
        """
        try:
            logger.info(
                f"📚 [LiveData] Fetching live orderbook: {symbol} (limit: {limit})"
            )

            orderbook = self.exchange.fetch_order_book(symbol, limit)

            best_bid = orderbook["bids"][0][0] if orderbook["bids"] else 0
            best_ask = orderbook["asks"][0][0] if orderbook["asks"] else 0
            spread = best_ask - best_bid if best_bid and best_ask else 0

            logger.info(
                f"✅ [LiveData] Orderbook fetched - Bid: ${best_bid:.2f}, Ask: ${best_ask:.2f}, Spread: ${spread:.2f}"
            )

            return orderbook

        except Exception as e:
            logger.error(f"❌ [LiveData] Failed to fetch orderbook for {symbol}: {e}")
            raise

    def get_live_market_context(
        self, symbol: str, timeframe: str = "5m", limit: int = 100
    ) -> Dict:
        """
        Hämta komplett marknadskontext för trading beslut

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            timeframe: Candlestick timeframe
            limit: Number of candles

        Returns:
            Dict with comprehensive market data
        """
        try:
            logger.info(f"🎯 [LiveData] Fetching complete market context for {symbol}")

            # Fetch all data in parallel would be better, but keeping simple for now
            ohlcv_df = self.fetch_live_ohlcv(symbol, timeframe, limit)
            ticker = self.fetch_live_ticker(symbol)

            # Try to fetch orderbook, use fallback for paper trading
            try:
                orderbook = self.fetch_live_orderbook(symbol)
            except Exception as e:
                logger.warning(
                    f"⚠️ [LiveData] Orderbook failed for {symbol}, using fallback: {e}"
                )
                # Create fallback orderbook based on ticker price
                current_price = float(ticker.get("last", 0))
                spread = current_price * 0.001  # 0.1% spread fallback
                orderbook = {
                    "bids": [[current_price - spread / 2, 1.0]],
                    "asks": [[current_price + spread / 2, 1.0]],
                    "timestamp": ticker.get("timestamp"),
                    "datetime": ticker.get("datetime"),
                    "nonce": None,
                }

            # Calculate additional metrics
            latest_close = float(ohlcv_df["close"].iloc[-1])
            volume_24h = float(ticker.get("baseVolume", 0))

            # Price change calculations
            price_change_24h = ticker.get("change", 0)
            price_change_pct = ticker.get("percentage", 0)

            # Volatility (simple calculation)
            price_std = float(ohlcv_df["close"].pct_change().std() * 100)

            market_context = {
                "symbol": symbol,
                "timestamp": datetime.now().isoformat(),
                "ohlcv_data": ohlcv_df,
                "current_price": latest_close,
                "ticker": ticker,
                "orderbook": orderbook,
                "best_bid": orderbook["bids"][0][0] if orderbook["bids"] else 0,
                "best_ask": orderbook["asks"][0][0] if orderbook["asks"] else 0,
                "spread": (
                    orderbook["asks"][0][0] - orderbook["bids"][0][0]
                    if orderbook["bids"] and orderbook["asks"]
                    else 0
                ),
                "volume_24h": volume_24h,
                "price_change_24h": price_change_24h,
                "price_change_pct": price_change_pct,
                "volatility_pct": price_std,
                "market_cap": None,  # Would need additional API call
                "data_quality": {
                    "ohlcv_rows": len(ohlcv_df),
                    "orderbook_levels": len(orderbook["bids"]) + len(orderbook["asks"]),
                    "ticker_complete": bool(ticker.get("last")),
                    "data_freshness_seconds": 0,  # Real-time
                },
            }

            logger.info(f"✅ [LiveData] Market context compiled successfully")
            logger.info(
                f"✅ [LiveData] Price: ${latest_close:.2f}, Volume: {volume_24h:.4f}, Volatility: {price_std:.2f}%"
            )

            return market_context

        except Exception as e:
            logger.error(
                f"❌ [LiveData] Failed to get market context for {symbol}: {e}"
            )
            raise

    def validate_market_conditions(self, market_context: Dict) -> Tuple[bool, str]:
        """
        Validera marknadsförhållanden för trading

        Args:
            market_context: Market data from get_live_market_context

        Returns:
            Tuple of (is_valid, reason)
        """
        try:
            # Check data quality
            quality = market_context["data_quality"]

            if quality["ohlcv_rows"] < 50:
                return False, f"Insufficient OHLCV data: {quality['ohlcv_rows']} rows"

            if quality["orderbook_levels"] < 10:
                return False, f"Thin orderbook: {quality['orderbook_levels']} levels"

            if not quality["ticker_complete"]:
                return False, "Incomplete ticker data"

            # Check spread (shouldn't be too wide)
            spread_pct = (
                market_context["spread"] / market_context["current_price"]
            ) * 100
            if spread_pct > 1.0:  # 1% spread threshold
                return False, f"Wide spread: {spread_pct:.2f}%"

            # Check volatility (basic check)
            if market_context["volatility_pct"] > 50:  # 50% volatility threshold
                return (
                    False,
                    f"High volatility: {market_context['volatility_pct']:.2f}%",
                )

            logger.info(f"✅ [LiveData] Market conditions validated - safe to trade")
            return True, "Market conditions are suitable for trading"

        except Exception as e:
            logger.error(f"❌ [LiveData] Market validation failed: {e}")
            return False, f"Validation error: {e}"

    def __str__(self):
        return f"LiveDataService(exchange={self.exchange_id})"

    def __repr__(self):
        return self.__str__()
