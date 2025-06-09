import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
import json
from unittest.mock import patch

from backend.app import app


def test_status_endpoint():
    client = app.test_client()
    response = client.get("/api/status")
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("status") == "running"
    assert "balance" in data


@patch("backend.routes.balances.fetch_balances")
def test_balances_endpoint(mock_fetch_balances):
    mock_fetch_balances.return_value = {
        "total": {"USD": 100.0, "BTC": 0.1},
        "free": {"USD": 80.0, "BTC": 0.05},
    }
    client = app.test_client()
    response = client.get("/api/balances")
    assert response.status_code == 200
    expected = [
        {"currency": "USD", "total_balance": 100.0, "available": 80.0},
        {"currency": "BTC", "total_balance": 0.1, "available": 0.05},
    ]
    assert response.get_json() == expected


def test_bot_control_endpoints():
    client = app.test_client()
    # Start the trading bot
    response = client.post("/api/start-bot")
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("status") == "running"
    assert data.get("message") == "Bot started"

    # Retrieve bot status (should include uptime and last_update)
    response = client.get("/api/bot-status")
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("status") == "running"
    assert "uptime" in data and isinstance(data["uptime"], (int, float))
    assert "last_update" in data and isinstance(data["last_update"], str)

    # Stop the trading bot
    response = client.post("/api/stop-bot")
    assert response.status_code == 200
    data = response.get_json()
    assert data.get("status") == "stopped"
    assert data.get("message") == "Bot stopped"
