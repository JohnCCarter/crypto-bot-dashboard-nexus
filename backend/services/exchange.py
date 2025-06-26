"""Exchange service for cryptocurrency trading."""

import threading
import time
from datetime import datetime
from typing import Any, Dict, Optional

import ccxt


class CustomBitfinex(ccxt.bitfinex):
    """Custom Bitfinex class with enhanced thread-safe nonce handling."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Start with millisecond precision as per Bitfinex official docs
        self._last_nonce = round(datetime.now().timestamp() * 1000)
        self._nonce_lock = threading.Lock()

    def nonce(self):
        """
        Generate thread-safe monotonically increasing nonce for Bitfinex API.

        Uses Bitfinex official method: round(datetime.now().timestamp() * 1000)
        This ensures millisecond precision as required by Bitfinex API.
        """
        with self._nonce_lock:
            # Use Bitfinex official nonce method: milliseconds since Unix epoch
            now_milliseconds = round(datetime.now().timestamp() * 1000)

            # Ensure nonce always increments with minimum gap
            if now_milliseconds <= self._last_nonce:
                # If current time is not ahead, add minimum increment (1ms)
                self._last_nonce += 1
            else:
                # Use current time but ensure increment from last nonce
                self._last_nonce = max(now_milliseconds, self._last_nonce + 1)

            return self._last_nonce


class ExchangeError(Exception):
    """Base exception for exchange-related errors."""

    pass


class ExchangeService:
    """Service for interacting with cryptocurrency exchanges."""

    def __init__(self, exchange_id: str, api_key: str, api_secret: str):
        """
        Initialize exchange service.

        Args:
            exchange_id: Exchange identifier (e.g. 'binance')
            api_key: Exchange API key
            api_secret: Exchange API secret
        """
        try:
            # Use custom Bitfinex class for proper nonce handling
            if exchange_id == "bitfinex":
                exchange_class = CustomBitfinex
            else:
                exchange_class = getattr(ccxt, exchange_id)

            self.exchange = exchange_class(
                {
                    "apiKey": api_key,
                    "secret": api_secret,
                    "enableRateLimit": True,
                    "rateLimit": 2000,  # 2 seconds between requests
                    "options": {
                        "adjustForTimeDifference": True,
                    },
                }
            )
        except Exception as e:
            raise ExchangeError(f"Failed to initialize exchange: {str(e)}")

    def create_order(
        self,
        symbol: str,
        order_type: str,
        side: str,
        amount: float,
        price: Optional[float] = None,
        position_type: str = "spot",
    ) -> Dict[str, Any]:
        """
        Create a new order on the exchange.

        Args:
            symbol: Trading pair (e.g. 'BTC/USD')
            order_type: 'market' or 'limit'
            side: 'buy' or 'sell'
            amount: Order size
            price: Required for limit orders
            position_type: 'margin' or 'spot'

        Returns:
            Dict containing order details

        Raises:
            ExchangeError: If order creation fails
        """
        try:
            params = {}
            if order_type == "limit" and price is None:
                raise ValueError("Price is required for limit orders")

            # Configure for margin vs spot trading on Bitfinex
            if hasattr(self.exchange, "id") and self.exchange.id == "bitfinex":
                # Check if this is paper trading
                if self.is_paper_trading():
                    # Paper trading: Use simple parameters
                    # Don't use EXCHANGE prefixes or complex params
                    params = {}  # Keep it simple for paper trading
                else:
                    # Live trading: Use full Bitfinex parameters
                    if position_type == "margin":
                        # Bitfinex margin trading parameters
                        params["type"] = "EXCHANGE MARGIN"
                        params["hidden"] = False
                        params["postonly"] = False
                    else:
                        # Bitfinex spot trading parameters (default)
                        if order_type == "limit":
                            params["type"] = "EXCHANGE LIMIT"
                        else:
                            params["type"] = "EXCHANGE MARKET"
                        params["hidden"] = False
                        params["postonly"] = False

            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=amount,
                price=price,
                params=params,
            )

            return {
                "id": order["id"],
                "symbol": order["symbol"],
                "type": order["type"],
                "side": order["side"],
                "amount": float(order["amount"]),
                "price": float(order.get("price", 0)),
                "status": order["status"],
                "filled": float(order.get("filled", 0)),
                "remaining": float(order.get("remaining", amount)),
                "position_type": position_type,  # Include position type
                "timestamp": order.get(
                    "timestamp", int(datetime.utcnow().timestamp() * 1000)
                ),
            }

        except Exception as e:
            raise ExchangeError(f"Failed to create order: {str(e)}")

    def fetch_order(self, order_id: str, symbol: str) -> Dict[str, Any]:
        """
        Fetch order details from exchange.

        Args:
            order_id: Exchange order ID
            symbol: Trading pair

        Returns:
            Dict containing order details

        Raises:
            ExchangeError: If order fetch fails
        """
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            # Safe float conversion with None checks
            amount = float(order["amount"]) if order.get("amount") else 0.0
            price = float(order["price"]) if order.get("price") else 0.0
            filled = float(order["filled"]) if order.get("filled") else 0.0
            remaining = float(order["remaining"]) if order.get("remaining") else 0.0

            return {
                "id": order["id"],
                "symbol": order["symbol"],
                "type": order["type"],
                "side": order["side"],
                "amount": amount,
                "price": price,
                "status": order["status"],
                "filled": filled,
                "remaining": remaining,
                "timestamp": order.get(
                    "timestamp", int(datetime.utcnow().timestamp() * 1000)
                ),
            }
        except Exception as e:
            raise ExchangeError(f"Failed to fetch order: {str(e)}")

    def cancel_order(self, order_id: str, symbol: Optional[str] = None) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: Exchange order ID
            symbol: Trading pair (optional for some exchanges)

        Returns:
            True if order was cancelled

        Raises:
            ExchangeError: If order cancellation fails
        """
        try:
            self.exchange.cancel_order(order_id, symbol)
            return True
        except Exception as e:
            raise ExchangeError(f"Failed to cancel order: {str(e)}")

    def fetch_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch current market data for a symbol.

        Args:
            symbol: Trading pair

        Returns:
            Dict containing market data

        Raises:
            ExchangeError: If ticker fetch fails
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return {
                "symbol": ticker["symbol"],
                "last": float(ticker["last"]),
                "bid": float(ticker["bid"]),
                "ask": float(ticker["ask"]),
                "volume": float(ticker["baseVolume"]),
                "timestamp": ticker["timestamp"],
            }
        except Exception as e:
            raise ExchangeError(f"Failed to fetch ticker: {str(e)}")

    def fetch_balance(self) -> Dict[str, float]:
        """
        Fetch account balance with retry mechanism for nonce issues.

        Returns:
            Dict mapping currency to balance

        Raises:
            ExchangeError: If balance fetch fails after retries
        """
        max_retries = 3
        base_delay = 0.5  # Start with 500ms delay

        for attempt in range(max_retries):
            try:
                balance = self.exchange.fetch_balance()
                result = {}

                # Handle different balance structure formats
                if "total" in balance and isinstance(balance["total"], dict):
                    # Standard CCXT format with nested structure
                    for currency, amount in balance["total"].items():
                        if isinstance(amount, dict) and "free" in amount:
                            free_amount = float(amount["free"])
                        else:
                            free_amount = float(amount)

                        if free_amount > 0:
                            result[currency] = free_amount
                else:
                    # Direct format or other structures
                    for currency, data in balance.items():
                        if currency in ["info", "datetime", "timestamp"]:
                            continue

                        if isinstance(data, dict):
                            if "free" in data:
                                free_amount = float(data["free"])
                            elif "total" in data:
                                free_amount = float(data["total"])
                            else:
                                free_amount = float(data.get("available", 0))
                        else:
                            free_amount = float(data)

                        if free_amount > 0:
                            result[currency] = free_amount

                return result

            except Exception as e:
                error_msg = str(e).lower()

                # Check if it's a nonce error
                if "nonce" in error_msg and attempt < max_retries - 1:
                    delay = base_delay * (2**attempt)  # Exponential backoff
                    print(
                        f"🔄 Nonce error on attempt {attempt + 1}, retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    continue

                # If not a nonce error or max retries reached, raise the error
                raise ExchangeError(f"Failed to fetch balance: {str(e)}")

    def fetch_ohlcv(self, symbol: str, timeframe: str = "5m", limit: int = 100) -> list:
        """
        Fetch OHLCV (candlestick) data from exchange.

        Args:
            symbol: Trading pair (e.g. 'BTC/USD')
            timeframe: Timeframe (e.g. '1m', '5m', '1h', '1d')
            limit: Number of candles to fetch

        Returns:
            List of OHLCV data [timestamp, open, high, low, close, volume]

        Raises:
            ExchangeError: If OHLCV fetch fails
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            return [
                {
                    "timestamp": candle[0],
                    "open": float(candle[1]),
                    "high": float(candle[2]),
                    "low": float(candle[3]),
                    "close": float(candle[4]),
                    "volume": float(candle[5]),
                }
                for candle in ohlcv
            ]
        except Exception as e:
            raise ExchangeError(f"Failed to fetch OHLCV data: {str(e)}")

    def fetch_order_book(self, symbol: str, limit: int = 20) -> Dict[str, Any]:
        """
        Fetch order book data from exchange.

        Args:
            symbol: Trading pair (e.g. 'BTC/USD')
            limit: Number of levels to fetch for each side

        Returns:
            Dict containing bids and asks

        Raises:
            ExchangeError: If order book fetch fails
        """
        try:
            # Special handling for Bitfinex orderbook
            if hasattr(self.exchange, "id") and self.exchange.id == "bitfinex":
                # Bitfinex requires different limit handling
                # Try without limit first, then apply client-side limiting
                orderbook = self.exchange.fetch_order_book(symbol)
            else:
                # Standard CCXT implementation for other exchanges
                orderbook = self.exchange.fetch_order_book(symbol, limit)

            # Apply limit on client side to ensure consistency
            limited_bids = orderbook["bids"][:limit] if orderbook["bids"] else []
            limited_asks = orderbook["asks"][:limit] if orderbook["asks"] else []

            return {
                "symbol": symbol,
                "bids": [
                    {"price": float(bid[0]), "amount": float(bid[1])}
                    for bid in limited_bids
                ],
                "asks": [
                    {"price": float(ask[0]), "amount": float(ask[1])}
                    for ask in limited_asks
                ],
                "timestamp": orderbook.get(
                    "timestamp", int(datetime.utcnow().timestamp() * 1000)
                ),
            }
        except Exception as e:
            raise ExchangeError(f"Failed to fetch order book: {str(e)}")

    def fetch_recent_trades(self, symbol: str, limit: int = 50) -> list:
        """
        Fetch recent trades from exchange.

        Args:
            symbol: Trading pair (e.g. 'BTC/USD')
            limit: Number of trades to fetch

        Returns:
            List of recent trades

        Raises:
            ExchangeError: If trades fetch fails
        """
        try:
            trades = self.exchange.fetch_trades(symbol, limit=limit)
            return [
                {
                    "id": trade["id"],
                    "symbol": trade["symbol"],
                    "side": trade["side"],
                    "amount": float(trade["amount"]),
                    "price": float(trade["price"]),
                    "timestamp": trade["timestamp"],
                }
                for trade in trades
            ]
        except Exception as e:
            raise ExchangeError(f"Failed to fetch recent trades: {str(e)}")

    def fetch_positions(self, symbols: Optional[list] = None) -> list:
        """
        Fetch current positions from exchange.

        Args:
            symbols: Optional list of symbols to filter by

        Returns:
            List of position dictionaries

        Raises:
            ExchangeError: If positions fetch fails
        """
        try:
            positions = self.exchange.fetch_positions(symbols)

            # Process all positions (including Bitfinex margin positions)
            active_positions = []
            for position in positions:
                # Get position size - handle different exchange formats
                size = position.get("size")
                amount = position.get("amount")
                notional = position.get("notional", 0)

                # For Bitfinex: sometimes size is None but notional contains amount
                if size is None and amount is None:
                    # Check if this is a Bitfinex margin position with notional
                    if notional != 0:
                        # Use notional as amount for Bitfinex margin positions
                        actual_amount = float(notional)
                    else:
                        # Try to extract from info array for Bitfinex
                        info = position.get("info", [])
                        if isinstance(info, list) and len(info) > 2:
                            try:
                                actual_amount = float(info[2])  # Amount is at index 2
                            except (ValueError, IndexError):
                                actual_amount = 0
                        else:
                            actual_amount = 0
                else:
                    actual_amount = float(size or amount or 0)

                # Only include positions with non-zero amounts
                if actual_amount != 0:
                    # Get mark price - try different sources
                    mark_price = position.get("markPrice")
                    if mark_price is None:
                        mark_price = position.get("lastPrice", 0)

                    active_positions.append(
                        {
                            "id": position.get("id", ""),
                            "symbol": position["symbol"],
                            "side": position["side"],  # 'long' or 'short'
                            "amount": actual_amount,
                            "entry_price": float(position.get("entryPrice", 0)),
                            "mark_price": float(mark_price or 0),
                            "pnl": float(position.get("unrealizedPnl", 0)),
                            "pnl_percentage": float(position.get("percentage", 0)),
                            "timestamp": position.get(
                                "timestamp", int(datetime.utcnow().timestamp() * 1000)
                            ),
                            "contracts": float(position.get("contracts") or 0),
                            "notional": float(position.get("notional") or 0),
                            "collateral": float(position.get("collateral") or 0),
                            "margin_mode": position.get("marginMode", "isolated"),
                            "maintenance_margin": float(
                                position.get("maintenanceMargin") or 0
                            ),
                            "position_type": "margin",  # Mark as real margin position
                            "leverage": float(position.get("leverage") or 1.0),
                        }
                    )

            return active_positions

        except Exception as e:
            raise ExchangeError(f"Failed to fetch positions: {str(e)}")

    def is_paper_trading(self) -> bool:
        """
        Detect if this is a paper trading account.

        Returns:
            True if paper trading, False if live trading
        """
        try:
            # For Bitfinex, check account info to determine if it's paper trading
            if hasattr(self.exchange, "id") and self.exchange.id == "bitfinex":
                balance = self.exchange.fetch_balance()
                info = balance.get("info", [])

                # Primary check: Look for TEST currency prefixes in balance
                # Paper trading accounts use TESTUSD, TESTBTC, etc.
                if isinstance(info, list) and len(info) > 0:
                    for account_info in info:
                        if isinstance(account_info, list) and len(account_info) >= 2:
                            currency = str(account_info[1])
                            if currency.startswith("TEST"):
                                return True

                # Secondary check: Look for TEST currencies in balance currencies
                for currency in balance.keys():
                    if isinstance(currency, str) and currency.startswith("TEST"):
                        return True

                # Fallback check: limited markets available in paper trading
                markets = self.exchange.load_markets()
                spot_pairs = sum(
                    bool(market.get("spot", False) and market.get("active", False))
                    for market in markets.values()
                )

                # Live Bitfinex typically has 300+ spot pairs, paper has ~18
                if spot_pairs <= 50:  # Conservative threshold
                    return True

            return False

        except Exception:
            # If detection fails, assume live trading for safety
            return False

    def get_trading_limitations(self) -> Dict[str, Any]:
        """
        Hämta trading limitations för Bitfinex (t.ex. minsta orderstorlek)
        """
        try:
            self.exchange.load_markets()

            # Kolla om vi är i paper trading-läge
            # Beroende på exchange kan detta behöva anpassas
            if "paper" in self.exchange.options.get("urls", {}).get("api", ""):
                # Sätt manuella begränsningar för paper trading
                return {
                    "min_order_size": {"BTC/USD": 0.0002, "ETH/USD": 0.005},
                    "max_leverage": 10.0,
                    "supported_position_types": ["spot", "margin"],
                }

            # Hämta live-begränsningar för riktig trading
            if hasattr(self.exchange, "id") and self.exchange.id == "bitfinex":
                # Bitfinex specific limitations
                return {
                    "is_paper_trading": False,
                    "margin_trading_available": True,
                    "supported_order_types": ["spot", "margin", "perpetual", "futures"],
                    "limitations": [],
                }
            else:
                # Standard CCXT implementation for other exchanges
                return {
                    "is_paper_trading": False,
                    "margin_trading_available": True,
                    "supported_order_types": ["spot", "margin", "perpetual", "futures"],
                    "limitations": [],
                }

        except Exception as e:
            raise ExchangeError(f"Failed to get trading limitations: {str(e)}")

    def get_markets(self) -> Dict[str, Any]:
        """
        Get available trading markets from exchange.

        Returns:
            Dict containing available markets

        Raises:
            ExchangeError: If markets fetch fails
        """
        try:
            markets = self.exchange.load_markets()
            return {
                symbol: {
                    "base": market["base"],
                    "quote": market["quote"],
                    "active": market["active"],
                    "type": market["type"],
                    "spot": market.get("spot", True),
                    "margin": market.get("margin", False),
                    "future": market.get("future", False),
                    "option": market.get("option", False),
                    "contract": market.get("contract", False),
                }
                for symbol, market in markets.items()
                if market["active"]
            }
        except Exception as e:
            raise ExchangeError(f"Failed to fetch markets: {str(e)}")

    def fetch_order_history(
        self,
        symbols: Optional[list] = None,
        since: Optional[int] = None,
        limit: int = 100,
    ) -> list:
        """
        Fetch order history from exchange using supported methods.

        Args:
            symbols: Optional list of symbols to filter by
            since: Optional timestamp (in milliseconds) to fetch orders from
            limit: Maximum number of orders to return (default 100)

        Returns:
            List of order dictionaries

        Raises:
            ExchangeError: If order history fetch fails
        """
        try:
            # Bitfinex doesn't support fetchOrders(), use fetchClosedOrders() instead
            if hasattr(self.exchange, "id") and self.exchange.id == "bitfinex":
                # Use fetchClosedOrders() for Bitfinex (supported method)
                all_orders = []

                if symbols:
                    # Fetch closed orders for each symbol
                    for symbol in symbols:
                        try:
                            orders = self.exchange.fetch_closed_orders(
                                symbol, since, limit
                            )
                            all_orders.extend(orders)
                        except Exception as e:
                            # Log error but continue with other symbols
                            print(f"Warning: Could not fetch orders for {symbol}: {e}")
                            continue
                else:
                    # Fetch all closed orders
                    all_orders = self.exchange.fetch_closed_orders(None, since, limit)
            else:
                # Use standard fetchOrders for other exchanges
                if symbols:
                    all_orders = []
                    for symbol in symbols:
                        orders = self.exchange.fetch_orders(symbol, since, limit)
                        all_orders.extend(orders)
                else:
                    all_orders = self.exchange.fetch_orders(None, since, limit)

            # Transform to standardized format
            standardized_orders = []
            for order in all_orders:
                # Safely handle None values in order data
                fee_data = order.get("fee") or {}
                standardized_order = {
                    "id": order.get("id", ""),
                    "symbol": order.get("symbol", ""),
                    "order_type": order.get("type", ""),
                    "side": order.get("side", ""),
                    "amount": float(order.get("amount") or 0),
                    "price": float(order.get("price") or 0),
                    "fee": float(
                        fee_data.get("cost") if isinstance(fee_data, dict) else 0
                    ),
                    "timestamp": order.get("timestamp") or 0,
                    "datetime": order.get("datetime") or "",
                    "status": order.get("status", ""),
                    "filled": float(order.get("filled") or 0),
                    "remaining": float(order.get("remaining") or 0),
                    "cost": float(order.get("cost") or 0),
                    "trades": order.get("trades", []),
                }
                standardized_orders.append(standardized_order)

            # Sort by timestamp (newest first)
            standardized_orders.sort(key=lambda x: x["timestamp"] or 0, reverse=True)

            return standardized_orders

        except Exception as e:
            raise ExchangeError(f"Failed to fetch order history: {str(e)}")

    def fetch_open_orders(self, symbol: Optional[str] = None) -> list:
        """
        Fetch open orders from exchange.

        Args:
            symbol: Optional trading pair to filter by

        Returns:
            List of open order dictionaries

        Raises:
            ExchangeError: If open orders fetch fails
        """
        try:
            # Fetch open orders from exchange
            open_orders = self.exchange.fetch_open_orders(symbol)

            # Transform to standardized format
            standardized_orders = []
            for order in open_orders:
                standardized_order = {
                    "id": order["id"],
                    "symbol": order["symbol"],
                    "order_type": order["type"],
                    "side": order["side"],
                    "amount": float(order["amount"]),
                    "price": float(order["price"] or 0),
                    "status": order["status"],
                    "filled": float(order["filled"]),
                    "remaining": float(order["remaining"]),
                    "timestamp": order["timestamp"],
                    "datetime": order["datetime"],
                }
                standardized_orders.append(standardized_order)

            return standardized_orders

        except Exception as e:
            error_msg = str(e)
            # Handle nonce-specific errors with retry suggestion
            if "nonce" in error_msg.lower() and "small" in error_msg.lower():
                raise ExchangeError(
                    f"Bitfinex nonce error: {error_msg}. "
                    "Try waiting a few seconds before retrying."
                )
            raise ExchangeError(f"Failed to fetch open orders: {error_msg}")
