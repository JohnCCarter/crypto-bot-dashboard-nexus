"""
FastAPI Orders API tests.

This module tests the FastAPI orders endpoints with OrderServiceAsync integration.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.api.dependencies import get_order_service
from backend.api.orders import router as orders_router
from backend.services.order_service_async import OrderServiceAsync


@pytest.fixture
def mock_order_service():
    """Create a mock OrderServiceAsync."""
    return AsyncMock(spec=OrderServiceAsync)


@pytest.fixture
def app(mock_order_service):
    """Create FastAPI app for testing with mocked dependencies."""
    app = FastAPI()

    # Override the dependency
    def override_get_order_service():
        return mock_order_service

    app.dependency_overrides[get_order_service] = override_get_order_service
    app.include_router(orders_router)
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.mark.fast
@pytest.mark.api
def test_get_orders_success(client, mock_order_service):
    """Test successful GET /api/orders."""
    # Mock orders data
    mock_orders = [
        {
            "id": "123",
            "symbol": "BTC/USD",
            "type": "limit",
            "side": "buy",
            "amount": 0.1,
            "price": 27000,
            "status": "open",
        },
        {
            "id": "124",
            "symbol": "ETH/USD",
            "type": "market",
            "side": "sell",
            "amount": 1.0,
            "price": 0,
            "status": "open",
        },
    ]

    mock_order_service.get_open_orders.return_value = mock_orders

    response = client.get("/api/orders")

    assert response.status_code == 200
    data = response.json()
    assert "orders" in data
    assert len(data["orders"]) == 2
    assert data["orders"][0]["id"] == "123"
    assert data["orders"][1]["id"] == "124"

    mock_order_service.get_open_orders.assert_called_once_with(None)


@pytest.mark.fast
@pytest.mark.api
def test_get_orders_with_symbol_filter(client, mock_order_service):
    """Test GET /api/orders with symbol filter."""
    mock_orders = [
        {
            "id": "123",
            "symbol": "BTC/USD",
            "type": "limit",
            "side": "buy",
            "amount": 0.1,
            "price": 27000,
            "status": "open",
        }
    ]

    mock_order_service.get_open_orders.return_value = mock_orders

    response = client.get("/api/orders?symbol=BTC/USD")

    assert response.status_code == 200
    data = response.json()
    assert len(data["orders"]) == 1
    assert data["orders"][0]["symbol"] == "BTC/USD"

    mock_order_service.get_open_orders.assert_called_once_with("BTC/USD")


def test_get_order_by_id_success(client, mock_order_service):
    """Test successful GET /api/orders/{order_id}."""
    mock_order = {
        "id": "123",
        "symbol": "BTC/USD",
        "type": "limit",
        "side": "buy",
        "amount": 0.1,
        "price": 27000,
        "status": "open",
    }

    mock_order_service.get_order_status.return_value = mock_order

    response = client.get("/api/orders/123")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "123"
    assert data["symbol"] == "BTC/USD"
    assert data["status"] == "open"

    mock_order_service.get_order_status.assert_called_once_with("123")


def test_get_order_by_id_not_found(client, mock_order_service):
    """Test GET /api/orders/{order_id} when order not found."""
    mock_order_service.get_order_status.return_value = None

    response = client.get("/api/orders/999")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


@pytest.mark.fast
@pytest.mark.api
def test_place_order_success(client, mock_order_service):
    """Test successful POST /api/orders."""
    order_data = {
        "symbol": "BTC/USD",
        "type": "limit",
        "side": "buy",
        "amount": 0.1,
        "price": 27000,
    }

    mock_result = {
        "id": "123",
        "symbol": "BTC/USD",
        "type": "limit",
        "side": "buy",
        "amount": 0.1,
        "price": 27000,
        "status": "open",
    }

    mock_order_service.place_order.return_value = mock_result

    response = client.post("/api/orders", json=order_data)

    assert response.status_code == 201
    data = response.json()
    # Order ID is generated by the service, so we just check it exists
    assert "id" in data
    assert data["status"] == "open"

    # Verify that place_order was called with the correct data
    mock_order_service.place_order.assert_called_once()
    call_args = mock_order_service.place_order.call_args[0][0]
    assert call_args["symbol"] == "BTC/USD"
    assert call_args["order_type"] == "limit"  # type should be converted to order_type


def test_place_market_order_success(client, mock_order_service):
    """Test successful POST /api/orders for market orders with None price."""
    order_data = {
        "symbol": "BTC/USD",
        "type": "market",
        "side": "buy",
        "amount": 0.1,
        # No price field for market orders
    }

    mock_result = {
        "id": "123",
        "symbol": "BTC/USD",
        "type": "market",
        "side": "buy",
        "amount": 0.1,
        "price": None,
        "status": "open",
    }

    mock_order_service.place_order.return_value = mock_result

    response = client.post("/api/orders", json=order_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "open"

    # Verify that place_order was called with the correct data
    mock_order_service.place_order.assert_called_once()
    call_args = mock_order_service.place_order.call_args[0][0]
    assert call_args["symbol"] == "BTC/USD"
    assert call_args["order_type"] == "market"
    assert "price" not in call_args or call_args["price"] is None


def test_place_market_order_with_explicit_none_price(client, mock_order_service):
    """Test successful POST /api/orders for market orders with explicit None price."""
    order_data = {
        "symbol": "BTC/USD",
        "type": "market",
        "side": "buy",
        "amount": 0.1,
        "price": None,  # Explicit None price for market orders
    }

    mock_result = {
        "id": "123",
        "symbol": "BTC/USD",
        "type": "market",
        "side": "buy",
        "amount": 0.1,
        "price": None,
        "status": "open",
    }

    mock_order_service.place_order.return_value = mock_result

    response = client.post("/api/orders", json=order_data)

    assert response.status_code == 201
    data = response.json()
    assert "id" in data
    assert data["status"] == "open"

    # Verify that place_order was called with the correct data
    mock_order_service.place_order.assert_called_once()
    call_args = mock_order_service.place_order.call_args[0][0]
    assert call_args["symbol"] == "BTC/USD"
    assert call_args["order_type"] == "market"
    assert call_args["price"] is None


def test_cancel_order_success(client, mock_order_service):
    """Test successful DELETE /api/orders/{order_id}."""
    mock_order = {
        "id": "123",
        "symbol": "BTC/USD",
        "type": "limit",
        "side": "buy",
        "amount": 0.1,
        "price": 27000,
        "status": "cancelled",
    }

    mock_order_service.cancel_order.return_value = True
    mock_order_service.get_order_status.return_value = mock_order

    response = client.delete("/api/orders/123?symbol=BTC/USD")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "123"
    assert data["status"] == "cancelled"

    mock_order_service.cancel_order.assert_called_once_with("123")


def test_cancel_order_not_found(client, mock_order_service):
    """Test DELETE /api/orders/{order_id} when order not found."""
    mock_order_service.cancel_order.return_value = False

    response = client.delete("/api/orders/999?symbol=BTC/USD")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_cancel_order_missing_symbol(client, mock_order_service):
    """Test DELETE /api/orders/{order_id} without symbol parameter."""
    response = client.delete("/api/orders/123")

    assert (
        response.status_code == 422
    )  # Validation error for missing required parameter


def test_get_orders_with_limit(client, mock_order_service):
    """Test GET /api/orders with limit parameter."""
    mock_orders = [
        {"id": "1", "symbol": "BTC/USD", "status": "open"},
        {"id": "2", "symbol": "ETH/USD", "status": "open"},
        {"id": "3", "symbol": "LTC/USD", "status": "open"},
    ]

    mock_order_service.get_open_orders.return_value = mock_orders

    response = client.get("/api/orders?limit=2")

    assert response.status_code == 200
    data = response.json()
    assert len(data["orders"]) == 2  # Should be limited to 2 orders
