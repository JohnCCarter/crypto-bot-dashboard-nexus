"""Tests for FastAPI positions endpoints."""

import pytest
from fastapi.testclient import TestClient
import time

from backend.fastapi_app import app
from backend.services.exchange import ExchangeError
from unittest.mock import patch, MagicMock, AsyncMock

client = TestClient(app)


@pytest.fixture
def mock_positions_service():
    """Mock positions service for testing."""
    async def mock_fetch_positions_async(symbols=None):
        """Mock fetch_positions_async function."""
        if symbols and "ERROR" in symbols:
            raise ExchangeError("Test exchange error")
        elif symbols and "EXCEPTION" in symbols:
            raise Exception("Test general exception")
        
        # Return mock positions data
        return [
            {
                "id": "BTC-PERP-12345",
                "symbol": "BTC/USD",
                "side": "buy",
                "amount": 0.5,
                "entry_price": 45000.0,
                "mark_price": 47500.0,
                "pnl": 1250.0,
                "pnl_percentage": 5.56,
                "timestamp": int(time.time() * 1000),
                "contracts": 0.5,
                "notional": 23750.0,
                "collateral": 23750.0,
                "margin_mode": "cross",
                "maintenance_margin": 1187.5,
                "position_type": "margin",
                "leverage": 1.0,
            },
            {
                "id": "ETH-PERP-23456",
                "symbol": "ETH/USD",
                "side": "sell",
                "amount": 2.5,
                "entry_price": 3500.0,
                "mark_price": 3250.0,
                "pnl": 625.0,
                "pnl_percentage": 7.14,
                "timestamp": int(time.time() * 1000),
                "contracts": 2.5,
                "notional": 8125.0,
                "collateral": 8125.0,
                "margin_mode": "cross",
                "maintenance_margin": 406.25,
                "position_type": "margin",
                "leverage": 1.0,
            },
        ]
    
    with patch("backend.api.dependencies.get_positions_service") as mock:
        mock.return_value = mock_fetch_positions_async
        yield mock


@pytest.fixture
def mock_event_logger():
    """Mock event logger for testing."""
    with patch("backend.api.positions.event_logger") as mock:
        mock.log_event = MagicMock()
        mock.log_exchange_error = MagicMock()
        mock.log_api_error = MagicMock()
        yield mock


@pytest.fixture
def mock_should_suppress_routine_log():
    """Mock should_suppress_routine_log function for testing."""
    with patch("backend.api.positions.should_suppress_routine_log") as mock:
        # Default to not suppressing logs for testing
        mock.return_value = False
        yield mock


def test_get_positions(mock_positions_service, mock_event_logger, mock_should_suppress_routine_log):
    """Test get_positions endpoint."""
    response = client.get("/api/positions")
    assert response.status_code == 200
    data = response.json()
    assert "positions" in data
    assert len(data["positions"]) == 2
    assert data["positions"][0]["symbol"] == "BTC/USD"
    assert data["positions"][1]["symbol"] == "ETH/USD"
    
    # Verify event logger was called
    mock_event_logger.log_event.assert_called_once()


def test_get_positions_with_symbols(mock_positions_service, mock_event_logger):
    """Test get_positions endpoint with symbols parameter."""
    response = client.get("/api/positions?symbols=BTC/USD&symbols=ETH/USD")
    assert response.status_code == 200
    data = response.json()
    assert "positions" in data
    assert len(data["positions"]) == 2


def test_get_positions_suppress_log(mock_positions_service, mock_event_logger, mock_should_suppress_routine_log):
    """Test get_positions endpoint with log suppression."""
    # Configure mock to suppress logs
    mock_should_suppress_routine_log.return_value = True
    
    response = client.get("/api/positions")
    assert response.status_code == 200
    
    # Verify event logger was not called
    mock_event_logger.log_event.assert_not_called()


def test_get_positions_exchange_error(mock_positions_service, mock_event_logger):
    """Test get_positions endpoint with exchange error."""
    response = client.get("/api/positions?symbols=ERROR")
    assert response.status_code == 200
    data = response.json()
    assert "positions" in data
    assert len(data["positions"]) == 0
    
    # Verify exchange error was logged
    mock_event_logger.log_exchange_error.assert_called_once()


def test_get_positions_general_exception(mock_positions_service, mock_event_logger):
    """Test get_positions endpoint with general exception."""
    response = client.get("/api/positions?symbols=EXCEPTION")
    assert response.status_code == 500
    
    # Verify API error was logged
    mock_event_logger.log_api_error.assert_called_once() 