"""
Live Market Data Service för Trading Bot Automation (Async Version)
Använder ccxt.async_support för att hämta real-time data från Bitfinex asynkront
"""

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import ccxt.async_support as ccxt_async
import pandas as pd

logger = logging.getLogger(__name__)


class LiveDataServiceAsync:
    """Asynkron service för att hämta live marknadsdata för trading bot"""

    def __init__(self, exchange_id: str = "bitfinex"):
        """
        Initialize async live data service for PUBLIC market data only.

        No API keys needed - only fetches public market data (OHLCV, ticker, orderbook).
        This eliminates nonce conflicts with authenticated services.

        Args:
            exchange_id: Exchange identifier (default: bitfinex)
        """
        self.exchange_id = exchange_id

        # Initialize exchange for PUBLIC data only (no API keys = no nonce conflicts)
        exchange_class = getattr(ccxt_async, exchange_id)
        self.exchange = exchange_class(
            {
                # NO API KEYS - only public endpoints
                "sandbox": False,  # Use live data
                "enableRateLimit": True,
                "timeout": 30000,
            }
        )

        logger.info(f"LiveDataServiceAsync initialized with {exchange_id}")

    async def fetch_live_ohlcv(
        self, symbol: str, timeframe: str = "5m", limit: int = 100
    ) -> pd.DataFrame:
        """
        Hämta live OHLCV data för trading strategies asynkront

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            timeframe: Candlestick timeframe (e.g., '1m', '5m', '1h')
            limit: Number of candles to fetch

        Returns:
            DataFrame with OHLCV data
        """
        try:
            logger.info(
                f"🔴 [LiveDataAsync] Fetching live OHLCV: {symbol} {timeframe} (limit: {limit})"
            )

            # Fetch from exchange asynchronously
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

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

            logger.info(f"✅ [LiveDataAsync] Fetched {len(df)} candles for {symbol}")
            logger.info(f"✅ [LiveDataAsync] Latest price: ${df['close'].iloc[-1]:.2f}")
            logger.info(
                f"✅ [LiveDataAsync] Price range: ${df['low'].min():.2f} - ${df['high'].max():.2f}"
            )

            return df

        except Exception as e:
            logger.error(f"❌ [LiveDataAsync] Failed to fetch OHLCV for {symbol}: {e}")
            raise

    async def fetch_live_ticker(self, symbol: str) -> Dict:
        """
        Hämta live ticker data asynkront

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')

        Returns:
            Dict with ticker information
        """
        try:
            logger.info(f"📊 [LiveDataAsync] Fetching live ticker: {symbol}")

            ticker = await self.exchange.fetch_ticker(symbol)

            logger.info(
                f"✅ [LiveDataAsync] Ticker fetched - Price: ${ticker['last']:.2f}, Volume: {ticker['baseVolume']:.4f}"
            )

            return ticker

        except Exception as e:
            logger.error(f"❌ [LiveDataAsync] Failed to fetch ticker for {symbol}: {e}")
            raise

    async def fetch_live_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """
        Hämta live orderbook asynkront

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            limit: Number of levels per side

        Returns:
            Dict with bids and asks
        """
        try:
            logger.info(
                f"📚 [LiveDataAsync] Fetching live orderbook: {symbol} (limit: {limit})"
            )

            orderbook = await self.exchange.fetch_order_book(symbol, limit)

            best_bid = orderbook["bids"][0][0] if orderbook["bids"] else 0
            best_ask = orderbook["asks"][0][0] if orderbook["asks"] else 0
            spread = best_ask - best_bid if best_bid and best_ask else 0

            logger.info(
                f"✅ [LiveDataAsync] Orderbook fetched - Bid: ${best_bid:.2f}, Ask: ${best_ask:.2f}, Spread: ${spread:.2f}"
            )

            return orderbook

        except Exception as e:
            logger.error(
                f"❌ [LiveDataAsync] Failed to fetch orderbook for {symbol}: {e}"
            )
            raise

    async def get_live_market_context(
        self, symbol: str, timeframe: str = "5m", limit: int = 100
    ) -> Dict:
        """
        Hämta komplett marknadskontext för trading beslut asynkront

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            timeframe: Candlestick timeframe
            limit: Number of candles

        Returns:
            Dict with comprehensive market data
        """
        try:
            logger.info(
                f"🎯 [LiveDataAsync] Fetching complete market context for {symbol}"
            )

            # Fetch all data in parallel with asyncio.gather
            ohlcv_task = self.fetch_live_ohlcv(symbol, timeframe, limit)
            ticker_task = self.fetch_live_ticker(symbol)
            orderbook_task = self.fetch_live_orderbook(symbol)

            # Await all tasks concurrently
            results = await asyncio.gather(
                ohlcv_task, ticker_task, orderbook_task, return_exceptions=True
            )

            ohlcv_df = results[0] if not isinstance(results[0], Exception) else None
            ticker = results[1] if not isinstance(results[1], Exception) else None
            orderbook = results[2] if not isinstance(results[2], Exception) else None

            # Handle potential failures
            if isinstance(results[0], Exception):
                logger.error(f"❌ [LiveDataAsync] OHLCV fetch failed: {results[0]}")
                raise results[0]

            if isinstance(results[1], Exception):
                logger.error(f"❌ [LiveDataAsync] Ticker fetch failed: {results[1]}")
                raise results[1]

            if isinstance(results[2], Exception):
                logger.warning(
                    f"⚠️ [LiveDataAsync] Orderbook failed for {symbol}, using fallback: {results[2]}"
                )
                # Create fallback orderbook based on ticker price
                if ticker is not None:
                    current_price = float(ticker.get("last", 0))
                    spread = current_price * 0.001  # 0.1% spread fallback
                    orderbook = {
                        "bids": [[current_price - spread / 2, 1.0]],
                        "asks": [[current_price + spread / 2, 1.0]],
                        "timestamp": ticker.get("timestamp"),
                        "datetime": ticker.get("datetime"),
                        "nonce": None,
                    }
                else:
                    # If ticker is also None, create a minimal orderbook
                    orderbook = {
                        "bids": [[0, 0]],
                        "asks": [[0, 0]],
                        "timestamp": None,
                        "datetime": None,
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

            logger.info("✅ [LiveDataAsync] Market context compiled successfully")
            logger.info(
                f"✅ [LiveDataAsync] Price: ${latest_close:.2f}, Volume: {volume_24h:.4f}, Volatility: {price_std:.2f}%"
            )

            return market_context

        except Exception as e:
            logger.error(
                f"❌ [LiveDataAsync] Failed to get market context for {symbol}: {e}"
            )
            raise

    async def validate_market_conditions(
        self, market_context: Dict
    ) -> Tuple[bool, str]:
        """
        Validera marknadsförhållanden för trading asynkront

        Args:
            market_context: Market data from get_live_market_context

        Returns:
            Tuple with validation status and reason
        """
        try:
            logger.info("✅ [LiveDataAsync] Validating market conditions")

            # Example validation: check for extreme volatility
            if market_context["volatility_pct"] > 10.0:  # 10% volatility is very high
                return (
                    False,
                    f"High volatility detected ({market_context['volatility_pct']:.2f}%) - pausing trading",
                )

            # Example validation: check spread
            spread_pct = (
                (market_context["best_ask"] - market_context["best_bid"])
                / market_context["best_ask"]
            ) * 100
            if spread_pct > 1.0:  # 1% spread threshold
                return False, f"Wide spread: {spread_pct:.2f}%"

            # Check volatility (basic check)
            if market_context["volatility_pct"] > 50:  # 50% volatility threshold
                return (
                    False,
                    f"High volatility: {market_context['volatility_pct']:.2f}%",
                )

            logger.info(
                "✅ [LiveDataAsync] Market conditions validated - safe to trade"
            )
            return True, "Market conditions are suitable for trading"

        except Exception as e:
            logger.error(
                f"❌ [LiveDataAsync] Failed to validate market conditions: {e}"
            )
            raise

    async def close(self):
        """Close the exchange connection"""
        if hasattr(self, "exchange") and self.exchange:
            await self.exchange.close()
            logger.info(f"✅ [LiveDataAsync] Closed connection to {self.exchange_id}")

    def __str__(self):
        return "Async Live Market Data Service"

    def __repr__(self):
        return f"<LiveDataServiceAsync exchange='{self.exchange_id}'>"


# Singleton instance
_live_data_service_instance: Optional[LiveDataServiceAsync] = None


async def get_live_data_service_async() -> LiveDataServiceAsync:
    """
    Get or create a singleton instance of LiveDataServiceAsync.

    Returns:
        LiveDataServiceAsync: The singleton instance
    """
    global _live_data_service_instance

    if _live_data_service_instance is None:
        _live_data_service_instance = LiveDataServiceAsync()

    return _live_data_service_instance


async def close_live_data_service_async() -> None:
    """Close the singleton instance of LiveDataServiceAsync if it exists."""
    global _live_data_service_instance

    if _live_data_service_instance is not None:
        await _live_data_service_instance.close()
        _live_data_service_instance = None
        logger.info("✅ [LiveDataAsync] Service closed and instance reset")
