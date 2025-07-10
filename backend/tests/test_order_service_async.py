"""
Optimerade tester för OrderServiceAsync.

Denna testfil använder optimerad testmetodik för att testa OrderServiceAsync
med korrekt hantering av asynkrona funktioner och mockade dependencies.
"""

import asyncio
import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from backend.services.exchange import ExchangeService
from backend.services.order_service_async import OrderServiceAsync


# Skapa en mock för ExchangeService istället för en egen klass
@pytest.fixture
def mock_exchange_service():
    """Skapa en mockad ExchangeService."""
    mock = MagicMock(spec=ExchangeService)

    # Konfigurera mock-metoder
    mock.create_order.return_value = {
        "id": "1",
        "symbol": "BTC/USD",
        "type": "limit",
        "side": "buy",
        "amount": 1.0,
        "price": 50000.0,
        "status": "open",
        "filled": 0.0,
        "remaining": 1.0,
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
    }

    mock.fetch_order.return_value = {
        "id": "1",
        "symbol": "BTC/USD",
        "type": "limit",
        "side": "buy",
        "amount": 1.0,
        "price": 50000.0,
        "status": "open",
        "filled": 0.0,
        "remaining": 1.0,
        "timestamp": int(datetime.utcnow().timestamp() * 1000),
    }

    mock.cancel_order.return_value = True

    mock.fetch_open_orders.return_value = []

    return mock


@pytest.fixture
def order_service_async(mock_exchange_service):
    """Skapa en OrderServiceAsync med mockad ExchangeService."""
    return OrderServiceAsync(mock_exchange_service)


# === Tester för OrderServiceAsync ===


@pytest.mark.asyncio
async def test_place_order(order_service_async, mock_exchange_service):
    """Test för att placera en order."""
    # Arrange
    order_data = {
        "symbol": "BTC/USD",
        "order_type": "limit",
        "side": "buy",
        "amount": 1.0,
        "price": 50000.0,
    }

    # Patcha create_order_async för att använda den mockade exchange_service
    with patch(
        "backend.services.order_service_async.create_order_async"
    ) as mock_create_order:
        mock_create_order.return_value = {
            "id": "1",
            "symbol": "BTC/USD",
            "type": "limit",
            "side": "buy",
            "amount": 1.0,
            "price": 50000.0,
            "status": "open",
            "filled": 0.0,
            "remaining": 1.0,
        }

        # Act
        order = await order_service_async.place_order(order_data)

        # Assert
        assert order["symbol"] == "BTC/USD"
        assert order["type"] == "limit"
        assert order["side"] == "buy"
        assert order["amount"] == 1.0
        assert order["price"] == 50000.0
        assert order["status"] == "open"
        assert "id" in order

        # Verify that create_order_async was called with correct parameters
        mock_create_order.assert_called_once()
        args, kwargs = mock_create_order.call_args
        assert kwargs["exchange"] == mock_exchange_service
        assert kwargs["symbol"] == "BTC/USD"
        assert kwargs["order_type"] == "limit"
        assert kwargs["side"] == "buy"
        assert kwargs["amount"] == 1.0
        assert kwargs["price"] == 50000.0


@pytest.mark.asyncio
async def test_get_order_status(order_service_async, mock_exchange_service):
    """Test för att hämta orderstatus."""
    # Arrange
    # Först skapa en order
    order_data = {
        "symbol": "BTC/USD",
        "order_type": "limit",
        "side": "buy",
        "amount": 1.0,
        "price": 50000.0,
    }

    # Patcha create_order_async och fetch_order_async
    with patch(
        "backend.services.order_service_async.create_order_async"
    ) as mock_create_order, patch(
        "backend.services.order_service_async.fetch_order_async"
    ) as mock_fetch_order:

        mock_create_order.return_value = {
            "id": "1",
            "symbol": "BTC/USD",
            "type": "limit",
            "side": "buy",
            "amount": 1.0,
            "price": 50000.0,
            "status": "open",
            "filled": 0.0,
            "remaining": 1.0,
        }

        mock_fetch_order.return_value = {
            "id": "1",
            "symbol": "BTC/USD",
            "type": "limit",
            "side": "buy",
            "amount": 1.0,
            "price": 50000.0,
            "status": "open",
            "filled": 0.0,
            "remaining": 1.0,
        }

        # Skapa ordern
        order = await order_service_async.place_order(order_data)
        order_id = order["id"]

        # Act
        order_status = await order_service_async.get_order_status(order_id)

        # Assert
        assert order_status["id"] == order_id
        assert order_status["status"] == "open"

        # Verify that fetch_order_async was called with correct parameters
        mock_fetch_order.assert_called_once()
        args, kwargs = mock_fetch_order.call_args
        assert kwargs["exchange"] == mock_exchange_service
        assert kwargs["order_id"] == order["exchange_order_id"]
        assert kwargs["symbol"] == "BTC/USD"


@pytest.mark.asyncio
async def test_get_order_status_not_found(order_service_async):
    """Test för att hämta orderstatus för en order som inte finns."""
    # Act
    order_status = await order_service_async.get_order_status("non-existent-id")

    # Assert
    assert order_status is None


@pytest.mark.asyncio
async def test_cancel_order(order_service_async, mock_exchange_service):
    """Test för att avbryta en order."""
    # Arrange
    # Först skapa en order
    order_data = {
        "symbol": "BTC/USD",
        "order_type": "limit",
        "side": "buy",
        "amount": 1.0,
        "price": 50000.0,
    }

    # Patcha create_order_async och cancel_order_async
    with patch(
        "backend.services.order_service_async.create_order_async"
    ) as mock_create_order, patch(
        "backend.services.order_service_async.cancel_order_async"
    ) as mock_cancel_order:

        mock_create_order.return_value = {
            "id": "1",
            "symbol": "BTC/USD",
            "type": "limit",
            "side": "buy",
            "amount": 1.0,
            "price": 50000.0,
            "status": "open",
            "filled": 0.0,
            "remaining": 1.0,
        }

        mock_cancel_order.return_value = True

        # Skapa ordern
        order = await order_service_async.place_order(order_data)
        order_id = order["id"]

        # Act
        result = await order_service_async.cancel_order(order_id)

        # Assert
        assert result is True

        # Verify order status
        order_status = await order_service_async.get_order_status(order_id)
        assert order_status["status"] == "cancelled"

        # Verify that cancel_order_async was called with correct parameters
        mock_cancel_order.assert_called_once()
        args, kwargs = mock_cancel_order.call_args
        assert kwargs["exchange"] == mock_exchange_service
        assert kwargs["order_id"] == order["exchange_order_id"]
        assert kwargs["symbol"] == "BTC/USD"


@pytest.mark.asyncio
async def test_cancel_order_not_found(order_service_async):
    """Test för att avbryta en order som inte finns."""
    # Act
    result = await order_service_async.cancel_order("non-existent-id")

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_get_open_orders(order_service_async, mock_exchange_service):
    """Test för att hämta öppna ordrar."""
    # Arrange
    # Rensa tidigare ordrar
    order_service_async.orders = {}

    # Patcha create_order_async och fetch_open_orders_async
    with patch(
        "backend.services.order_service_async.create_order_async"
    ) as mock_create_order, patch(
        "backend.services.order_service_async.fetch_open_orders_async"
    ) as mock_fetch_open_orders:

        # Konfigurera mock för create_order_async
        def create_order_side_effect(exchange, symbol, order_type, side, amount, price):
            return {
                "id": f"{symbol}_{side}",
                "symbol": symbol,
                "type": order_type,
                "side": side,
                "amount": amount,
                "price": price,
                "status": "open",
                "filled": 0.0,
                "remaining": amount,
            }

        mock_create_order.side_effect = create_order_side_effect

        # Konfigurera mock för fetch_open_orders_async
        mock_fetch_open_orders.return_value = [
            {
                "id": "BTC/USD_buy",
                "symbol": "BTC/USD",
                "type": "limit",
                "side": "buy",
                "amount": 1.0,
                "price": 50000.0,
                "status": "open",
                "filled": 0.0,
                "remaining": 1.0,
            },
            {
                "id": "ETH/USD_sell",
                "symbol": "ETH/USD",
                "type": "limit",
                "side": "sell",
                "amount": 2.0,
                "price": 3000.0,
                "status": "open",
                "filled": 0.0,
                "remaining": 2.0,
            },
        ]

        # Skapa några ordrar
        order_data1 = {
            "symbol": "BTC/USD",
            "order_type": "limit",
            "side": "buy",
            "amount": 1.0,
            "price": 50000.0,
        }
        order_data2 = {
            "symbol": "ETH/USD",
            "order_type": "limit",
            "side": "sell",
            "amount": 2.0,
            "price": 3000.0,
        }

        await order_service_async.place_order(order_data1)
        await order_service_async.place_order(order_data2)

        # Act
        open_orders = await order_service_async.get_open_orders()

        # Assert
        assert len(open_orders) == 2

        # Test filtrering på symbol
        with patch(
            "backend.services.order_service_async.fetch_open_orders_async"
        ) as mock_fetch_filtered:
            mock_fetch_filtered.return_value = [
                {
                    "id": "BTC/USD_buy",
                    "symbol": "BTC/USD",
                    "type": "limit",
                    "side": "buy",
                    "amount": 1.0,
                    "price": 50000.0,
                    "status": "open",
                    "filled": 0.0,
                    "remaining": 1.0,
                }
            ]

            btc_orders = await order_service_async.get_open_orders("BTC/USD")
            assert len(btc_orders) == 1
            assert btc_orders[0]["symbol"] == "BTC/USD"

            mock_fetch_filtered.assert_called_once_with(
                exchange=mock_exchange_service, symbol="BTC/USD"
            )


@pytest.mark.asyncio
async def test_place_order_validation_error(order_service_async):
    """Test för att placera en order med ogiltiga data."""
    # Arrange
    invalid_order_data = {
        "symbol": "INVALID",  # Ogiltigt symbolformat
        "order_type": "limit",
        "side": "buy",
        "amount": 1.0,
        "price": 50000.0,
    }

    # Patcha validate_trading_pair för att simulera valideringsfel
    with patch(
        "backend.services.order_service_async.validate_trading_pair"
    ) as mock_validate:
        mock_validate.return_value = (False, "Invalid trading pair format")

        # Act & Assert
        with pytest.raises(ValueError):
            await order_service_async.place_order(invalid_order_data)


@pytest.mark.asyncio
async def test_place_order_exchange_error(order_service_async):
    """Test för att hantera fel från exchange vid orderplacering."""
    # Arrange
    order_data = {
        "symbol": "BTC/USD",
        "order_type": "limit",
        "side": "buy",
        "amount": 1.0,
        "price": 50000.0,
    }

    # Patcha create_order_async för att kasta ett undantag
    with patch(
        "backend.services.order_service_async.create_order_async",
        side_effect=Exception("Exchange error"),
    ):
        # Act & Assert
        with pytest.raises(Exception):
            await order_service_async.place_order(order_data)

        # Verifiera att ordern sparades med status "failed"
        orders = list(order_service_async.orders.values())
        assert len(orders) > 0
        latest_order = orders[-1]
        assert latest_order["status"] == "failed"
        assert "error" in latest_order
