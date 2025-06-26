import os
import sys
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from backend.app import app


def test_status_endpoint():
    client = app.test_client()
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("status") == "running"
    assert "balance" in data


@patch("backend.services.balance_service.get_shared_exchange_service")
def test_balances_endpoint(mock_exchange_service):
    # Skapa mock exchange med fetch_balance metod
    mock_exchange = MagicMock()
    mock_exchange.fetch_balance.return_value = {
        "total": {"USD": 100.0, "BTC": 0.1},
        "free": {"USD": 80.0, "BTC": 0.05},
    }

    mock_service = MagicMock()
    mock_service.exchange = mock_exchange
    mock_exchange_service.return_value = mock_service

    client = app.test_client()
    response = client.get("/api/balances")
    assert response.status_code == 200
    expected = [
        {"currency": "USD", "total_balance": 100.0, "available": 80.0},
        {"currency": "BTC", "total_balance": 0.1, "available": 0.05},
    ]
    assert response.get_json() == expected
