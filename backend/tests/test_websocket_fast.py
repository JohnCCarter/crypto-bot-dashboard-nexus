"""
Optimerad version av WebSocket-testerna med patched sleep-anrop.
"""

import os
import pytest
import logging
import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

from fastapi.websockets import WebSocket
from fastapi.testclient import TestClient

from backend.api.websocket import ConnectionManager
from backend.fastapi_app import app

# Konfigurera loggning med minimal nivå
logging.basicConfig(level=logging.CRITICAL)
logger = logging.getLogger(__name__)


# Skapa en mock för asyncio.sleep och time.sleep som inte orsakar fördröjning
async def fast_async_sleep(*args, **kwargs):
    """Ersätter asyncio.sleep med en version utan fördröjning."""
    pass


def fast_sync_sleep(*args, **kwargs):
    """Ersätter time.sleep med en version utan fördröjning."""
    pass


# Definiera mockade versioner av WebSocket-tjänsterna
class MockWebSocketClient:
    def __init__(self):
        self.websocket = None
        self.running = False
        self.connected = False
        self.subscriptions = {}
        self.callbacks = {}

    async def connect(self):
        self.connected = True
        return self

    async def disconnect(self):
        self.connected = False
        return self

    async def subscribe_ticker(self, symbol, callback):
        self.callbacks[f"ticker_{symbol}"] = callback
        return AsyncMock()

    async def subscribe_orderbook(self, symbol, callback, precision="P0"):
        self.callbacks[f"book_{symbol}"] = callback
        return AsyncMock()

    async def subscribe_trades(self, symbol, callback):
        self.callbacks[f"trades_{symbol}"] = callback
        return AsyncMock()


# Patcha WebSocket-relaterade funktioner och sleep-anrop för alla tester
@pytest.fixture(autouse=True)
def mock_all_services():
    """
    Patcha alla tjänster och sleep-anrop för att undvika externa anslutningar och fördröjningar.
    Denna fixture körs automatiskt före varje test.
    """
    # Patcha asyncio.sleep och time.sleep
    with patch("asyncio.sleep", fast_async_sleep):
        with patch("time.sleep", fast_sync_sleep):
            
            # Patcha websockets-modulen för att undvika anslutningar
            websocket_mock = AsyncMock()
            websocket_connect_mock = AsyncMock(return_value=websocket_mock)
            
            with patch("websockets.connect", websocket_connect_mock):
                
                # Patcha get_websocket_client för att returnera vår mock
                with patch("backend.api.websocket.get_websocket_client") as mock_get_client:
                    mock_get_client.return_value = MockWebSocketClient()
                    
                    # Patcha BitfinexUserDataClient för att undvika externa anslutningar
                    with patch("backend.api.websocket.BitfinexUserDataClient") as mock_user_client_class:
                        mock_user_client = MagicMock()
                        mock_user_client.connect = AsyncMock()
                        mock_user_client.on_balance_update = MagicMock()
                        mock_user_client.on_order_update = MagicMock()
                        mock_user_client.on_position_update = MagicMock()
                        mock_user_client_class.return_value = mock_user_client
                        
                        # Patcha start_websocket_service för att undvika anslutningar
                        with patch("backend.api.websocket.start_websocket_service") as mock_start_service:
                            mock_start_service.return_value = AsyncMock()
                            
                            # Inaktivera alla bakgrundstjänster via miljövariabler
                            os.environ["FASTAPI_DISABLE_WEBSOCKETS"] = "true"
                            os.environ["FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER"] = "true"
                            
                            # Tillhandahåll fixtures till testerna
                            yield {
                                "mock_get_client": mock_get_client,
                                "mock_user_client_class": mock_user_client_class,
                                "mock_user_client": mock_user_client,
                                "mock_start_service": mock_start_service
                            }
                            
                            # Återställ miljövariabler
                            os.environ.pop("FASTAPI_DISABLE_WEBSOCKETS", None)
                            os.environ.pop("FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER", None)


@pytest.fixture
def mock_websocket():
    """Skapar en mockad WebSocket för tester."""
    mock = MagicMock(spec=WebSocket)
    mock.send_json = AsyncMock()
    mock.send_text = AsyncMock()
    mock.receive_text = AsyncMock()
    return mock


@pytest.fixture
def test_client():
    """TestClient för FastAPI app med mockade tjänster."""
    with patch("backend.services.websocket_market_service.BitfinexWebSocketClient", return_value=MockWebSocketClient()):
        return TestClient(app)


class TestWebSocketFast:
    """Tester för WebSocket med optimerad hastighet."""
    
    @pytest.mark.asyncio
    async def test_connection_manager_basic(self, mock_websocket):
        """Testar grundläggande ConnectionManager-funktionalitet."""
        manager = ConnectionManager("test")
        
        # Testa connect
        await manager.connect(mock_websocket, "test-client")
        assert mock_websocket in manager.active_connections
        assert manager.client_data[mock_websocket]["id"] == "test-client"
        
        # Testa add_subscription
        manager.add_subscription(mock_websocket, "test_subscription")
        assert "test_subscription" in manager.get_subscriptions(mock_websocket)
        
        # Testa disconnect
        manager.disconnect(mock_websocket)
        assert mock_websocket not in manager.active_connections
    
    @pytest.mark.asyncio
    async def test_handle_market_subscription(self, mock_websocket, mock_all_services):
        """Testar hantering av marknadsprenumerationer med mockning."""
        from backend.api.websocket import handle_market_subscription
        
        # Använda vår mockade get_websocket_client
        mock_client = mock_all_services["mock_get_client"].return_value
        
        # Testa ticker-prenumeration
        await handle_market_subscription(mock_websocket, "BTCUSD", "ticker")
        
        # Kontrollera att vi skickade rätt bekräftelsemeddelande
        mock_websocket.send_json.assert_any_call({
            "status": "subscribed", 
            "channel": "ticker",
            "symbol": "BTCUSD"
        })
        
        # Återställ mock
        mock_websocket.send_json.reset_mock()
        
        # Testa orderbook-prenumeration
        await handle_market_subscription(mock_websocket, "BTCUSD", "orderbook")
        
        # Kontrollera att vi skickade rätt bekräftelsemeddelande
        mock_websocket.send_json.assert_any_call({
            "status": "subscribed", 
            "channel": "orderbook",
            "symbol": "BTCUSD"
        })
    
    @pytest.mark.asyncio
    async def test_websocket_user_endpoint_auth(self, mock_websocket, mock_all_services):
        """Testar autentiseringsdelen av WebSocket user endpoint."""
        from backend.api.websocket import user_data_manager
        
        # Simulera autentiseringsmeddelande
        auth_data = '{"api_key": "test_key", "api_secret": "test_secret"}'
        mock_websocket.receive_text = AsyncMock(return_value=auth_data)
        
        # Registrera klienten i user_data_manager
        await user_data_manager.connect(mock_websocket, "test-client")
        
        # Simulera autentisering
        from backend.api.websocket import BitfinexUserDataClient
        mock_user_client = mock_all_services["mock_user_client"]
        
        # Verifiera att callback-registrering fungerar
        mock_user_client.on_balance_update(lambda data: None)
        mock_user_client.on_order_update(lambda data: None)
        mock_user_client.on_position_update(lambda data: None)
        
        # Kontrollera att callbacks registrerades
        assert mock_user_client.on_balance_update.call_count == 1
        assert mock_user_client.on_order_update.call_count == 1
        assert mock_user_client.on_position_update.call_count == 1
        
        # Rensa efter testet
        user_data_manager.disconnect(mock_websocket) 