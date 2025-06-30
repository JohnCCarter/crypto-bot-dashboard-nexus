"""
Tester för BitfinexClientWrapper-klassen.
"""

import unittest
from unittest.mock import patch, MagicMock
import asyncio
import pytest

from backend.services.bitfinex_client_wrapper import BitfinexClientWrapper


class TestBitfinexClientWrapper(unittest.TestCase):
    """Test suite för BitfinexClientWrapper."""

    def setUp(self):
        """Konfigurerar testmiljön."""
        self.api_key = "test_api_key"
        self.api_secret = "test_api_secret"
        self.client = BitfinexClientWrapper(
            api_key=self.api_key, 
            api_secret=self.api_secret
        )
        
    @patch("backend.services.bitfinex_client_wrapper.Client")
    def test_initialization(self, mock_client):
        """Testar att klienten initialiseras korrekt."""
        # Arrange
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        # Act
        client = BitfinexClientWrapper(
            api_key=self.api_key, 
            api_secret=self.api_secret
        )
        
        # Assert
        mock_client.assert_called_once_with(
            api_key=self.api_key,
            api_secret=self.api_secret,
            rest_kwargs={},
            wss_kwargs={"create_event_emitter": True}
        )
        self.assertEqual(client.api_key, self.api_key)
        self.assertEqual(client.api_secret, self.api_secret)
        self.assertFalse(client.is_ws_connected)
        self.assertFalse(client.is_ws_authenticated)
        
    @patch("backend.services.bitfinex_client_wrapper.asyncio.new_event_loop")
    @patch("backend.services.bitfinex_client_wrapper.Client")
    def test_connect_websocket(self, mock_client, mock_event_loop):
        """Testar att WebSocket-anslutningen fungerar."""
        # Arrange
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        mock_loop = MagicMock()
        mock_event_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = True
        
        client = BitfinexClientWrapper(
            api_key=self.api_key, 
            api_secret=self.api_secret
        )
        
        # Act
        result = client.connect_websocket()
        
        # Assert
        self.assertTrue(result)
        mock_loop.run_until_complete.assert_called_once()
        mock_loop.close.assert_called_once()
        
    @patch("backend.services.bitfinex_client_wrapper.asyncio.new_event_loop")
    @patch("backend.services.bitfinex_client_wrapper.Client")
    def test_place_order(self, mock_client, mock_event_loop):
        """Testar att placera en order."""
        # Arrange
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        mock_loop = MagicMock()
        mock_event_loop.return_value = mock_loop
        
        # Simulera ett lyckat ordersvar
        mock_order_response = {
            "id": 123456,
            "symbol": "tBTCUSD",
            "price": "30000",
            "amount": "0.1",
            "status": 0
        }
        mock_loop.run_until_complete.return_value = mock_order_response
        
        client = BitfinexClientWrapper(
            api_key=self.api_key, 
            api_secret=self.api_secret
        )
        
        # Act
        result = client.place_order(
            symbol="tBTCUSD",
            amount=0.1,
            price=30000,
            order_type="LIMIT"
        )
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["order"], mock_order_response)
        mock_loop.run_until_complete.assert_called_once()
        mock_loop.close.assert_called_once()
        
    @patch("backend.services.bitfinex_client_wrapper.asyncio.new_event_loop")
    @patch("backend.services.bitfinex_client_wrapper.Client")
    def test_get_wallet_balances(self, mock_client, mock_event_loop):
        """Testar att hämta plånbokssaldon."""
        # Arrange
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        mock_loop = MagicMock()
        mock_event_loop.return_value = mock_loop
        
        # Simulera ett lyckat balansvar
        mock_balance_response = [
            ["exchange", "BTC", 0.5, 0, 0.5],
            ["exchange", "USD", 10000, 0, 10000]
        ]
        mock_loop.run_until_complete.return_value = mock_balance_response
        
        client = BitfinexClientWrapper(
            api_key=self.api_key, 
            api_secret=self.api_secret
        )
        
        # Act
        result = client.get_wallet_balances()
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["balances"], mock_balance_response)
        mock_loop.run_until_complete.assert_called_once()
        mock_loop.close.assert_called_once()
        
    @patch("backend.services.bitfinex_client_wrapper.asyncio.new_event_loop")
    @patch("backend.services.bitfinex_client_wrapper.Client")
    def test_get_ticker(self, mock_client, mock_event_loop):
        """Testar att hämta ticker-information."""
        # Arrange
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        mock_loop = MagicMock()
        mock_event_loop.return_value = mock_loop
        
        # Simulera ett lyckat tickersvar
        # Bitfinex ticker format: [BID, BID_SIZE, ASK, ASK_SIZE, DAILY_CHANGE, DAILY_CHANGE_RELATIVE, 
        # LAST_PRICE, VOLUME, HIGH, LOW]
        mock_ticker_response = [
            29900, 10.5, 30000, 5.2, 100, 0.003, 29950, 1500, 30100, 29800
        ]
        mock_loop.run_until_complete.return_value = mock_ticker_response
        
        client = BitfinexClientWrapper(
            api_key=self.api_key, 
            api_secret=self.api_secret
        )
        
        # Act
        result = client.get_ticker(symbol="tBTCUSD")
        
        # Assert
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["ticker"], mock_ticker_response)
        mock_loop.run_until_complete.assert_called_once()
        mock_loop.close.assert_called_once()
        
    @patch("backend.services.bitfinex_client_wrapper.asyncio.new_event_loop")
    @patch("backend.services.bitfinex_client_wrapper.Client")
    def test_register_ws_callback(self, mock_client, mock_event_loop):
        """Testar att registrera en WebSocket-callback."""
        # Arrange
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        client = BitfinexClientWrapper(
            api_key=self.api_key, 
            api_secret=self.api_secret
        )
        
        # Mock callback
        mock_callback = MagicMock()
        
        # Act
        client.register_ws_callback("ticker", mock_callback)
        
        # Assert
        mock_instance.wss.on.assert_called_with("ticker", mock_callback)
        self.assertIn("ticker", client.ws_callbacks)
        self.assertEqual(client.ws_callbacks["ticker"], mock_callback)
        
    @patch("backend.services.bitfinex_client_wrapper.asyncio.new_event_loop")
    @patch("backend.services.bitfinex_client_wrapper.Client")
    def test_exception_handling(self, mock_client, mock_event_loop):
        """Testar att felhantering fungerar korrekt."""
        # Arrange
        mock_instance = MagicMock()
        mock_client.return_value = mock_instance
        
        mock_loop = MagicMock()
        mock_event_loop.return_value = mock_loop
        
        # Simulera ett fel
        mock_loop.run_until_complete.side_effect = Exception("API Error")
        
        client = BitfinexClientWrapper(
            api_key=self.api_key, 
            api_secret=self.api_secret
        )
        
        # Act
        result = client.get_ticker(symbol="tBTCUSD")
        
        # Assert
        self.assertEqual(result["status"], "error")
        self.assertEqual(result["message"], "API Error")
        mock_loop.run_until_complete.assert_called_once()
        mock_loop.close.assert_called_once()


if __name__ == "__main__":
    unittest.main() 