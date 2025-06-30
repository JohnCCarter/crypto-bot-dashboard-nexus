"""
Bitfinex API Client Wrapper
Integrerar det officiella Bitfinex API Python-biblioteket med vår befintliga kod
"""

import asyncio
import logging
import threading
import time
from typing import Any, Callable, Dict

from bfxapi import Client

from backend.services.global_nonce_manager import get_global_nonce_manager

logger = logging.getLogger(__name__)


class BitfinexClientWrapper:
    """
    Wrapper för Bitfinex API Python-biblioteket som integrerar med vår befintliga kod.
    Hanterar både REST API och WebSocket-anslutningar.
    """

    def __init__(
        self, api_key: str = None, api_secret: str = None, use_rest_auth: bool = True
    ):
        """
        Initialisera Bitfinex-klienten.

        Args:
            api_key: API-nyckel för autentisering
            api_secret: API-hemlighet för autentisering
            use_rest_auth: Om REST API ska använda autentisering
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.use_rest_auth = use_rest_auth

        # Registrera API-nyckeln med GlobalNonceManager
        if api_key and api_secret:
            self.nonce_manager = get_global_nonce_manager()
            self.nonce_manager.register_api_key(api_key, "BitfinexClientWrapper")

        # Skapa Bitfinex-klienten
        self.client = Client(
            api_key=api_key,
            api_secret=api_secret
        )

        # Flaggor för anslutningsstatus
        self.is_ws_connected = False
        self.is_ws_authenticated = False
        self.ws_reconnect_attempts = 0
        self.max_reconnect_attempts = 10
        self.reconnect_delay = 5  # Sekunder, ökar exponentiellt

        # Callback-funktioner för WebSocket-händelser
        self.ws_callbacks = {}

        # Registrera grundläggande WebSocket-händelser
        self._setup_ws_handlers()

        # Statistik för övervakning
        self.api_calls_count = 0
        self.ws_messages_count = 0
        self.last_api_call_time = 0
        self.last_ws_message_time = 0
        self.api_errors = []
        self.ws_errors = []

    def _setup_ws_handlers(self):
        """Konfigurera grundläggande WebSocket-händelsehanterare"""
        # Hantera anslutningshändelser
        self.client.wss.on('open', self._handle_ws_connected)
        self.client.wss.on('close', self._handle_ws_disconnected)
        self.client.wss.on('error', self._handle_ws_error)

        # Hantera autentiseringshändelser
        self.client.wss.on('auth', self._handle_ws_authenticated)
        self.client.wss.on('auth_error', self._handle_ws_auth_failed)

    def _handle_ws_connected(self, *args, **kwargs):
        """Hantera WebSocket-anslutning"""
        logger.info("Bitfinex WebSocket ansluten")
        self.is_ws_connected = True
        self.ws_reconnect_attempts = 0
        self.reconnect_delay = 5  # Återställ fördröjningen

    def _handle_ws_disconnected(self, *args, **kwargs):
        """Hantera WebSocket-frånkoppling"""
        logger.warning("Bitfinex WebSocket frånkopplad")
        self.is_ws_connected = False
        self.is_ws_authenticated = False

        # Försök återansluta med exponentiell backoff
        if self.ws_reconnect_attempts < self.max_reconnect_attempts:
            self.ws_reconnect_attempts += 1
            delay = self.reconnect_delay * (2 ** (self.ws_reconnect_attempts - 1))
            logger.info(
                f"Försöker återansluta om {delay} sekunder (försök {self.ws_reconnect_attempts}/{self.max_reconnect_attempts})..."
            )
            threading.Timer(delay, self.connect_websocket).start()
        else:
            logger.error("Maximalt antal återanslutningsförsök uppnått. Ger upp.")

    def _handle_ws_error(self, error, *args, **kwargs):
        """Hantera WebSocket-fel"""
        error_msg = str(error)
        logger.error(f"Bitfinex WebSocket fel: {error_msg}")
        self.ws_errors.append({"time": time.time(), "error": error_msg})

        # Begränsa antalet lagrade fel
        if len(self.ws_errors) > 100:
            self.ws_errors = self.ws_errors[-100:]

    def _handle_ws_authenticated(self, *args, **kwargs):
        """Hantera lyckad WebSocket-autentisering"""
        logger.info("Bitfinex WebSocket autentiserad")
        self.is_ws_authenticated = True

    def _handle_ws_auth_failed(self, error, *args, **kwargs):
        """Hantera misslyckad WebSocket-autentisering"""
        error_msg = str(error)
        logger.error(f"Bitfinex WebSocket autentiseringsfel: {error_msg}")
        self.is_ws_authenticated = False
        self.api_errors.append(
            {"time": time.time(), "type": "auth_failed", "error": error_msg}
        )

    def _get_nonce(self, service_name: str = "rest_api") -> int:
        """
        Hämta nästa nonce-värde från GlobalNonceManager

        Args:
            service_name: Namn på tjänsten som begär nonce

        Returns:
            Unikt nonce-värde
        """
        if hasattr(self, "nonce_manager") and self.api_key:
            nonce = self.nonce_manager.get_next_nonce(
                self.api_key, f"BitfinexClientWrapper_{service_name}"
            )
            logger.debug(f"Generated nonce: {nonce} for {service_name}")
            return nonce
        else:
            # Fallback om ingen nonce_manager finns
            return int(time.time() * 1000)

    async def connect_websocket_async(self):
        """Anslut till Bitfinex WebSocket API (asynkron)"""
        try:
            await self.client.wss.connect()
            if self.api_key and self.api_secret:
                # Använd GlobalNonceManager för WebSocket-autentisering
                nonce = self.nonce_manager.get_websocket_nonce(self.api_key)
                # Autentisera med WebSocket
                await self.client.wss.auth()
            return True
        except Exception as e:
            logger.error(f"Fel vid anslutning till Bitfinex WebSocket: {e}")
            self.ws_errors.append(
                {"time": time.time(), "type": "connect_error", "error": str(e)}
            )
            return False

    def connect_websocket(self):
        """Anslut till Bitfinex WebSocket API (synkron wrapper)"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(self.connect_websocket_async())
        except Exception as e:
            logger.error(f"Fel vid synkron WebSocket-anslutning: {e}")
            return False
        finally:
            loop.close()

    def disconnect_websocket(self):
        """Koppla från Bitfinex WebSocket API"""
        if self.is_ws_connected:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.client.wss.close())
                self.is_ws_connected = False
                self.is_ws_authenticated = False
                return True
            except Exception as e:
                logger.error(f"Fel vid frånkoppling från Bitfinex WebSocket: {e}")
                return False
            finally:
                loop.close()
        return True

    def register_ws_callback(self, event_type: str, callback: Callable):
        """
        Registrera en callback-funktion för en WebSocket-händelse

        Args:
            event_type: Typ av händelse ('ticker', 'trades', 'book', etc.)
            callback: Callback-funktion som anropas när händelsen inträffar
        """
        self.client.wss.on(event_type, callback)
        self.ws_callbacks[event_type] = callback
        logger.info(f"Registrerade callback för WebSocket-händelse: {event_type}")

    def subscribe_to_channel(self, channel: str, symbol: str = None, **kwargs):
        """
        Prenumerera på en WebSocket-kanal

        Args:
            channel: Kanalnamn ('ticker', 'trades', 'book', etc.)
            symbol: Valutapar (t.ex. 'tBTCUSD')
            **kwargs: Ytterligare parametrar för prenumerationen
        """
        if not self.is_ws_connected:
            logger.warning("Kan inte prenumerera på kanal, WebSocket är inte ansluten")
            return False

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            params = {"channel": channel}
            if symbol:
                params["symbol"] = symbol
            params.update(kwargs)

            loop.run_until_complete(self.client.wss.subscribe(**params))
            logger.info(
                f"Prenumererade på kanal: {channel} för {symbol or 'alla symboler'}"
            )
            return True
        except Exception as e:
            logger.error(f"Fel vid prenumeration på kanal {channel}: {e}")
            return False
        finally:
            loop.close()

    def place_order(
        self, symbol: str, amount: float, price: float, order_type: str = "LIMIT"
    ) -> Dict[str, Any]:
        """
        Placera en order

        Args:
            symbol: Valutapar (t.ex. 'tBTCUSD')
            amount: Mängd att köpa/sälja (positivt för köp, negativt för sälj)
            price: Pris per enhet
            order_type: Ordertyp ('LIMIT', 'MARKET', etc.)

        Returns:
            Ordersvar från API:et
        """
        try:
            # Använd asynkron API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Uppdaterad för version 3.0.4
            result = loop.run_until_complete(
                self.client.rest.auth.submit_order(
                    symbol=symbol,
                    price=str(price),
                    amount=str(amount),
                    market_type=order_type
                )
            )
            
            self.api_calls_count += 1
            self.last_api_call_time = time.time()
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Fel vid placering av order: {error_msg}")
            self.api_errors.append(
                {"time": time.time(), "type": "place_order", "error": error_msg}
            )
            return {"error": error_msg}
        finally:
            loop.close()

    def get_order_status(self, order_id: int) -> Dict[str, Any]:
        """
        Hämta status för en order

        Args:
            order_id: Order-ID att hämta status för

        Returns:
            Orderstatus från API:et
        """
        try:
            # Använd asynkron API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Uppdaterad för version 3.0.4
            result = loop.run_until_complete(
                self.client.rest.auth.orders(id=order_id)
            )
            
            self.api_calls_count += 1
            self.last_api_call_time = time.time()
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Fel vid hämtning av orderstatus: {error_msg}")
            self.api_errors.append(
                {"time": time.time(), "type": "get_order_status", "error": error_msg}
            )
            return {"error": error_msg}
        finally:
            loop.close()

    def get_active_orders(self) -> Dict[str, Any]:
        """
        Hämta aktiva ordrar

        Returns:
            Aktiva ordrar från API:et
        """
        try:
            # Använd asynkron API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Uppdaterad för version 3.0.4
            result = loop.run_until_complete(
                self.client.rest.auth.active_orders()
            )
            
            self.api_calls_count += 1
            self.last_api_call_time = time.time()
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Fel vid hämtning av aktiva ordrar: {error_msg}")
            self.api_errors.append(
                {"time": time.time(), "type": "get_active_orders", "error": error_msg}
            )
            return {"error": error_msg}
        finally:
            loop.close()

    def cancel_order(self, order_id: int) -> Dict[str, Any]:
        """
        Avbryt en order

        Args:
            order_id: Order-ID att avbryta

        Returns:
            Svar från API:et
        """
        try:
            # Använd asynkron API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Uppdaterad för version 3.0.4
            result = loop.run_until_complete(
                self.client.rest.auth.cancel_order(id=order_id)
            )
            
            self.api_calls_count += 1
            self.last_api_call_time = time.time()
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Fel vid avbrytning av order: {error_msg}")
            self.api_errors.append(
                {"time": time.time(), "type": "cancel_order", "error": error_msg}
            )
            return {"error": error_msg}
        finally:
            loop.close()

    def get_wallet_balances(self) -> Dict[str, Any]:
        """
        Hämta plånbokssaldon

        Returns:
            Plånbokssaldon från API:et
        """
        try:
            # Använd asynkron API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Uppdaterad för version 3.0.4
            result = loop.run_until_complete(
                self.client.rest.auth.wallets()
            )
            
            self.api_calls_count += 1
            self.last_api_call_time = time.time()
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Fel vid hämtning av plånbokssaldon: {error_msg}")
            self.api_errors.append(
                {"time": time.time(), "type": "get_wallet_balances", "error": error_msg}
            )
            return {"error": error_msg}
        finally:
            loop.close()

    def get_positions(self) -> Dict[str, Any]:
        """
        Hämta öppna positioner

        Returns:
            Öppna positioner från API:et
        """
        try:
            # Använd asynkron API
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Uppdaterad för version 3.0.4
            result = loop.run_until_complete(
                self.client.rest.auth.positions()
            )
            
            self.api_calls_count += 1
            self.last_api_call_time = time.time()
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Fel vid hämtning av positioner: {error_msg}")
            self.api_errors.append(
                {"time": time.time(), "type": "get_positions", "error": error_msg}
            )
            return {"error": error_msg}
        finally:
            loop.close()

    def get_ticker(self, symbol: str) -> Dict[str, Any]:
        """
        Hämta ticker för ett valutapar

        Args:
            symbol: Valutapar (t.ex. 'tBTCUSD')

        Returns:
            Ticker från API:et
        """
        try:
            # Uppdaterad för version 3.0.4 - inte asynkron i den nya versionen
            result = self.client.rest.public.get_t_ticker(symbol=symbol)
            
            self.api_calls_count += 1
            self.last_api_call_time = time.time()
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Fel vid hämtning av ticker: {error_msg}")
            self.api_errors.append(
                {"time": time.time(), "type": "get_ticker", "error": error_msg}
            )
            return {"error": error_msg}

    def get_order_book(
        self, symbol: str, precision: str = "P0", length: int = 25
    ) -> Dict[str, Any]:
        """
        Hämta orderbok för ett valutapar

        Args:
            symbol: Valutapar (t.ex. 'tBTCUSD')
            precision: Precision för orderboken ('P0', 'P1', 'P2', 'P3', 'P4')
            length: Antal nivåer att hämta

        Returns:
            Orderbok från API:et
        """
        try:
            # Uppdaterad för version 3.0.4 - inte asynkron i den nya versionen
            result = self.client.rest.public.get_book(
                symbol=symbol, precision=precision, len=str(length)
            )
            
            self.api_calls_count += 1
            self.last_api_call_time = time.time()
            return result
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Fel vid hämtning av orderbok: {error_msg}")
            self.api_errors.append(
                {"time": time.time(), "type": "get_order_book", "error": error_msg}
            )
            return {"error": error_msg}

    def get_status(self) -> Dict[str, Any]:
        """
        Hämta status för klienten

        Returns:
            Status för klienten
        """
        return {
            "is_ws_connected": self.is_ws_connected,
            "is_ws_authenticated": self.is_ws_authenticated,
            "api_calls_count": self.api_calls_count,
            "ws_messages_count": self.ws_messages_count,
            "last_api_call_time": self.last_api_call_time,
            "last_ws_message_time": self.last_ws_message_time,
            "api_errors": self.api_errors[-5:],  # Bara de 5 senaste felen
            "ws_errors": self.ws_errors[-5:],  # Bara de 5 senaste felen
            "ws_reconnect_attempts": self.ws_reconnect_attempts,
        }
