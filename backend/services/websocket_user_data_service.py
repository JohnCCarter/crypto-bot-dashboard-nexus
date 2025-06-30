#!/usr/bin/env python3
"""
🔐 Bitfinex User Data WebSocket Service
Hanterar autentiserade streams för order executions, balances och positioner

Detta kompletterar websocket_market_service.py med user-specifik data.
"""

import asyncio
import hashlib
import hmac
import json
import logging
from backend.services.global_nonce_manager import get_global_nonce_manager
from backend.services.bitfinex_client_wrapper import BitfinexClientWrapper
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, List, Optional

try:
    import websockets
except ImportError:
    websockets = None  # Handle missing websockets in test environments

logger = logging.getLogger(__name__)


@dataclass
class OrderFill:
    """Order execution data"""

    id: str
    order_id: str
    symbol: str
    side: str
    amount: float
    price: float
    fee: float
    timestamp: datetime


@dataclass
class LiveOrder:
    """Live order status"""

    id: str
    symbol: str
    side: str
    amount: float
    price: float
    filled: float
    remaining: float
    status: str
    timestamp: datetime


@dataclass
class LiveBalance:
    """Live balance update"""

    currency: str
    available: float
    total: float
    timestamp: datetime


@dataclass
class Position:
    """Position data"""

    symbol: str
    status: str
    amount: float
    base_price: float
    margin_funding: float
    margin_funding_type: int
    pl: float
    pl_perc: float
    price_liq: float
    leverage: float
    timestamp: datetime


@dataclass
class MarginInfo:
    """Margin trading info"""

    symbol: str
    tradable_balance: float
    gross_balance: float
    buy: float
    sell: float
    timestamp: datetime


@dataclass
class BalanceInfo:
    """Total balance info"""

    total_aum: float
    net_aum: float
    timestamp: datetime


@dataclass
class FundingOffer:
    """Funding offer data"""

    id: str
    symbol: str
    mts_create: int
    mts_update: int
    amount: float
    amount_orig: float
    offer_type: str
    flags: int
    status: str
    rate: float
    period: int
    timestamp: datetime


@dataclass
class FundingCredit:
    """Funding credit data"""

    id: str
    symbol: str
    side: int
    mts_create: int
    mts_update: int
    amount: float
    flags: int
    status: str
    rate: float
    period: int
    mts_opening: int
    mts_last_payout: int
    notify: int
    hidden: int
    renew: int
    rate_real: float
    timestamp: datetime


@dataclass
class FundingLoan:
    """Funding loan data"""

    id: str
    symbol: str
    side: int
    mts_create: int
    mts_update: int
    amount: float
    flags: int
    status: str
    rate: float
    period: int
    mts_opening: int
    mts_last_payout: int
    notify: int
    hidden: int
    renew: int
    rate_real: float
    timestamp: datetime


@dataclass
class FundingTrade:
    """Funding trade execution"""

    id: str
    symbol: str
    mts_create: int
    offer_id: str
    amount: float
    rate: float
    period: int
    maker: int
    timestamp: datetime


@dataclass
class FundingInfo:
    """Funding info update"""

    symbol: str
    yield_loan: float
    yield_lend: float
    duration_loan: float
    duration_lend: float
    timestamp: datetime


@dataclass
class Notification:
    """Notification data"""

    mts: int
    notification_type: str
    notification_info: list
    code: int
    status: str
    text: str
    timestamp: datetime


class BitfinexUserDataClient:
    """
    Klient för Bitfinex autentiserade WebSocket API.
    Hanterar användarspecifik data som order, balances och positioner.
    """

    def __init__(self, api_key: str, api_secret: str):
        """
        Initiera klienten med API-nycklar.
        
        Args:
            api_key: Bitfinex API-nyckel
            api_secret: Bitfinex API-hemlighet
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.websocket = None
        self.connected = False
        self.authenticated = False
        self.fill_callbacks = []
        self.order_callbacks = []
        self.balance_callbacks = []
        self.position_callbacks = []
        self.margin_callbacks = []
        self.notification_callbacks = []
        
        # Använd den nya BitfinexClientWrapper för WebSocket-hantering
        self.bitfinex_client = BitfinexClientWrapper(
            api_key=api_key,
            api_secret=api_secret,
            use_rest_auth=True
        )
        
        # Flagga för att indikera om vi använder wrapper eller legacy-kod
        self.use_wrapper = True

    async def connect(self):
        """Anslut till Bitfinex WebSocket API och autentisera."""
        if self.connected:
            logger.info("Redan ansluten till Bitfinex User Data WebSocket")
            return

        try:
            if self.use_wrapper:
                # Använd wrapper för att ansluta
                success = self.bitfinex_client.connect_websocket()
                if success:
                    self.connected = True
                    self.authenticated = self.bitfinex_client.is_ws_authenticated
                    
                    # Registrera callbacks för relevanta händelser
                    self._register_wrapper_callbacks()
                    
                    logger.info("Ansluten till Bitfinex User Data WebSocket via wrapper")
                    return
                else:
                    logger.error("Kunde inte ansluta till Bitfinex WebSocket via wrapper")
                    # Fallback till legacy-kod
                    self.use_wrapper = False
            
            # Legacy-kod om wrapper inte används eller misslyckas
            if not websockets:
                raise ImportError("websockets module is required")
                
            self.websocket = await websockets.connect("wss://api.bitfinex.com/ws/2")
            self.connected = True
            
            # Autentisera anslutningen
            await self._authenticate()
            
            # Starta meddelandehantering i bakgrunden
            asyncio.create_task(self._handle_messages())
            
            logger.info("Ansluten till Bitfinex User Data WebSocket")
            
        except Exception as e:
            self.connected = False
            self.authenticated = False
            logger.error(f"Fel vid anslutning till Bitfinex User Data WebSocket: {e}")
            raise

    def _register_wrapper_callbacks(self):
        """Registrera callbacks för wrapper-klienten."""
        # Registrera callbacks för olika händelsetyper
        if self.bitfinex_client:
            # Orderhantering
            self.bitfinex_client.register_ws_callback('order_new', 
                                                     self._wrapper_handle_order_new)
            self.bitfinex_client.register_ws_callback('order_update', 
                                                     self._wrapper_handle_order_update)
            self.bitfinex_client.register_ws_callback('order_cancel', 
                                                     self._wrapper_handle_order_cancel)
            
            # Trades/fills
            self.bitfinex_client.register_ws_callback('trade_execution', 
                                                     self._wrapper_handle_trade_execution)
            
            # Wallet/balances
            self.bitfinex_client.register_ws_callback('wallet_snapshot', 
                                                     self._wrapper_handle_wallet_snapshot)
            self.bitfinex_client.register_ws_callback('wallet_update', 
                                                     self._wrapper_handle_wallet_update)
            
            # Positions
            self.bitfinex_client.register_ws_callback('position_snapshot', 
                                                     self._wrapper_handle_position_snapshot)
            self.bitfinex_client.register_ws_callback('position_new', 
                                                     self._wrapper_handle_position_new)
            self.bitfinex_client.register_ws_callback('position_update', 
                                                     self._wrapper_handle_position_update)
            self.bitfinex_client.register_ws_callback('position_close', 
                                                     self._wrapper_handle_position_close)
            
            # Margin info
            self.bitfinex_client.register_ws_callback('margin_info_update', 
                                                     self._wrapper_handle_margin_info_update)
            
            # Notifications
            self.bitfinex_client.register_ws_callback('notification', 
                                                     self._wrapper_handle_notification)

    # Wrapper callback-hanterare
    def _wrapper_handle_order_new(self, data):
        """Hantera ny order via wrapper."""
        asyncio.create_task(self._handle_order_new(data))
    
    def _wrapper_handle_order_update(self, data):
        """Hantera orderuppdatering via wrapper."""
        asyncio.create_task(self._handle_order_update(data))
    
    def _wrapper_handle_order_cancel(self, data):
        """Hantera avbruten order via wrapper."""
        asyncio.create_task(self._handle_order_cancel(data))
    
    def _wrapper_handle_trade_execution(self, data):
        """Hantera trade execution via wrapper."""
        asyncio.create_task(self._handle_trade_execution(data))
    
    def _wrapper_handle_wallet_snapshot(self, data):
        """Hantera wallet snapshot via wrapper."""
        asyncio.create_task(self._handle_wallet_snapshot(data))
    
    def _wrapper_handle_wallet_update(self, data):
        """Hantera wallet update via wrapper."""
        asyncio.create_task(self._handle_wallet_update(data))
    
    def _wrapper_handle_position_snapshot(self, data):
        """Hantera position snapshot via wrapper."""
        asyncio.create_task(self._handle_position_snapshot(data))
    
    def _wrapper_handle_position_new(self, data):
        """Hantera ny position via wrapper."""
        asyncio.create_task(self._handle_position_new(data))
    
    def _wrapper_handle_position_update(self, data):
        """Hantera positionsuppdatering via wrapper."""
        asyncio.create_task(self._handle_position_update(data))
    
    def _wrapper_handle_position_close(self, data):
        """Hantera stängd position via wrapper."""
        asyncio.create_task(self._handle_position_close(data))
    
    def _wrapper_handle_margin_info_update(self, data):
        """Hantera margin info update via wrapper."""
        asyncio.create_task(self._handle_margin_info_update(data))
    
    def _wrapper_handle_notification(self, data):
        """Hantera notifikation via wrapper."""
        asyncio.create_task(self._handle_notification(data))

    async def disconnect(self):
        """Koppla från Bitfinex WebSocket API."""
        if not self.connected:
            return
            
        try:
            if self.use_wrapper and self.bitfinex_client:
                self.bitfinex_client.disconnect_websocket()
            elif self.websocket:
                await self.websocket.close()
                
            self.connected = False
            self.authenticated = False
            logger.info("Frånkopplad från Bitfinex User Data WebSocket")
        except Exception as e:
            logger.error(f"Fel vid frånkoppling från Bitfinex User Data WebSocket: {e}")

    async def _authenticate(self):
        """Authenticate WebSocket connection"""
        try:
            # Generate authentication payload using global nonce manager
            global_nonce_manager = get_global_nonce_manager()
            nonce = global_nonce_manager.get_websocket_nonce(self.api_key)
            auth_payload = f"AUTH{nonce}"
            signature = hmac.new(
                self.api_secret.encode(), auth_payload.encode(), hashlib.sha384
            ).hexdigest()

            auth_message = {
                "event": "auth",
                "apiKey": self.api_key,
                "authSig": signature,
                "authPayload": auth_payload,
                "authNonce": nonce,
            }

            await self.websocket.send(json.dumps(auth_message))

        except Exception as e:
            logger.error(f"❌ Authentication failed: {e}")

    async def _handle_messages(self):
        """Handle incoming WebSocket messages"""
        try:
            async for message in self.websocket:
                try:
                    data = json.loads(message)
                    await self._process_message(data)
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info("🔌 User data WebSocket connection closed")
        except Exception as e:
            logger.error(f"❌ Message handler error: {e}")

    async def _process_message(self, data):
        """Process incoming message and route to appropriate handler"""

        if isinstance(data, dict) and data.get("event") == "auth":
            if data.get("status") == "OK":
                self.authenticated = True
                logger.info("✅ WebSocket authentication successful")
            else:
                logger.error(f"❌ Authentication failed: {data}")
            return

        if isinstance(data, list) and len(data) >= 2:
            message_data = data[0], data[1]

            # Handle different message types
            if message_data == "hb":
                # Heartbeat
                return

            # Order executions (fills)
            if isinstance(message_data, list) and len(message_data) > 0:
                msg_type = message_data[0] if isinstance(message_data[0], str) else None

                # Trade executions
                if msg_type == "te":  # Trade execution
                    await self._handle_trade_execution(message_data[1])
                elif msg_type == "tu":  # Trade execution update
                    await self._handle_trade_execution_update(message_data[1])

                # Orders
                elif msg_type == "os":  # Order snapshot
                    await self._handle_order_snapshot(message_data[1])
                elif msg_type == "on":  # Order new
                    await self._handle_order_new(message_data[1])
                elif msg_type == "ou":  # Order update
                    await self._handle_order_update(message_data[1])
                elif msg_type == "oc":  # Order cancel
                    await self._handle_order_cancel(message_data[1])

                # Positions
                elif msg_type == "ps":  # Position snapshot
                    await self._handle_position_snapshot(message_data[1])
                elif msg_type == "pn":  # Position new
                    await self._handle_position_new(message_data[1])
                elif msg_type == "pu":  # Position update
                    await self._handle_position_update(message_data[1])
                elif msg_type == "pc":  # Position close
                    await self._handle_position_close(message_data[1])

                # Wallets
                elif msg_type == "ws":  # Wallet snapshot
                    await self._handle_wallet_snapshot(message_data[1])
                elif msg_type == "wu":  # Wallet update
                    await self._handle_wallet_update(message_data[1])

                # Balance & Margin info
                elif msg_type == "bu":  # Balance update
                    await self._handle_balance_update(message_data[1])
                elif msg_type == "miu":  # Margin info update
                    await self._handle_margin_info_update(message_data[1])

                # Funding offers
                elif msg_type == "fos":  # Funding offer snapshot
                    await self._handle_funding_offer_snapshot(message_data[1])
                elif msg_type == "fon":  # Funding offer new
                    await self._handle_funding_offer_new(message_data[1])
                elif msg_type == "fou":  # Funding offer update
                    await self._handle_funding_offer_update(message_data[1])
                elif msg_type == "foc":  # Funding offer cancel
                    await self._handle_funding_offer_cancel(message_data[1])

                # Funding credits
                elif msg_type == "fcs":  # Funding credits snapshot
                    await self._handle_funding_credits_snapshot(message_data[1])
                elif msg_type == "fcn":  # Funding credits new
                    await self._handle_funding_credits_new(message_data[1])
                elif msg_type == "fcu":  # Funding credits update
                    await self._handle_funding_credits_update(message_data[1])
                elif msg_type == "fcc":  # Funding credits close
                    await self._handle_funding_credits_close(message_data[1])

                # Funding loans
                elif msg_type == "fls":  # Funding loans snapshot
                    await self._handle_funding_loans_snapshot(message_data[1])
                elif msg_type == "fln":  # Funding loans new
                    await self._handle_funding_loans_new(message_data[1])
                elif msg_type == "flu":  # Funding loans update
                    await self._handle_funding_loans_update(message_data[1])
                elif msg_type == "flc":  # Funding loans close
                    await self._handle_funding_loans_close(message_data[1])

                # Funding trades
                elif msg_type == "fte":  # Funding trade execution
                    await self._handle_funding_trade_execution(message_data[1])
                elif msg_type == "ftu":  # Funding trade update
                    await self._handle_funding_trade_update(message_data[1])

                # Funding info
                elif msg_type == "fiu":  # Funding info update
                    await self._handle_funding_info_update(message_data[1])

                # Notifications
                elif msg_type == "n":  # Notification
                    await self._handle_notification(message_data[1])

                else:
                    logger.debug(f"🔍 Unknown message type: {msg_type}")

    async def _handle_trade_execution(self, execution_data):
        """Handle trade execution (fill) data"""
        try:
            # Bitfinex trade execution format: [ID, PAIR, MTS_CREATE, ORDER_ID, EXEC_AMOUNT, EXEC_PRICE, ...]
            if len(execution_data) >= 6:
                fill = OrderFill(
                    id=str(execution_data[0]),
                    order_id=str(execution_data[3]),
                    symbol=execution_data[1],
                    side="buy" if execution_data[4] > 0 else "sell",
                    amount=abs(float(execution_data[4])),
                    price=float(execution_data[5]),
                    fee=float(execution_data[9]) if len(execution_data) > 9 else 0.0,
                    timestamp=datetime.fromtimestamp(execution_data[2] / 1000),
                )

                # Notify all fill callbacks
                for callback in self.fill_callbacks:
                    await self._safe_callback(callback, fill)

        except Exception as e:
            logger.error(f"❌ Error processing trade execution: {e}")

    async def _handle_order_update(self, order_data):
        """Handle live order status update"""
        try:
            # Bitfinex order format: [ID, GID, CID, SYMBOL, MTS_CREATE, MTS_UPDATE, AMOUNT, AMOUNT_ORIG, TYPE, ...]
            if len(order_data) >= 16:
                order = LiveOrder(
                    id=str(order_data[0]),
                    symbol=order_data[3],
                    side="buy" if float(order_data[7]) > 0 else "sell",
                    amount=abs(float(order_data[7])),
                    price=float(order_data[16]) if order_data[16] else 0.0,
                    filled=abs(float(order_data[7])) - abs(float(order_data[6])),
                    remaining=abs(float(order_data[6])),
                    status=self._parse_order_status(order_data[13]),
                    timestamp=datetime.fromtimestamp(order_data[5] / 1000),
                )

                # Notify all order callbacks
                for callback in self.order_callbacks:
                    await self._safe_callback(callback, order)

        except Exception as e:
            logger.error(f"❌ Error processing order update: {e}")

    async def _handle_wallet_update(self, wallet_data):
        """Handle live balance update"""
        try:
            # Bitfinex wallet format: [WALLET_TYPE, CURRENCY, BALANCE, UNSETTLED_INTEREST, BALANCE_AVAILABLE]
            if len(wallet_data) >= 5:
                balance = LiveBalance(
                    currency=wallet_data[1],
                    available=float(wallet_data[4]) if wallet_data[4] else 0.0,
                    total=float(wallet_data[2]) if wallet_data[2] else 0.0,
                    timestamp=datetime.now(),
                )

                # Notify all balance callbacks
                for callback in self.balance_callbacks:
                    await self._safe_callback(callback, balance)

        except Exception as e:
            logger.error(f"❌ Error processing wallet update: {e}")

    # ==================== MISSING HANDLERS - SNAPSHOTS ====================

    async def _handle_wallet_snapshot(self, wallet_data):
        """Handle wallet snapshot (initial wallet state)"""
        try:
            # Wallet snapshot is array of wallet arrays
            if isinstance(wallet_data, list) and len(wallet_data) > 0:
                for wallet in wallet_data:
                    if len(wallet) >= 5:
                        balance = LiveBalance(
                            currency=wallet[1],
                            available=float(wallet[4]) if wallet[4] else 0.0,
                            total=float(wallet[2]) if wallet[2] else 0.0,
                            timestamp=datetime.now(),
                        )

                        # Notify all balance callbacks
                        for callback in self.balance_callbacks:
                            await self._safe_callback(callback, balance)

                logger.info(
                    f"✅ Processed wallet snapshot with {len(wallet_data)} wallets"
                )
        except Exception as e:
            logger.error(f"❌ Error processing wallet snapshot: {e}")

    async def _handle_order_snapshot(self, order_data):
        """Handle order snapshot (initial active orders)"""
        try:
            # Order snapshot is array of order arrays
            if isinstance(order_data, list) and len(order_data) > 0:
                for order_info in order_data:
                    if len(order_info) >= 16:
                        order = LiveOrder(
                            id=str(order_info[0]),
                            symbol=order_info[3],
                            side="buy" if float(order_info[7]) > 0 else "sell",
                            amount=abs(float(order_info[7])),
                            price=float(order_info[16]) if order_info[16] else 0.0,
                            filled=abs(float(order_info[7]))
                            - abs(float(order_info[6])),
                            remaining=abs(float(order_info[6])),
                            status=self._parse_order_status(order_info[13]),
                            timestamp=datetime.fromtimestamp(order_info[5] / 1000),
                        )

                        # Notify all order callbacks
                        for callback in self.order_callbacks:
                            await self._safe_callback(callback, order)

                logger.info(
                    f"✅ Processed order snapshot with {len(order_data)} orders"
                )
        except Exception as e:
            logger.error(f"❌ Error processing order snapshot: {e}")

    async def _handle_position_snapshot(self, position_data):
        """Handle position snapshot (initial positions)"""
        try:
            # Position snapshot is array of position arrays
            if isinstance(position_data, list) and len(position_data) > 0:
                for pos in position_data:
                    if len(pos) >= 11:
                        position = Position(
                            symbol=pos[0],
                            status=pos[1],
                            amount=float(pos[2]),
                            base_price=float(pos[3]),
                            margin_funding=float(pos[4]),
                            margin_funding_type=int(pos[5]),
                            pl=float(pos[6]),
                            pl_perc=float(pos[7]),
                            price_liq=float(pos[8]) if pos[8] else 0.0,
                            leverage=float(pos[9]) if pos[9] else 1.0,
                            timestamp=datetime.now(),
                        )

                        # Notify position callbacks (add to callbacks if needed)
                        if "positions" not in self.position_callbacks:
                            self.position_callbacks["positions"] = []
                        for callback in self.position_callbacks["positions"]:
                            await self._safe_callback(callback, position)

                logger.info(
                    f"✅ Processed position snapshot with {len(position_data)} positions"
                )
        except Exception as e:
            logger.error(f"❌ Error processing position snapshot: {e}")

    async def _handle_funding_offer_snapshot(self, offer_data):
        """Handle funding offer snapshot"""
        try:
            if isinstance(offer_data, list) and len(offer_data) > 0:
                for offer in offer_data:
                    if len(offer) >= 12:
                        funding_offer = FundingOffer(
                            id=str(offer[0]),
                            symbol=offer[1],
                            mts_create=int(offer[2]),
                            mts_update=int(offer[3]),
                            amount=float(offer[4]),
                            amount_orig=float(offer[5]),
                            offer_type=offer[6],
                            flags=int(offer[9]),
                            status=offer[10],
                            rate=float(offer[14]) if len(offer) > 14 else 0.0,
                            period=int(offer[15]) if len(offer) > 15 else 0,
                            timestamp=datetime.fromtimestamp(offer[2] / 1000),
                        )

                        if "funding_offers" not in self.position_callbacks:
                            self.position_callbacks["funding_offers"] = []
                        for callback in self.position_callbacks["funding_offers"]:
                            await self._safe_callback(callback, funding_offer)

                logger.info(
                    f"✅ Processed funding offer snapshot with {len(offer_data)} offers"
                )
        except Exception as e:
            logger.error(f"❌ Error processing funding offer snapshot: {e}")

    async def _handle_funding_credits_snapshot(self, credits_data):
        """Handle funding credits snapshot"""
        try:
            if isinstance(credits_data, list) and len(credits_data) > 0:
                for credit in credits_data:
                    if len(credit) >= 18:
                        funding_credit = FundingCredit(
                            id=str(credit[0]),
                            symbol=credit[1],
                            side=int(credit[2]),
                            mts_create=int(credit[3]),
                            mts_update=int(credit[4]),
                            amount=float(credit[5]),
                            flags=int(credit[6]),
                            status=credit[7],
                            rate=float(credit[11]),
                            period=int(credit[12]),
                            mts_opening=int(credit[13]),
                            mts_last_payout=int(credit[14]),
                            notify=int(credit[15]),
                            hidden=int(credit[16]),
                            renew=int(credit[18]) if len(credit) > 18 else 0,
                            rate_real=float(credit[19]) if len(credit) > 19 else 0.0,
                            timestamp=datetime.fromtimestamp(credit[3] / 1000),
                        )

                        if "funding_credits" not in self.position_callbacks:
                            self.position_callbacks["funding_credits"] = []
                        for callback in self.position_callbacks["funding_credits"]:
                            await self._safe_callback(callback, funding_credit)

                logger.info(
                    f"✅ Processed funding credits snapshot with {len(credits_data)} credits"
                )
        except Exception as e:
            logger.error(f"❌ Error processing funding credits snapshot: {e}")

    async def _handle_funding_loans_snapshot(self, loans_data):
        """Handle funding loans snapshot"""
        try:
            if isinstance(loans_data, list) and len(loans_data) > 0:
                for loan in loans_data:
                    if len(loan) >= 18:
                        funding_loan = FundingLoan(
                            id=str(loan[0]),
                            symbol=loan[1],
                            side=int(loan[2]),
                            mts_create=int(loan[3]),
                            mts_update=int(loan[4]),
                            amount=float(loan[5]),
                            flags=int(loan[6]),
                            status=loan[7],
                            rate=float(loan[11]),
                            period=int(loan[12]),
                            mts_opening=int(loan[13]),
                            mts_last_payout=int(loan[14]),
                            notify=int(loan[15]),
                            hidden=int(loan[16]),
                            renew=int(loan[18]) if len(loan) > 18 else 0,
                            rate_real=float(loan[19]) if len(loan) > 19 else 0.0,
                            timestamp=datetime.fromtimestamp(loan[3] / 1000),
                        )

                        if "funding_loans" not in self.position_callbacks:
                            self.position_callbacks["funding_loans"] = []
                        for callback in self.position_callbacks["funding_loans"]:
                            await self._safe_callback(callback, funding_loan)

                logger.info(
                    f"✅ Processed funding loans snapshot with {len(loans_data)} loans"
                )
        except Exception as e:
            logger.error(f"❌ Error processing funding loans snapshot: {e}")

    # ==================== POSITION MANAGEMENT ====================

    async def _handle_position_new(self, position_data):
        """Handle new position"""
        try:
            if len(position_data) >= 11:
                position = Position(
                    symbol=position_data[0],
                    status=position_data[1],
                    amount=float(position_data[2]),
                    base_price=float(position_data[3]),
                    margin_funding=float(position_data[4]),
                    margin_funding_type=int(position_data[5]),
                    pl=float(position_data[6]),
                    pl_perc=float(position_data[7]),
                    price_liq=float(position_data[8]) if position_data[8] else 0.0,
                    leverage=float(position_data[9]) if position_data[9] else 1.0,
                    timestamp=datetime.now(),
                )

                if "positions" not in self.position_callbacks:
                    self.position_callbacks["positions"] = []
                for callback in self.position_callbacks["positions"]:
                    await self._safe_callback(callback, position)

                logger.info(f"✅ New position: {position.symbol}")
        except Exception as e:
            logger.error(f"❌ Error processing new position: {e}")

    async def _handle_position_update(self, position_data):
        """Handle position update"""
        try:
            if len(position_data) >= 11:
                position = Position(
                    symbol=position_data[0],
                    status=position_data[1],
                    amount=float(position_data[2]),
                    base_price=float(position_data[3]),
                    margin_funding=float(position_data[4]),
                    margin_funding_type=int(position_data[5]),
                    pl=float(position_data[6]),
                    pl_perc=float(position_data[7]),
                    price_liq=float(position_data[8]) if position_data[8] else 0.0,
                    leverage=float(position_data[9]) if position_data[9] else 1.0,
                    timestamp=datetime.now(),
                )

                if "positions" not in self.position_callbacks:
                    self.position_callbacks["positions"] = []
                for callback in self.position_callbacks["positions"]:
                    await self._safe_callback(callback, position)

                logger.info(f"✅ Updated position: {position.symbol}")
        except Exception as e:
            logger.error(f"❌ Error processing position update: {e}")

    async def _handle_position_close(self, position_data):
        """Handle position close"""
        try:
            if len(position_data) >= 11:
                position = Position(
                    symbol=position_data[0],
                    status="CLOSED",
                    amount=float(position_data[2]),
                    base_price=float(position_data[3]),
                    margin_funding=float(position_data[4]),
                    margin_funding_type=int(position_data[5]),
                    pl=float(position_data[6]),
                    pl_perc=float(position_data[7]),
                    price_liq=float(position_data[8]) if position_data[8] else 0.0,
                    leverage=float(position_data[9]) if position_data[9] else 1.0,
                    timestamp=datetime.now(),
                )

                if "positions" not in self.position_callbacks:
                    self.position_callbacks["positions"] = []
                for callback in self.position_callbacks["positions"]:
                    await self._safe_callback(callback, position)

                logger.info(f"✅ Closed position: {position.symbol}")
        except Exception as e:
            logger.error(f"❌ Error processing position close: {e}")

    # ==================== MARGIN & BALANCE INFO ====================

    async def _handle_margin_info_update(self, margin_data):
        """Handle margin info update"""
        try:
            if len(margin_data) >= 5:
                margin_info = MarginInfo(
                    symbol=margin_data[0] if margin_data[0] else "BASE",
                    tradable_balance=float(margin_data[1]) if margin_data[1] else 0.0,
                    gross_balance=float(margin_data[2]) if margin_data[2] else 0.0,
                    buy=float(margin_data[3]) if margin_data[3] else 0.0,
                    sell=float(margin_data[4]) if margin_data[4] else 0.0,
                    timestamp=datetime.now(),
                )

                if "margin_info" not in self.margin_callbacks:
                    self.margin_callbacks["margin_info"] = []
                for callback in self.margin_callbacks["margin_info"]:
                    await self._safe_callback(callback, margin_info)

                logger.info(f"✅ Margin info update: {margin_info.symbol}")
        except Exception as e:
            logger.error(f"❌ Error processing margin info: {e}")

    async def _handle_balance_update(self, balance_data):
        """Handle balance info update (total/net AUM)"""
        try:
            if len(balance_data) >= 2:
                balance_info = BalanceInfo(
                    total_aum=float(balance_data[0]) if balance_data[0] else 0.0,
                    net_aum=float(balance_data[1]) if balance_data[1] else 0.0,
                    timestamp=datetime.now(),
                )

                if "balance_info" not in self.balance_callbacks:
                    self.balance_callbacks["balance_info"] = []
                for callback in self.balance_callbacks["balance_info"]:
                    await self._safe_callback(callback, balance_info)

                logger.info(f"✅ Balance update: Total AUM {balance_info.total_aum}")
        except Exception as e:
            logger.error(f"❌ Error processing balance update: {e}")

    async def _handle_funding_info_update(self, funding_data):
        """Handle funding info update"""
        try:
            if len(funding_data) >= 5:
                funding_info = FundingInfo(
                    symbol=funding_data[0] if funding_data[0] else "USD",
                    yield_loan=float(funding_data[1]) if funding_data[1] else 0.0,
                    yield_lend=float(funding_data[2]) if funding_data[2] else 0.0,
                    duration_loan=float(funding_data[3]) if funding_data[3] else 0.0,
                    duration_lend=float(funding_data[4]) if funding_data[4] else 0.0,
                    timestamp=datetime.now(),
                )

                if "funding_info" not in self.position_callbacks:
                    self.position_callbacks["funding_info"] = []
                for callback in self.position_callbacks["funding_info"]:
                    await self._safe_callback(callback, funding_info)

                logger.info(f"✅ Funding info update: {funding_info.symbol}")
        except Exception as e:
            logger.error(f"❌ Error processing funding info: {e}")

    def _parse_order_status(self, status_info):
        """Parse Bitfinex order status"""
        if not status_info:
            return "open"

        status_str = str(status_info)
        if "EXECUTED" in status_str:
            return "filled"
        elif "CANCELED" in status_str:
            return "cancelled"
        elif "PARTIALLY FILLED" in status_str:
            return "partial"
        else:
            return "open"

    async def subscribe_fills(self, callback: Callable):
        """Subscribe to order execution updates"""
        self.fill_callbacks.append(callback)
        logger.info("✅ Subscribed to order fills")

    async def subscribe_orders(self, callback: Callable):
        """Subscribe to live order status updates"""
        self.order_callbacks.append(callback)
        logger.info("✅ Subscribed to order updates")

    async def subscribe_balances(self, callback: Callable):
        """Subscribe to live balance updates"""
        self.balance_callbacks.append(callback)
        logger.info("✅ Subscribed to balance updates")

    async def _safe_callback(self, callback, data):
        """Safely execute callback with error handling"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(data)
            else:
                callback(data)
        except Exception as e:
            logger.error(f"❌ Callback error: {e}")

    # ==================== MISSING ORDER HANDLERS ====================

    async def _handle_order_new(self, order_data):
        """Handle new order (on)"""
        await self._handle_order_update(order_data)  # Same processing as update

    async def _handle_order_cancel(self, order_data):
        """Handle order cancel (oc)"""
        await self._handle_order_update(order_data)  # Same processing as update

    async def _handle_trade_execution_update(self, execution_data):
        """Handle trade execution update (tu)"""
        await self._handle_trade_execution(execution_data)  # Same processing

    # ==================== FUNDING OPERATIONS ====================

    async def _handle_funding_offer_new(self, offer_data):
        """Handle new funding offer"""
        try:
            if len(offer_data) >= 12:
                funding_offer = FundingOffer(
                    id=str(offer_data[0]),
                    symbol=offer_data[1],
                    mts_create=int(offer_data[2]),
                    mts_update=int(offer_data[3]),
                    amount=float(offer_data[4]),
                    amount_orig=float(offer_data[5]),
                    offer_type=offer_data[6],
                    flags=int(offer_data[9]),
                    status=offer_data[10],
                    rate=float(offer_data[14]) if len(offer_data) > 14 else 0.0,
                    period=int(offer_data[15]) if len(offer_data) > 15 else 0,
                    timestamp=datetime.fromtimestamp(offer_data[2] / 1000),
                )

                if "funding_offers" not in self.position_callbacks:
                    self.position_callbacks["funding_offers"] = []
                for callback in self.position_callbacks["funding_offers"]:
                    await self._safe_callback(callback, funding_offer)

                logger.info(f"✅ New funding offer: {funding_offer.id}")
        except Exception as e:
            logger.error(f"❌ Error processing new funding offer: {e}")

    async def _handle_funding_offer_update(self, offer_data):
        """Handle funding offer update"""
        await self._handle_funding_offer_new(offer_data)  # Same processing

    async def _handle_funding_offer_cancel(self, offer_data):
        """Handle funding offer cancel"""
        await self._handle_funding_offer_new(offer_data)  # Same processing

    async def _handle_funding_credits_new(self, credit_data):
        """Handle new funding credit"""
        try:
            if len(credit_data) >= 18:
                funding_credit = FundingCredit(
                    id=str(credit_data[0]),
                    symbol=credit_data[1],
                    side=int(credit_data[2]),
                    mts_create=int(credit_data[3]),
                    mts_update=int(credit_data[4]),
                    amount=float(credit_data[5]),
                    flags=int(credit_data[6]),
                    status=credit_data[7],
                    rate=float(credit_data[11]),
                    period=int(credit_data[12]),
                    mts_opening=int(credit_data[13]),
                    mts_last_payout=int(credit_data[14]),
                    notify=int(credit_data[15]),
                    hidden=int(credit_data[16]),
                    renew=int(credit_data[18]) if len(credit_data) > 18 else 0,
                    rate_real=float(credit_data[19]) if len(credit_data) > 19 else 0.0,
                    timestamp=datetime.fromtimestamp(credit_data[3] / 1000),
                )

                if "funding_credits" not in self.position_callbacks:
                    self.position_callbacks["funding_credits"] = []
                for callback in self.position_callbacks["funding_credits"]:
                    await self._safe_callback(callback, funding_credit)

                logger.info(f"✅ New funding credit: {funding_credit.id}")
        except Exception as e:
            logger.error(f"❌ Error processing new funding credit: {e}")

    async def _handle_funding_credits_update(self, credit_data):
        """Handle funding credit update"""
        await self._handle_funding_credits_new(credit_data)  # Same processing

    async def _handle_funding_credits_close(self, credit_data):
        """Handle funding credit close"""
        await self._handle_funding_credits_new(credit_data)  # Same processing

    async def _handle_funding_loans_new(self, loan_data):
        """Handle new funding loan"""
        try:
            if len(loan_data) >= 18:
                funding_loan = FundingLoan(
                    id=str(loan_data[0]),
                    symbol=loan_data[1],
                    side=int(loan_data[2]),
                    mts_create=int(loan_data[3]),
                    mts_update=int(loan_data[4]),
                    amount=float(loan_data[5]),
                    flags=int(loan_data[6]),
                    status=loan_data[7],
                    rate=float(loan_data[11]),
                    period=int(loan_data[12]),
                    mts_opening=int(loan_data[13]),
                    mts_last_payout=int(loan_data[14]),
                    notify=int(loan_data[15]),
                    hidden=int(loan_data[16]),
                    renew=int(loan_data[18]) if len(loan_data) > 18 else 0,
                    rate_real=float(loan_data[19]) if len(loan_data) > 19 else 0.0,
                    timestamp=datetime.fromtimestamp(loan_data[3] / 1000),
                )

                if "funding_loans" not in self.position_callbacks:
                    self.position_callbacks["funding_loans"] = []
                for callback in self.position_callbacks["funding_loans"]:
                    await self._safe_callback(callback, funding_loan)

                logger.info(f"✅ New funding loan: {funding_loan.id}")
        except Exception as e:
            logger.error(f"❌ Error processing new funding loan: {e}")

    async def _handle_funding_loans_update(self, loan_data):
        """Handle funding loan update"""
        await self._handle_funding_loans_new(loan_data)  # Same processing

    async def _handle_funding_loans_close(self, loan_data):
        """Handle funding loan close"""
        await self._handle_funding_loans_new(loan_data)  # Same processing

    async def _handle_funding_trade_execution(self, trade_data):
        """Handle funding trade execution"""
        try:
            if len(trade_data) >= 8:
                funding_trade = FundingTrade(
                    id=str(trade_data[0]),
                    symbol=trade_data[1],
                    mts_create=int(trade_data[2]),
                    offer_id=str(trade_data[3]),
                    amount=float(trade_data[4]),
                    rate=float(trade_data[5]),
                    period=int(trade_data[6]),
                    maker=int(trade_data[7]),
                    timestamp=datetime.fromtimestamp(trade_data[2] / 1000),
                )

                if "funding_trades" not in self.position_callbacks:
                    self.position_callbacks["funding_trades"] = []
                for callback in self.position_callbacks["funding_trades"]:
                    await self._safe_callback(callback, funding_trade)

                logger.info(f"✅ Funding trade execution: {funding_trade.id}")
        except Exception as e:
            logger.error(f"❌ Error processing funding trade: {e}")

    async def _handle_funding_trade_update(self, trade_data):
        """Handle funding trade update"""
        await self._handle_funding_trade_execution(trade_data)  # Same processing

    # ==================== NOTIFICATIONS ====================

    async def _handle_notification(self, notification_data):
        """Handle notification"""
        try:
            if len(notification_data) >= 7:
                notification = Notification(
                    mts=int(notification_data[0]),
                    notification_type=notification_data[1],
                    notification_info=(
                        notification_data[4] if len(notification_data) > 4 else []
                    ),
                    code=int(notification_data[5]) if len(notification_data) > 5 else 0,
                    status=(
                        notification_data[6] if len(notification_data) > 6 else "INFO"
                    ),
                    text=notification_data[7] if len(notification_data) > 7 else "",
                    timestamp=datetime.fromtimestamp(notification_data[0] / 1000),
                )

                if "notifications" not in self.notification_callbacks:
                    self.notification_callbacks["notifications"] = []
                for callback in self.notification_callbacks["notifications"]:
                    await self._safe_callback(callback, notification)

                logger.info(f"✅ Notification: {notification.notification_type}")
        except Exception as e:
            logger.error(f"❌ Error processing notification: {e}")


# Global instance för user data client
_user_data_client = None


async def get_user_data_client(api_key: str, api_secret: str) -> BitfinexUserDataClient:
    """Get or create global user data client"""
    global _user_data_client

    if _user_data_client is None:
        _user_data_client = BitfinexUserDataClient(api_key, api_secret)
        await _user_data_client.connect()

    return _user_data_client


async def stop_user_data_client():
    """Stop global user data client"""
    global _user_data_client

    if _user_data_client:
        await _user_data_client.disconnect()
        _user_data_client = None
