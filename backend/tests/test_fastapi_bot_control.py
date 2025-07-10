"""
Tests for FastAPI bot control endpoints.

Denna testfil använder en isolerad approach där vi testar enbart bot_control-routern
utan att ladda hela FastAPI-applikationen.
"""

from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from backend.api.bot_control import router as bot_control_router
from backend.api.dependencies import get_bot_manager


# Skapa en helt mockad app för testning
@pytest.fixture
def mock_app():
    """Create a mock FastAPI app for testing."""
    app = FastAPI()
    app.include_router(bot_control_router)
    return app


# Skapa en mock för BotManagerDependency - standardversion
@pytest.fixture
def mock_bot_manager():
    """Create a mock bot manager."""
    mock = AsyncMock()

    # Konfigurera dev_mode som en property
    type(mock).dev_mode = PropertyMock(return_value=False)

    # Mock get_status method
    mock.get_status.return_value = {
        "status": "stopped",
        "uptime": 0.0,
        "last_update": "2023-01-01T00:00:00",
        "thread_alive": False,
        "cycle_count": 0,
        "last_cycle_time": None,
        "dev_mode": False,
    }

    # Mock start_bot method
    mock.start_bot.return_value = {
        "success": True,
        "message": "Bot started successfully",
        "status": "running",
    }

    # Mock stop_bot method
    mock.stop_bot.return_value = {
        "success": True,
        "message": "Bot stopped successfully",
        "status": "stopped",
    }

    return mock


# Skapa en mock för BotManagerDependency - dev_mode version
@pytest.fixture
def mock_bot_manager_dev_mode():
    """Create a mock bot manager with dev_mode=True."""
    mock = AsyncMock()

    # Konfigurera dev_mode som en property
    type(mock).dev_mode = PropertyMock(return_value=True)

    # Mock get_status method
    mock.get_status.return_value = {
        "status": "stopped",
        "uptime": 0.0,
        "last_update": "2023-01-01T00:00:00",
        "thread_alive": False,
        "cycle_count": 0,
        "last_cycle_time": None,
        "dev_mode": True,
    }

    # Mock start_bot method
    mock.start_bot.return_value = {
        "success": True,
        "message": "Bot started successfully (DEVELOPMENT MODE)",
        "status": "running",
    }

    # Mock stop_bot method
    mock.stop_bot.return_value = {
        "success": True,
        "message": "Bot stopped successfully",
        "status": "stopped",
    }

    return mock


# Skapa en mock för BotManagerDependency - error version
@pytest.fixture
def mock_bot_manager_error():
    """Create a mock bot manager that raises errors."""
    mock = AsyncMock()

    # Konfigurera dev_mode som en property
    type(mock).dev_mode = PropertyMock(return_value=False)

    # Mock get_status method to raise exception
    mock.get_status.side_effect = Exception("Test error")

    # Mock start_bot method to raise exception
    mock.start_bot.side_effect = Exception("Test error")

    # Mock stop_bot method to raise exception
    mock.stop_bot.side_effect = Exception("Test error")

    return mock


# Skapa en mock för BotManagerDependency - already running version
@pytest.fixture
def mock_bot_manager_already_running():
    """Create a mock bot manager that simulates already running bot."""
    mock = AsyncMock()

    # Konfigurera dev_mode som en property
    type(mock).dev_mode = PropertyMock(return_value=False)

    # Mock get_status method
    mock.get_status.return_value = {
        "status": "running",
        "uptime": 100.0,
        "last_update": "2023-01-01T00:00:00",
        "thread_alive": True,
        "cycle_count": 5,
        "last_cycle_time": "2023-01-01T00:05:00",
        "dev_mode": False,
    }

    # Mock start_bot method to return already running
    mock.start_bot.return_value = {
        "success": False,
        "message": "Bot is already running",
        "status": "running",
    }

    # Mock stop_bot method
    mock.stop_bot.return_value = {
        "success": True,
        "message": "Bot stopped successfully",
        "status": "stopped",
    }

    return mock


# Skapa en mock för BotManagerDependency - not running version
@pytest.fixture
def mock_bot_manager_not_running():
    """Create a mock bot manager that simulates bot not running."""
    mock = AsyncMock()

    # Konfigurera dev_mode som en property
    type(mock).dev_mode = PropertyMock(return_value=False)

    # Mock get_status method
    mock.get_status.return_value = {
        "status": "stopped",
        "uptime": 0.0,
        "last_update": "2023-01-01T00:00:00",
        "thread_alive": False,
        "cycle_count": 0,
        "last_cycle_time": None,
        "dev_mode": False,
    }

    # Mock start_bot method
    mock.start_bot.return_value = {
        "success": True,
        "message": "Bot started successfully",
        "status": "running",
    }

    # Mock stop_bot method to return not running
    mock.stop_bot.return_value = {
        "success": False,
        "message": "Bot is not running",
        "status": "stopped",
    }

    return mock


# Patcha event_logger för att undvika sidoeffekter
@pytest.fixture
def mock_event_logger():
    """Mock event logger."""
    mock_logger = MagicMock()
    mock_logger.log_event = MagicMock()
    mock_logger.log_api_error = MagicMock()

    # Förbättrad mock för should_suppress_routine_log
    def mock_should_suppress(endpoint, method):
        # Returnera True för rutinmässig polling, False annars
        if endpoint == "/api/bot-status" and method == "GET":
            return True
        return False

    mock_logger.should_suppress_routine_log = mock_should_suppress
    return mock_logger


# Skapa en test client med mockade beroenden - standardversion utan dev_mode
@pytest.fixture
def test_client(mock_app, mock_bot_manager, mock_event_logger):
    """Create a test client with mocked dependencies."""

    # Skapa en dependency override funktion
    def override_get_bot_manager():
        return mock_bot_manager

    # Använd dependency override istället för patching
    mock_app.dependency_overrides[get_bot_manager] = override_get_bot_manager

    # Patcha event_logger för att undvika sidoeffekter
    with patch("backend.api.bot_control.event_logger", mock_event_logger), patch(
        "backend.api.bot_control.should_suppress_routine_log",
        mock_event_logger.should_suppress_routine_log,
    ):

        # Skapa test client
        client = TestClient(mock_app)
        yield client

        # Cleanup
        mock_app.dependency_overrides.clear()


# Skapa en test client med dev_mode aktiverat
@pytest.fixture
def test_client_dev_mode(mock_app, mock_bot_manager_dev_mode, mock_event_logger):
    """Create a test client with mocked dependencies and dev_mode enabled."""

    # Skapa en dependency override funktion
    def override_get_bot_manager():
        return mock_bot_manager_dev_mode

    # Använd dependency override istället för patching
    mock_app.dependency_overrides[get_bot_manager] = override_get_bot_manager

    # Patcha event_logger för att undvika sidoeffekter
    with patch("backend.api.bot_control.event_logger", mock_event_logger), patch(
        "backend.api.bot_control.should_suppress_routine_log",
        mock_event_logger.should_suppress_routine_log,
    ):

        # Skapa test client
        client = TestClient(mock_app)
        yield client

        # Cleanup
        mock_app.dependency_overrides.clear()


# Skapa en test client för error-scenarier
@pytest.fixture
def test_client_error(mock_app, mock_bot_manager_error, mock_event_logger):
    """Create a test client with error-throwing bot manager."""

    # Skapa en dependency override funktion
    def override_get_bot_manager():
        return mock_bot_manager_error

    # Använd dependency override istället för patching
    mock_app.dependency_overrides[get_bot_manager] = override_get_bot_manager

    # Patcha event_logger för att undvika sidoeffekter
    with patch("backend.api.bot_control.event_logger", mock_event_logger), patch(
        "backend.api.bot_control.should_suppress_routine_log",
        mock_event_logger.should_suppress_routine_log,
    ):

        # Skapa test client
        client = TestClient(mock_app)
        yield client

        # Cleanup
        mock_app.dependency_overrides.clear()


# Skapa en test client för already running scenario
@pytest.fixture
def test_client_already_running(
    mock_app, mock_bot_manager_already_running, mock_event_logger
):
    """Create a test client with already running bot manager."""

    # Skapa en dependency override funktion
    def override_get_bot_manager():
        return mock_bot_manager_already_running

    # Använd dependency override istället för patching
    mock_app.dependency_overrides[get_bot_manager] = override_get_bot_manager

    # Patcha event_logger för att undvika sidoeffekter
    with patch("backend.api.bot_control.event_logger", mock_event_logger), patch(
        "backend.api.bot_control.should_suppress_routine_log",
        mock_event_logger.should_suppress_routine_log,
    ):

        # Skapa test client
        client = TestClient(mock_app)
        yield client

        # Cleanup
        mock_app.dependency_overrides.clear()


# Skapa en test client för not running scenario
@pytest.fixture
def test_client_not_running(mock_app, mock_bot_manager_not_running, mock_event_logger):
    """Create a test client with not running bot manager."""

    # Skapa en dependency override funktion
    def override_get_bot_manager():
        return mock_bot_manager_not_running

    # Använd dependency override istället för patching
    mock_app.dependency_overrides[get_bot_manager] = override_get_bot_manager

    # Patcha event_logger för att undvika sidoeffekter
    with patch("backend.api.bot_control.event_logger", mock_event_logger), patch(
        "backend.api.bot_control.should_suppress_routine_log",
        mock_event_logger.should_suppress_routine_log,
    ):

        # Skapa test client
        client = TestClient(mock_app)
        yield client

        # Cleanup
        mock_app.dependency_overrides.clear()


def test_get_bot_status(test_client):
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


def test_get_bot_status_dev_mode(test_client_dev_mode):
    """Test getting bot status with dev_mode enabled."""
    # Act
    response = test_client_dev_mode.get("/api/bot-status")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"
    assert data["dev_mode"] is True
    assert "uptime" in data
    assert "thread_alive" in data


def test_start_bot(test_client):
    """Test starting the bot."""
    # Act
    response = test_client.post("/api/bot/start")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "running"


def test_start_bot_dev_mode(test_client_dev_mode):
    """Test starting the bot in dev mode."""
    # Act
    response = test_client_dev_mode.post("/api/bot/start")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "running"
    assert "DEVELOPMENT MODE" in data["message"]


def test_stop_bot(test_client):
    """Test stopping the bot."""
    # Act
    response = test_client.post("/api/bot/stop")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "stopped"


def test_stop_bot_dev_mode(test_client_dev_mode):
    """Test stopping the bot in dev mode."""
    # Act
    response = test_client_dev_mode.post("/api/bot/stop")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "stopped"


def test_start_bot_already_running(test_client_already_running):
    """Test starting the bot when it's already running."""
    # Act
    response = test_client_already_running.post("/api/bot/start")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Bot is already running"
    assert data["status"] == "running"


def test_stop_bot_not_running(test_client_not_running):
    """Test stopping the bot when it's not running."""
    # Act
    response = test_client_not_running.post("/api/bot/stop")

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Bot is not running"
    assert data["status"] == "stopped"


def test_get_bot_status_error(test_client_error):
    """Test getting bot status with error."""
    # Act
    response = test_client_error.get("/api/bot-status")

    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"].lower()


def test_start_bot_error(test_client_error):
    """Test starting the bot with error."""
    # Act
    response = test_client_error.post("/api/bot/start")

    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "error" in data["detail"].lower()
