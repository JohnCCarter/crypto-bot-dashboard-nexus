"""WebSocket service för live marknadsdata från Bitfinex."""

import json
import asyncio
import websockets
import logging
from typing import Callable, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class MarketData:
    """Container för marknadsdata."""

    symbol: str
    price: float
    volume: float
    timestamp: datetime
    bid: Optional[float] = None
    ask: Optional[float] = None


class BitfinexWebSocketClient:
    """WebSocket klient för Bitfinex real-time data."""

    def __init__(self):
        self.uri = "wss://api-pub.bitfinex.com/ws/2"
        self.websocket = None
        self.subscriptions = {}
        self.callbacks = {}
        self.running = False

    async def connect(self):
        """Anslut till Bitfinex WebSocket."""
        try:
            self.websocket = await websockets.connect(self.uri)
            self.running = True
            logger.info("✅ WebSocket ansluten till Bitfinex")

            # Starta message handler
            asyncio.create_task(self._handle_messages())

        except Exception as e:
            logger.error(f"❌ WebSocket anslutning misslyckades: {e}")
            raise

    async def disconnect(self):
        """Koppla från WebSocket."""
        self.running = False
        if self.websocket:
            await self.websocket.close()
            logger.info("🔌 WebSocket frånkopplad")

    async def subscribe_ticker(self, symbol: str, callback: Callable):
        """
        Prenumerera på ticker data för en symbol.

        Args:
            symbol: Trading pair (t.ex. 'BTCUSD')
            callback: Funktion som anropas när data kommer
        """
        # Bitfinex använder tBTCUSD format
        if not symbol.startswith("t"):
            symbol = f"t{symbol}"

        channel_id = f"ticker_{symbol}"
        self.callbacks[channel_id] = callback

        subscribe_msg = {"event": "subscribe", "channel": "ticker", "symbol": symbol}

        await self._send_message(subscribe_msg)
        logger.info(f"📡 Prenumererar på ticker: {symbol}")

    async def subscribe_orderbook(
        self, symbol: str, callback: Callable, precision: str = "P0"
    ):
        """
        Prenumerera på orderbook data.

        Args:
            symbol: Trading pair (t.ex. 'BTCUSD')
            callback: Funktion som anropas när data kommer
            precision: Precision level (P0, P1, P2, P3, P4)
        """
        if not symbol.startswith("t"):
            symbol = f"t{symbol}"

        channel_id = f"book_{symbol}"
        self.callbacks[channel_id] = callback

        subscribe_msg = {
            "event": "subscribe",
            "channel": "book",
            "symbol": symbol,
            "prec": precision,
            "freq": "F0",  # Real-time frequency
            "len": "25",  # 25 levels per side
        }

        await self._send_message(subscribe_msg)
        logger.info(f"📚 Prenumererar på orderbook: {symbol}")

    async def subscribe_trades(self, symbol: str, callback: Callable):
        """Prenumerera på trades data."""
        if not symbol.startswith("t"):
            symbol = f"t{symbol}"

        channel_id = f"trades_{symbol}"
        self.callbacks[channel_id] = callback

        subscribe_msg = {"event": "subscribe", "channel": "trades", "symbol": symbol}

        await self._send_message(subscribe_msg)
        logger.info(f"💱 Prenumererar på trades: {symbol}")

    async def _send_message(self, message: Dict[str, Any]):
        """Skicka meddelande till WebSocket."""
        if self.websocket:
            await self.websocket.send(json.dumps(message))

    async def _handle_messages(self):
        """Hantera inkommande meddelanden."""
        try:
            async for message in self.websocket:
                await self._process_message(json.loads(message))
        except Exception as e:
            logger.error(f"❌ WebSocket meddelande fel: {e}")
            self.running = False

    async def _process_message(self, data):
        """Processera inkommande data."""
        try:
            # Hantera olika typer av meddelanden
            if isinstance(data, dict):
                # Event meddelanden (subscriptions, etc.)
                if data.get("event") == "subscribed":
                    channel_id = f"{data['channel']}_{data['symbol']}"
                    self.subscriptions[data["chanId"]] = channel_id
                    logger.info(f"✅ Prenumeration aktiv: {channel_id}")

            elif isinstance(data, list) and len(data) >= 2:
                # Data meddelanden [CHANNEL_ID, ...]
                channel_id_num = data[0]

                if channel_id_num in self.subscriptions:
                    channel_id = self.subscriptions[channel_id_num]

                    # Ticker data
                    if channel_id.startswith("ticker_"):
                        await self._handle_ticker_data(channel_id, data[1])

                    # Orderbook data
                    elif channel_id.startswith("book_"):
                        await self._handle_orderbook_data(channel_id, data[1])

                    # Trades data
                    elif channel_id.startswith("trades_"):
                        await self._handle_trades_data(channel_id, data[1])

        except Exception as e:
            logger.error(f"❌ Fel vid processering av meddelande: {e}")

    async def _handle_ticker_data(self, channel_id: str, data):
        """Hantera ticker data."""
        try:
            if len(data) >= 10:
                # Bitfinex ticker format: [BID, BID_SIZE, ASK, ASK_SIZE, DAILY_CHANGE,
                #                         DAILY_CHANGE_PERC, LAST_PRICE, VOLUME, HIGH, LOW]
                symbol = channel_id.replace("ticker_t", "")

                market_data = MarketData(
                    symbol=symbol,
                    price=float(data[6]),  # LAST_PRICE
                    volume=float(data[7]),  # VOLUME
                    bid=float(data[0]),  # BID
                    ask=float(data[2]),  # ASK
                    timestamp=datetime.now(),
                )

                # Anropa callback
                if channel_id in self.callbacks:
                    await self._safe_callback(self.callbacks[channel_id], market_data)

        except Exception as e:
            logger.error(f"❌ Ticker data fel: {e}")

    async def _handle_orderbook_data(self, channel_id: str, data):
        """Hantera orderbook data."""
        try:
            # Bitfinex orderbook format kan vara snapshot eller update
            symbol = channel_id.replace("book_t", "")

            if isinstance(data[0], list):
                # Snapshot - array av [PRICE, COUNT, AMOUNT]
                orderbook_data = {
                    "symbol": symbol,
                    "bids": [],
                    "asks": [],
                    "timestamp": datetime.now().isoformat(),
                }

                for entry in data:
                    price, count, amount = entry
                    if amount > 0:  # Bid
                        orderbook_data["bids"].append(
                            {"price": price, "amount": amount}
                        )
                    else:  # Ask
                        orderbook_data["asks"].append(
                            {"price": price, "amount": abs(amount)}
                        )

            else:
                # Update - [PRICE, COUNT, AMOUNT]
                price, count, amount = data
                orderbook_data = {
                    "symbol": symbol,
                    "update": {
                        "price": price,
                        "count": count,
                        "amount": amount,
                        "side": "bid" if amount > 0 else "ask",
                    },
                    "timestamp": datetime.now().isoformat(),
                }

            # Anropa callback
            if channel_id in self.callbacks:
                await self._safe_callback(self.callbacks[channel_id], orderbook_data)

        except Exception as e:
            logger.error(f"❌ Orderbook data fel: {e}")

    async def _handle_trades_data(self, channel_id: str, data):
        """Hantera trades data."""
        try:
            symbol = channel_id.replace("trades_t", "")

            if isinstance(data[0], list):
                # Snapshot - array av trades
                trades = []
                for trade in data:
                    trades.append(
                        {
                            "id": trade[0],
                            "timestamp": trade[1],
                            "amount": trade[2],
                            "price": trade[3],
                        }
                    )
            else:
                # Single trade update
                trades = [
                    {
                        "id": data[0],
                        "timestamp": data[1],
                        "amount": data[2],
                        "price": data[3],
                    }
                ]

            trade_data = {
                "symbol": symbol,
                "trades": trades,
                "timestamp": datetime.now().isoformat(),
            }

            # Anropa callback
            if channel_id in self.callbacks:
                await self._safe_callback(self.callbacks[channel_id], trade_data)

        except Exception as e:
            logger.error(f"❌ Trades data fel: {e}")

    async def _safe_callback(self, callback, data):
        """Säker callback execution."""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"❌ Callback fel: {e}")


# Globala variabler för service
ws_client = None


async def start_websocket_service():
    """Starta WebSocket service."""
    global ws_client
    if not ws_client:
        ws_client = BitfinexWebSocketClient()
        await ws_client.connect()
    return ws_client


async def stop_websocket_service():
    """Stoppa WebSocket service."""
    global ws_client
    if ws_client:
        await ws_client.disconnect()
        ws_client = None


def get_websocket_client():
    """Hämta aktiv WebSocket klient."""
    return ws_client
