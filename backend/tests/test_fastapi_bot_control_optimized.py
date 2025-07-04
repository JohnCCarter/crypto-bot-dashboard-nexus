"""
Optimerade tester för FastAPI bot control endpoints.

Denna testfil använder optimerad testmetodik för att lösa problemen som identifierats
i FASTAPI_DEBUG_SESSION_2025_07_03.md. Följande förbättringar är implementerade:

1. Bättre hantering av dependency injection
2. Mer isolerade tester med korrekt hantering av asynkron kod
3. Korrekt hantering av dev_mode
4. Korrekt hantering av globala tjänster som kan påverka tester
"""

import os
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock

from fastapi import FastAPI, HTTPException, Depends
from fastapi.testclient import TestClient

from backend.api.bot_control import router as bot_control_router
from backend.api.bot_control import get_bot_manager
from backend.api.models import BotStatusResponse, BotActionResponse
from backend.services.bot_manager_async import BotManagerAsync
from backend.api.dependencies import BotManagerDependency


# Skapa en isolerad version av BotManagerAsync för testning
class MockBotManagerAsync:
    """Isolerad mock för BotManagerAsync."""
    
    def __init__(self, dev_mode=False):
        """Initialize with predefined test values."""
        self.dev_mode = dev_mode
        self.is_running = False
        self.cycle_count = 0
        self.start_time = None
        self.error = None
        self.should_raise_error = False
        self.error_message = "Test error"
    
    async def get_status(self):
        """Get mock bot status."""
        if self.should_raise_error:
            raise Exception(self.error_message)
            
        return {
            "status": "running" if self.is_running else "stopped",
            "uptime": 0.0,
            "last_update": "2023-01-01T00:00:00",
            "thread_alive": self.is_running,
            "cycle_count": self.cycle_count,
            "last_cycle_time": None,
            "dev_mode": self.dev_mode,
            **({"error": self.error} if self.error else {})
        }
    
    async def start_bot(self):
        """Mock start bot functionality."""
        if self.should_raise_error:
            raise Exception(self.error_message)
            
        if self.is_running:
            return {
                "success": False,
                "message": "Bot is already running",
                "status": "running",
                "dev_mode": self.dev_mode
            }
        
        self.is_running = True
        return {
            "success": True,
            "message": f"Bot started successfully{' (DEVELOPMENT MODE)' if self.dev_mode else ''}",
            "status": "running",
            "dev_mode": self.dev_mode
        }
    
    async def stop_bot(self):
        """Mock stop bot functionality."""
        if self.should_raise_error:
            raise Exception(self.error_message)
            
        if not self.is_running:
            return {
                "success": False,
                "message": "Bot is not running",
                "status": "stopped",
                "dev_mode": self.dev_mode
            }
        
        self.is_running = False
        return {
            "success": True,
            "message": "Bot stopped successfully",
            "status": "stopped",
            "dev_mode": self.dev_mode
        }


class MockBotManagerDependency:
    """Mock av BotManagerDependency som använder MockBotManagerAsync."""
    
    def __init__(self, dev_mode=False):
        """Initialize med MockBotManagerAsync instance."""
        self.bot_manager = MockBotManagerAsync(dev_mode=dev_mode)
        self._dev_mode = dev_mode
    
    @property
    def dev_mode(self):
        """Return dev_mode flag."""
        return self._dev_mode
    
    async def get_status(self):
        """Proxy till bot_manager.get_status."""
        return await self.bot_manager.get_status()
    
    async def start_bot(self):
        """Proxy till bot_manager.start_bot."""
        return await self.bot_manager.start_bot()
    
    async def stop_bot(self):
        """Proxy till bot_manager.stop_bot."""
        return await self.bot_manager.stop_bot()


# Håll en global referens till mockarna för att kunna manipulera dem i tester
mock_manager_normal = MockBotManagerDependency(dev_mode=False)
mock_manager_dev = MockBotManagerDependency(dev_mode=True)


# Skapa en isolerad test app med korrekta mockningar
@pytest.fixture
def test_app_normal():
    """Create a clean isolated FastAPI app for testing with normal mode mocks."""
    app = FastAPI()
    
    # Återställ mocken till ursprungligt tillstånd
    mock_manager_normal.bot_manager.is_running = False
    mock_manager_normal.bot_manager.should_raise_error = False
    
    # Mocked async dependency
    async def get_mock_bot_manager():
        return mock_manager_normal
    
    # Montera router med mockat beroende
    app.include_router(bot_control_router)
    
    # Ersätt dependency med mock
    app.dependency_overrides[get_bot_manager] = get_mock_bot_manager
    
    # Mock event logger
    with patch("backend.api.bot_control.event_logger") as mock_event_logger:
        mock_event_logger.log_event = MagicMock()
        mock_event_logger.log_api_error = MagicMock()
        mock_event_logger.should_suppress_routine_log = MagicMock(return_value=False)
        
        # Returnera app med mocks
        yield app, mock_event_logger
    
    # Rensa upp dependency overrides
    app.dependency_overrides = {}


# Test app med dev mode mocks
@pytest.fixture
def test_app_dev():
    """Create a clean isolated FastAPI app for testing with dev mode mocks."""
    app = FastAPI()
    
    # Återställ mocken till ursprungligt tillstånd
    mock_manager_dev.bot_manager.is_running = False
    mock_manager_dev.bot_manager.should_raise_error = False
    
    # Mocked async dependency
    async def get_mock_bot_manager():
        return mock_manager_dev
    
    # Montera router med mockat beroende
    app.include_router(bot_control_router)
    
    # Ersätt dependency med mock
    app.dependency_overrides[get_bot_manager] = get_mock_bot_manager
    
    # Mock event logger
    with patch("backend.api.bot_control.event_logger") as mock_event_logger:
        mock_event_logger.log_event = MagicMock()
        mock_event_logger.log_api_error = MagicMock()
        mock_event_logger.should_suppress_routine_log = MagicMock(return_value=False)
        
        # Returnera app med mocks
        yield app, mock_event_logger
    
    # Rensa upp dependency overrides
    app.dependency_overrides = {}


# Test clients för normal mode
@pytest.fixture
def test_client_normal(test_app_normal):
    """Create test client for normal mode."""
    app, _ = test_app_normal
    
    # Skapa TestClient som inte startar faktiska asynkrona tjänster
    with TestClient(app) as client:
        yield client


# Test clients för dev mode
@pytest.fixture
def test_client_dev(test_app_dev):
    """Create test client for dev mode."""
    app, _ = test_app_dev
    
    # Skapa TestClient som inte startar faktiska asynkrona tjänster
    with TestClient(app) as client:
        yield client


# === Normal Mode Tests ===

def test_get_bot_status(test_client_normal):
    """Test getting bot status in normal mode."""
    client = test_client_normal
    
    # Act
    response = client.get("/api/bot-status")
    
    # Debug utskrift
    print("Response status code:", response.status_code)
    print("Response body:", response.text)
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "stopped"
    assert data["uptime"] == 0.0
    assert data["thread_alive"] is False
    assert data["cycle_count"] == 0
    assert "dev_mode" in data
    assert data["dev_mode"] is False


def test_start_bot(test_client_normal):
    """Test starting the bot in normal mode."""
    client = test_client_normal
    
    # Act
    response = client.post("/api/bot/start")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "running"
    assert data["dev_mode"] is False


def test_stop_bot(test_client_normal):
    """Test stopping the bot in normal mode."""
    client = test_client_normal
    
    # Förbered för test genom att sätta is_running = True
    mock_manager_normal.bot_manager.is_running = True
    
    # Act
    response = client.post("/api/bot/stop")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "stopped"
    assert data["dev_mode"] is False


def test_start_bot_already_running(test_client_normal):
    """Test starting the bot when it's already running in normal mode."""
    client = test_client_normal
    
    # Förbered för test genom att sätta is_running = True
    mock_manager_normal.bot_manager.is_running = True
    
    # Act
    response = client.post("/api/bot/start")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "already running" in data["message"]
    assert data["status"] == "running"
    assert data["dev_mode"] is False


def test_stop_bot_not_running(test_client_normal):
    """Test stopping the bot when it's not running in normal mode."""
    client = test_client_normal
    
    # Förbered för test genom att sätta is_running = False
    mock_manager_normal.bot_manager.is_running = False
    
    # Act
    response = client.post("/api/bot/stop")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert "not running" in data["message"]
    assert data["status"] == "stopped"
    assert data["dev_mode"] is False


def test_get_bot_status_error(test_client_normal, test_app_normal):
    """Test getting bot status with error."""
    client = test_client_normal
    _, mock_event_logger = test_app_normal
    
    # Simulera ett fel i get_status
    mock_manager_normal.bot_manager.should_raise_error = True
    mock_manager_normal.bot_manager.error_message = "Test error in get_status"
    
    # Act
    with patch("backend.api.bot_control.event_logger", mock_event_logger):
        response = client.get("/api/bot-status")
    
    # Assert
    assert response.status_code == 500
    data = response.json()
    assert "detail" in data
    assert "test error in get_status" in data["detail"].lower()
    assert mock_event_logger.log_api_error.called


# === Dev Mode Tests ===

def test_get_bot_status_dev_mode(test_client_dev):
    """Test getting bot status in dev mode."""
    client = test_client_dev
    
    # Act
    response = client.get("/api/bot-status")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "uptime" in data
    assert "thread_alive" in data
    assert "cycle_count" in data
    assert "dev_mode" in data
    assert data["dev_mode"] is True


def test_start_bot_dev_mode(test_client_dev):
    """Test starting the bot in dev mode."""
    client = test_client_dev
    
    # Act
    response = client.post("/api/bot/start")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "running"
    assert data["dev_mode"] is True
    assert "DEVELOPMENT MODE" in data["message"]


def test_stop_bot_dev_mode(test_client_dev):
    """Test stopping the bot in dev mode."""
    client = test_client_dev
    
    # Förbered för test genom att sätta is_running = True
    mock_manager_dev.bot_manager.is_running = True
    
    # Act
    response = client.post("/api/bot/stop")
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "stopped"
    assert data["dev_mode"] is True


# === Setup och Teardown ===

@pytest.fixture(autouse=True, scope="module")
def setup_teardown():
    """
    Setup and teardown for the module.
    This ensures we don't have any global state affecting other tests.
    """
    # Setup - spara nuvarande miljövariabel
    original_dev_mode = os.environ.get("FASTAPI_DEV_MODE")
    
    # Yield för att låta testerna köras
    yield
    
    # Teardown - återställ miljövariabeln
    if original_dev_mode is not None:
        os.environ["FASTAPI_DEV_MODE"] = original_dev_mode
    elif "FASTAPI_DEV_MODE" in os.environ:
        del os.environ["FASTAPI_DEV_MODE"] 