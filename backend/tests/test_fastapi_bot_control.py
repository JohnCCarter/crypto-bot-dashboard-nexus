"""
Tests for FastAPI bot control endpoints.
"""

import pytest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from backend.fastapi_app import app
from backend.api.dependencies import BotManagerDependency


# Patcha get_bot_manager för att returnera en mock
@pytest.fixture(autouse=True)
def mock_dependencies():
    """Mock all dependencies for testing."""
    with patch("backend.api.bot_control.get_bot_manager") as mock_get_bot_manager:
        # Skapa en mock för BotManagerDependency
        mock_manager = AsyncMock(spec=BotManagerDependency)

        # Mock get_status method
        mock_manager.get_status.return_value = {
            "status": "stopped",
            "uptime": 0.0,
            "last_update": "2023-01-01T00:00:00",
            "thread_alive": False,
            "cycle_count": 0,
            "last_cycle_time": None,
        }

        # Mock start_bot method
        mock_manager.start_bot.return_value = {
            "success": True,
            "message": "Bot started successfully",
            "status": "running",
        }

        # Mock stop_bot method
        mock_manager.stop_bot.return_value = {
            "success": True,
            "message": "Bot stopped successfully",
            "status": "stopped",
        }

        mock_get_bot_manager.return_value = mock_manager
        yield mock_manager


@pytest.fixture
def test_client():
    """Create a test client for FastAPI app."""
    return TestClient(app)


@pytest.mark.asyncio
async def test_get_bot_status(mock_dependencies, test_client):
    """Test getting bot status."""
    # Act
    response = test_client.get("/api/bot-status")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"
    assert data["uptime"] == 0.0
    assert data["thread_alive"] is False
    assert data["cycle_count"] == 0
    mock_dependencies.get_status.assert_called_once()


@pytest.mark.asyncio
async def test_start_bot(mock_dependencies, test_client):
    """Test starting the bot."""
    # Act
    response = test_client.post("/api/bot/start")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "running"
    mock_dependencies.start_bot.assert_called_once()


@pytest.mark.asyncio
async def test_stop_bot(mock_dependencies, test_client):
    """Test stopping the bot."""
    # Act
    response = test_client.post("/api/bot/stop")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "stopped"
    mock_dependencies.stop_bot.assert_called_once()


@pytest.mark.asyncio
async def test_start_bot_already_running(mock_dependencies, test_client):
    """Test starting the bot when it's already running."""
    # Arrange
    mock_dependencies.start_bot.return_value = {
        "success": False,
        "message": "Bot is already running",
        "status": "running",
    }

    # Act
    response = test_client.post("/api/bot/start")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Bot is already running"
    assert data["status"] == "running"
    mock_dependencies.start_bot.assert_called_once()


@pytest.mark.asyncio
async def test_stop_bot_not_running(mock_dependencies, test_client):
    """Test stopping the bot when it's not running."""
    # Arrange
    mock_dependencies.stop_bot.return_value = {
        "success": False,
        "message": "Bot is not running",
        "status": "stopped",
    }

    # Act
    response = test_client.post("/api/bot/stop")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Bot is not running"
    assert data["status"] == "stopped"
    mock_dependencies.stop_bot.assert_called_once()


@pytest.mark.asyncio
@patch("backend.api.bot_control.event_logger")
async def test_get_bot_status_error(mock_event_logger, mock_dependencies, test_client):
    """Test getting bot status with error."""
    # Arrange
    mock_dependencies.get_status.side_effect = Exception("Test error")

    # Act
    response = test_client.get("/api/bot-status")

    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "Test error" in data["error"]
    mock_event_logger.log_api_error.assert_called_once()


@pytest.mark.asyncio
@patch("backend.api.bot_control.event_logger")
async def test_start_bot_error(mock_event_logger, mock_dependencies, test_client):
    """Test starting the bot with error."""
    # Arrange
    mock_dependencies.start_bot.return_value = {
        "success": False,
        "message": "Failed to start bot: Test error",
        "status": "error",
    }

    # Act
    response = test_client.post("/api/bot/start")

    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "error" in data
    assert "Failed to start bot" in data["detail"]
    mock_event_logger.log_event.assert_called_once()
