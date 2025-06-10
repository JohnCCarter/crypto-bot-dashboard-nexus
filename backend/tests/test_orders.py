from unittest.mock import patch

import pytest

from backend.app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_place_order_success(client):
    order_data = {
        "symbol": "BTC/USD",
        "order_type": "limit",
        "side": "buy",
        "amount": 0.1,
        "price": 27000,
    }
    with patch(
        "backend.services.order_service.OrderService.place_order"
    ) as mock_place_order:
        mock_place_order.return_value = {
            "id": "123",
            **order_data,
            "status": "filled",
        }
        response = client.post("/api/orders", json=order_data)
        assert response.status_code == 201
        data = response.get_json()
        assert data["message"] == "Order placed successfully"
        assert data["order"]["symbol"] == "BTC/USD"


def test_place_order_invalid_data(client):
    response = client.post("/api/orders", json={})
    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data


def test_get_order_success(client):
    with patch(
        "backend.services.order_service.OrderService.get_order_status"
    ) as mock_get_order:
        mock_get_order.return_value = {
            "id": "123",
            "symbol": "BTC/USD",
            "status": "filled",
        }
        response = client.get("/api/orders/123")
        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == "123"
        assert data["status"] == "filled"


def test_get_order_not_found(client):
    with patch(
        "backend.services.order_service.OrderService.get_order_status"
    ) as mock_get_order:
        mock_get_order.return_value = None
        response = client.get("/api/orders/999")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data


def test_cancel_order_success(client):
    with patch(
        "backend.services.order_service.OrderService.cancel_order"
    ) as mock_cancel_order:
        mock_cancel_order.return_value = True
        response = client.delete("/api/orders/123")
        assert response.status_code == 200
        data = response.get_json()
        assert data["message"] == "Order cancelled successfully"


def test_cancel_order_not_found(client):
    with patch(
        "backend.services.order_service.OrderService.cancel_order"
    ) as mock_cancel_order:
        mock_cancel_order.return_value = False
        response = client.delete("/api/orders/999")
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data


def test_get_open_orders(client):
    with patch(
        "backend.services.order_service.OrderService.get_open_orders"
    ) as mock_get_open_orders:
        mock_get_open_orders.return_value = [
            {"id": "1", "symbol": "BTC/USD", "status": "open"},
            {"id": "2", "symbol": "ETH/USD", "status": "open"},
        ]
        response = client.get("/api/orders")
        assert response.status_code == 200
        data = response.get_json()
        assert "orders" in data
        assert len(data["orders"]) == 2


def test_get_order_history(client):
    response = client.get("/api/orders/history")
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_place_order_server_error(client):
    with patch(
        "backend.services.order_service.OrderService.place_order",
        side_effect=Exception("DB error"),
    ):
        order_data = {
            "symbol": "BTC/USD",
            "order_type": "limit",
            "side": "buy",
            "amount": 0.1,
            "price": 27000,
        }
        response = client.post("/api/orders", json=order_data)
        assert response.status_code == 500
        data = response.get_json()
        assert "error" in data 