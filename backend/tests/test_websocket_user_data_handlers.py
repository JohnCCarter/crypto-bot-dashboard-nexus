#!/usr/bin/env python3
"""
🧪 Tester för alla nya WebSocket User Data handlers
Säkerställer att alla message types hanteras korrekt
"""

import os
import sys
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from backend.services.websocket_user_data_service import (
    BitfinexUserDataClient, MarginInfo, Notification, Position)

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestWebSocketUserDataHandlers:
    """Tester för alla nya message handlers"""

    @pytest.fixture
    def client(self):
        """Skapa test-klient"""
        return BitfinexUserDataClient("test_key", "test_secret")

    def test_all_handlers_exist(self, client):
        """Testa att alla handlers finns implementerade"""
        expected_handlers = [
            "_handle_wallet_snapshot",
            "_handle_order_snapshot",
            "_handle_position_snapshot",
            "_handle_funding_offer_snapshot",
            "_handle_funding_credits_snapshot",
            "_handle_funding_loans_snapshot",
            "_handle_position_new",
            "_handle_position_update",
            "_handle_position_close",
            "_handle_margin_info_update",
            "_handle_balance_update",
            "_handle_funding_info_update",
            "_handle_order_new",
            "_handle_order_cancel",
            "_handle_trade_execution_update",
            "_handle_funding_offer_new",
            "_handle_funding_offer_update",
            "_handle_funding_offer_cancel",
            "_handle_funding_credits_new",
            "_handle_funding_credits_update",
            "_handle_funding_credits_close",
            "_handle_funding_loans_new",
            "_handle_funding_loans_update",
            "_handle_funding_loans_close",
            "_handle_funding_trade_execution",
            "_handle_funding_trade_update",
            "_handle_notification",
        ]

        for handler in expected_handlers:
            assert hasattr(client, handler), f"Handler {handler} saknas"

        print(f"✅ Alla {len(expected_handlers)} handlers finns implementerade")

    def test_dataclasses_structure(self):
        """Testa att alla dataclasses har rätt struktur"""

        # Test Position
        pos = Position(
            symbol="BTCUSD",
            status="ACTIVE",
            amount=1.0,
            base_price=50000.0,
            margin_funding=0.0,
            margin_funding_type=0,
            pl=100.0,
            pl_perc=0.2,
            price_liq=45000.0,
            leverage=2.0,
            timestamp=datetime.now(),
        )
        assert pos.symbol == "BTCUSD"
        assert pos.pl == 100.0

        # Test MarginInfo
        margin = MarginInfo(
            symbol="BASE",
            tradable_balance=10000.0,
            gross_balance=15000.0,
            buy=5000.0,
            sell=5000.0,
            timestamp=datetime.now(),
        )
        assert margin.tradable_balance == 10000.0

        # Test Notification
        notif = Notification(
            mts=1640995200000,
            notification_type="ORDER_NEW",
            message_id=123,
            notification_info=[],
            code=0,
            status="SUCCESS",
            text="Order placed",
            timestamp=datetime.now(),
        )
        assert notif.notification_type == "ORDER_NEW"

        print("✅ Alla dataclasses har korrekt struktur")

    @pytest.mark.asyncio
    async def test_position_handler(self, client):
        """Testa position handlers"""

        # Mock callback
        position_callback = AsyncMock()
        client.position_callbacks = {"positions": [position_callback]}

        # Test position data (Bitfinex format)
        position_data = [
            "tBTCUSD",  # symbol
            "ACTIVE",  # status
            1.5,  # amount
            50000.0,  # base_price
            0.0,  # margin_funding
            0,  # margin_funding_type
            750.0,  # pl
            1.5,  # pl_perc
            45000.0,  # price_liq
            2.0,  # leverage
            None,  # placeholder
        ]

        # Test new position
        await client._handle_position_new(position_data)

        # Verify callback was called
        assert position_callback.call_count == 1
        position = position_callback.call_args[0][0]
        assert isinstance(position, Position)
        assert position.symbol == "tBTCUSD"
        assert position.amount == 1.5
        assert position.pl == 750.0

        print("✅ Position handlers fungerar korrekt")

    @pytest.mark.asyncio
    async def test_margin_info_handler(self, client):
        """Testa margin info handler"""

        # Mock callback
        margin_callback = AsyncMock()
        client.margin_callbacks = {"margin_info": [margin_callback]}

        # Test margin data
        margin_data = [
            "BASE",  # symbol
            8500.0,  # tradable_balance
            12000.0,  # gross_balance
            4000.0,  # buy
            4000.0,  # sell
        ]

        await client._handle_margin_info_update(margin_data)

        # Verify callback
        assert margin_callback.call_count == 1
        margin = margin_callback.call_args[0][0]
        assert isinstance(margin, MarginInfo)
        assert margin.tradable_balance == 8500.0
        assert margin.symbol == "BASE"

        print("✅ Margin info handler fungerar korrekt")

    @pytest.mark.asyncio
    async def test_notification_handler(self, client):
        """Testa notification handler"""

        # Mock callback
        notif_callback = AsyncMock()
        client.notification_callbacks = {"notifications": [notif_callback]}

        # Test notification data
        notif_data = [
            1640995200000,  # mts
            "ORDER_NEW",  # type
            12345,  # message_id
            None,  # placeholder
            [],  # notification_info
            0,  # code
            "SUCCESS",  # status
            "Order placed successfully",  # text
        ]

        await client._handle_notification(notif_data)

        # Verify callback
        assert notif_callback.call_count == 1
        notification = notif_callback.call_args[0][0]
        assert isinstance(notification, Notification)
        assert notification.notification_type == "ORDER_NEW"
        assert notification.text == "Order placed successfully"

        print("✅ Notification handler fungerar korrekt")

    def test_all_message_types_covered(self, client):
        """Testa att alla message types från Bitfinex dokumentationen täcks"""

        # Dessa är alla message types som ska hanteras enligt Bitfinex docs
        bitfinex_message_types = [
            "te",
            "tu",  # Trade executions
            "os",
            "on",
            "ou",
            "oc",  # Orders
            "ps",
            "pn",
            "pu",
            "pc",  # Positions
            "ws",
            "wu",  # Wallets
            "bu",
            "miu",  # Balance & Margin
            "fos",
            "fon",
            "fou",
            "foc",  # Funding offers
            "fcs",
            "fcn",
            "fcu",
            "fcc",  # Funding credits
            "fls",
            "fln",
            "flu",
            "flc",  # Funding loans
            "fte",
            "ftu",  # Funding trades
            "fiu",  # Funding info
            "n",  # Notifications
        ]

        # Kontrollera att varje message type har en motsvarande handler
        handler_mapping = {
            "te": "_handle_trade_execution",
            "tu": "_handle_trade_execution_update",
            "os": "_handle_order_snapshot",
            "on": "_handle_order_new",
            "ou": "_handle_order_update",
            "oc": "_handle_order_cancel",
            "ps": "_handle_position_snapshot",
            "pn": "_handle_position_new",
            "pu": "_handle_position_update",
            "pc": "_handle_position_close",
            "ws": "_handle_wallet_snapshot",
            "wu": "_handle_wallet_update",
            "bu": "_handle_balance_update",
            "miu": "_handle_margin_info_update",
            "fos": "_handle_funding_offer_snapshot",
            "fon": "_handle_funding_offer_new",
            "fou": "_handle_funding_offer_update",
            "foc": "_handle_funding_offer_cancel",
            "fcs": "_handle_funding_credits_snapshot",
            "fcn": "_handle_funding_credits_new",
            "fcu": "_handle_funding_credits_update",
            "fcc": "_handle_funding_credits_close",
            "fls": "_handle_funding_loans_snapshot",
            "fln": "_handle_funding_loans_new",
            "flu": "_handle_funding_loans_update",
            "flc": "_handle_funding_loans_close",
            "fte": "_handle_funding_trade_execution",
            "ftu": "_handle_funding_trade_update",
            "fiu": "_handle_funding_info_update",
            "n": "_handle_notification",
        }

        missing_handlers = []
        for msg_type, handler_name in handler_mapping.items():
            if not hasattr(client, handler_name):
                missing_handlers.append(f"{msg_type} -> {handler_name}")

        assert len(missing_handlers) == 0, f"Saknade handlers: {missing_handlers}"

        print(
            f"✅ Alla {len(bitfinex_message_types)} Bitfinex message types har handlers"
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
