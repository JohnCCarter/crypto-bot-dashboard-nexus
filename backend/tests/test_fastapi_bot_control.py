"""
Tests for FastAPI bot control endpoints.

Denna testfil använder en isolerad approach där vi testar enbart bot_control-routern
utan att ladda hela FastAPI-applikationen.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock, PropertyMock
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

from backend.api.bot_control import router as bot_control_router


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
    # OBS: AsyncMock.return_value används för att skapa ett korutinfunktionsobjekt som 
    # sedan returnerar det angivna värdet när det väntas
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
    # Patcha alla beroenden
    with patch("backend.api.bot_control.get_bot_manager") as mock_get_bot_manager, \
         patch("backend.api.bot_control.event_logger", mock_event_logger), \
         patch("backend.api.bot_control.should_suppress_routine_log", mock_event_logger.should_suppress_routine_log):
        
        # Konfigurera mock_get_bot_manager att returnera mock_bot_manager
        mock_get_bot_manager.return_value = mock_bot_manager
        
        # Skapa test client
        client = TestClient(mock_app)
        yield client


# Skapa en test client med dev_mode aktiverat
@pytest.fixture
def test_client_dev_mode(mock_app, mock_bot_manager_dev_mode, mock_event_logger):
    """Create a test client with mocked dependencies and dev_mode enabled."""
    # Patcha alla beroenden
    with patch("backend.api.bot_control.get_bot_manager") as mock_get_bot_manager, \
         patch("backend.api.bot_control.event_logger", mock_event_logger), \
         patch("backend.api.bot_control.should_suppress_routine_log", mock_event_logger.should_suppress_routine_log):
        
        # Konfigurera get_bot_manager att returnera mock_bot_manager
        mock_get_bot_manager.return_value = mock_bot_manager_dev_mode
        
        # Skapa test client
        client = TestClient(mock_app)
        yield client


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


def test_start_bot_already_running(test_client):
    """Test starting the bot when it's already running."""
    # Skapa en ny test client med anpassad mock för detta test
    with patch("backend.api.bot_control.get_bot_manager") as mock_get_bot_manager:
        # Skapa en anpassad mock
        mock_manager = AsyncMock()
        
        mock_manager.start_bot.return_value = {
            "success": False,
            "message": "Bot is already running",
            "status": "running",
        }
        
        # Konfigurera get_bot_manager
        mock_get_bot_manager.return_value = mock_manager
        
        # Skapa en ny test client
        app = FastAPI()
        app.include_router(bot_control_router)
        client = TestClient(app)
        
        # Utför testet
        response = client.post("/api/bot/start")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Bot is already running"
    assert data["status"] == "running"


def test_stop_bot_not_running(test_client):
    """Test stopping the bot when it's not running."""
    # Skapa en ny test client med anpassad mock för detta test
    with patch("backend.api.bot_control.get_bot_manager") as mock_get_bot_manager:
        # Skapa en anpassad mock
        mock_manager = AsyncMock()
        
        mock_manager.stop_bot.return_value = {
            "success": False,
            "message": "Bot is not running",
            "status": "stopped",
        }
        
        # Konfigurera get_bot_manager
        mock_get_bot_manager.return_value = mock_manager
        
        # Skapa en ny test client
        app = FastAPI()
        app.include_router(bot_control_router)
        client = TestClient(app)
        
        # Utför testet
        response = client.post("/api/bot/stop")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["message"] == "Bot is not running"
    assert data["status"] == "stopped"


def test_get_bot_status_error(test_client, mock_event_logger):
    """Test getting bot status with error."""
    # Skapa en ny test client med anpassad mock för detta test
    with patch("backend.api.bot_control.get_bot_manager") as mock_get_bot_manager, \
         patch("backend.api.bot_control.event_logger", mock_event_logger):
        # Skapa en anpassad mock som kastar ett fel
        mock_manager = AsyncMock()
        mock_manager.get_status.side_effect = Exception("Test error")
        
        # Konfigurera get_bot_manager
        mock_get_bot_manager.return_value = mock_manager
        
        # Skapa en ny test client
        app = FastAPI()
        app.include_router(bot_control_router)
        client = TestClient(app)
        
        # Utför testet
        response = client.get("/api/bot-status")
    
    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "test error" in data["detail"].lower()
    assert mock_event_logger.log_api_error.called


def test_start_bot_error(test_client, mock_event_logger):
    """Test starting the bot with error."""
    # Skapa en ny test client med anpassad mock för detta test
    with patch("backend.api.bot_control.get_bot_manager") as mock_get_bot_manager, \
         patch("backend.api.bot_control.event_logger", mock_event_logger):
        # Skapa en anpassad mock som kastar ett fel
        mock_manager = AsyncMock()
        mock_manager.start_bot.side_effect = Exception("Test error")
        
        # Konfigurera get_bot_manager
        mock_get_bot_manager.return_value = mock_manager
        
        # Skapa en ny test client
        app = FastAPI()
        app.include_router(bot_control_router)
        client = TestClient(app)
        
        # Utför testet
        response = client.post("/api/bot/start")
    
    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "test error" in data["detail"].lower()
    assert mock_event_logger.log_api_error.called
