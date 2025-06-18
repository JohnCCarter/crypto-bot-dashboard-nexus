"""Exchange service for cryptocurrency trading."""

from datetime import datetime
from typing import Any, Dict, Optional

import ccxt


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
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class(
                {"apiKey": api_key, "secret": api_secret, "enableRateLimit": True}
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
    ) -> Dict[str, Any]:
        """
        Create a new order on the exchange.

        Args:
            symbol: Trading pair (e.g. 'BTC/USD')
            order_type: 'market' or 'limit'
            side: 'buy' or 'sell'
            amount: Order size
            price: Required for limit orders

        Returns:
            Dict containing order details

        Raises:
            ExchangeError: If order creation fails
        """
        try:
            params = {}
            if order_type == "limit" and price is None:
                raise ValueError("Price is required for limit orders")

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
            return {
                "id": order["id"],
                "symbol": order["symbol"],
                "type": order["type"],
                "side": order["side"],
                "amount": float(order["amount"]),
                "price": float(order.get("price", 0)),
                "status": order["status"],
                "filled": float(order.get("filled", 0)),
                "remaining": float(order.get("remaining", 0)),
                "timestamp": order.get(
                    "timestamp", int(datetime.utcnow().timestamp() * 1000)
                ),
            }
        except Exception as e:
            raise ExchangeError(f"Failed to fetch order: {str(e)}")

    def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: Exchange order ID
            symbol: Trading pair

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
        Fetch account balance.

        Returns:
            Dict mapping currency to balance

        Raises:
            ExchangeError: If balance fetch fails
        """
        try:
            balance = self.exchange.fetch_balance()
            return {
                currency: float(data["free"])
                for currency, data in balance["total"].items()
                if float(data["free"]) > 0
            }
        except Exception as e:
            raise ExchangeError(f"Failed to fetch balance: {str(e)}")

    def fetch_ohlcv(self, symbol: str, timeframe: str = '5m', limit: int = 100) -> list:
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
                    "volume": float(candle[5])
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
            orderbook = self.exchange.fetch_order_book(symbol, limit)
            return {
                "symbol": symbol,
                "bids": [
                    {"price": float(bid[0]), "amount": float(bid[1])}
                    for bid in orderbook["bids"][:limit]
                ],
                "asks": [
                    {"price": float(ask[0]), "amount": float(ask[1])}
                    for ask in orderbook["asks"][:limit]
                ],
                "timestamp": orderbook.get("timestamp", int(datetime.utcnow().timestamp() * 1000))
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
                    "timestamp": trade["timestamp"]
                }
                for trade in trades
            ]
        except Exception as e:
            raise ExchangeError(f"Failed to fetch recent trades: {str(e)}")

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
                    "contract": market.get("contract", False)
                }
                for symbol, market in markets.items()
                if market["active"]
            }
        except Exception as e:
            raise ExchangeError(f"Failed to fetch markets: {str(e)}")
