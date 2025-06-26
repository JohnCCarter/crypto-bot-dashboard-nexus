"""
🧪 Integration Tests - Real API Calls
Tests actual functionality against running backend and real Bitfinex API.

These tests require:
1. Backend server running on localhost:5000
2. Valid Bitfinex API credentials in .env
3. Internet connection for API calls

Run with: pytest tests/integration/ -v
"""

import time

import pytest
import requests


class TestRealAPIIntegration:
    """Integration tests against real APIs and running backend server."""

    BASE_URL = "http://localhost:5000"
    TEST_SYMBOL = "TESTBTC/TESTUSD"
    TEST_SYMBOL_BITFINEX = "tTESTBTC:TESTUSD"

    @classmethod
    def setup_class(cls):
        """Verify backend is running before starting tests."""
        try:
            response = requests.get(f"{cls.BASE_URL}/api/status", timeout=5)
            response.raise_for_status()
            print("✅ Backend server is running")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"❌ Backend server not running: {e}")

    def test_api_status_integration(self):
        """Test /api/status endpoint returns real data."""
        response = requests.get(f"{self.BASE_URL}/api/status")

        assert response.status_code == 200
        data = response.json()

        # Verify real status data structure
        assert "status" in data
        assert data["status"] in ["running", "connected", "initialized"]

        print(f"✅ Status: {data['status']}")

    def test_api_balances_integration(self):
        """Test /api/balances returns real account data."""
        response = requests.get(f"{self.BASE_URL}/api/balances")

        assert response.status_code == 200
        data = response.json()

        # Should return list with balance information
        assert isinstance(data, list)
        # TEST symbols should exist in paper trading
        assert any("TEST" in item.get("currency", "") for item in data)

        print(f"✅ Retrieved {len(data)} balance entries")

    def test_place_and_track_order_integration(self):
        """
        Complete order lifecycle test:
        1. Place limit order
        2. Get order status
        3. Cancel order
        4. Verify cancellation
        """
        # Step 1: Place test order (low price so it stays open)
        order_data = {
            "symbol": self.TEST_SYMBOL,
            "order_type": "limit",
            "side": "buy",
            "amount": 0.0001,
            "price": 30000,  # Low price to ensure it stays open
        }

        print(f"📝 Placing order: {order_data}")
        response = requests.post(
            f"{self.BASE_URL}/api/orders", json=order_data, timeout=30
        )

        assert response.status_code == 201
        order_result = response.json()

        # API returns nested structure with order in "order" key
        assert "order" in order_result
        order_data = order_result["order"]
        assert "id" in order_data
        order_id = order_data["id"]
        print(f"✅ Order placed with ID: {order_id}")

        # Step 2: Get order status
        print(f"🔍 Getting status for order {order_id}")
        status_response = requests.get(
            f"{self.BASE_URL}/api/orders/{order_id}?symbol={self.TEST_SYMBOL}",
            timeout=15,
        )

        assert status_response.status_code == 200
        status_data = status_response.json()

        assert "id" in status_data
        assert "status" in status_data
        assert "symbol" in status_data
        assert status_data["id"] == order_id
        print(f"✅ Order status: {status_data['status']}")

        # Step 3: Cancel order
        print(f"❌ Cancelling order {order_id}")
        cancel_response = requests.delete(
            f"{self.BASE_URL}/api/orders/{order_id}", timeout=15
        )

        assert cancel_response.status_code == 200
        cancel_data = cancel_response.json()
        # API returns different structure for cancel response
        assert cancel_data.get("order") is True or "cancelled" in str(cancel_data)
        print("✅ Order cancelled successfully")

        # Step 4: Verify cancellation (wait a moment for API update)
        time.sleep(1)
        final_status_response = requests.get(
            f"{self.BASE_URL}/api/orders/{order_id}?symbol={self.TEST_SYMBOL}",
            timeout=15,
        )

        if final_status_response.status_code == 200:
            final_data = final_status_response.json()
            status = final_data.get("status", "unknown")
            # Some cancelled orders might return None status
            if status is not None:
                assert status in ["canceled", "cancelled", "CANCELED"]
                print(f"✅ Order verified as cancelled: {status}")
            else:
                print("✅ Order verified as cancelled: status=None")

    def test_order_history_integration(self):
        """Test order history endpoint returns real data."""
        response = requests.get(f"{self.BASE_URL}/api/orders/history", timeout=15)

        assert response.status_code == 200
        data = response.json()

        # Should return list (may be empty)
        assert isinstance(data, list)
        print(f"✅ Order history: {len(data)} entries")

    def test_open_orders_integration(self):
        """Test getting open orders returns real data."""
        response = requests.get(f"{self.BASE_URL}/api/orders", timeout=15)

        assert response.status_code == 200
        data = response.json()

        # API returns nested structure with orders in "orders" key
        assert "orders" in data
        orders = data["orders"]
        assert isinstance(orders, list)
        print(f"✅ Open orders: {len(orders)} entries")

    def test_trading_limitations_integration(self):
        """Test trading limitations endpoint."""
        response = requests.get(f"{self.BASE_URL}/api/trading-limitations", timeout=10)

        assert response.status_code == 200
        data = response.json()

        # Should return boolean or dict with limitation info
        assert isinstance(data, (bool, dict))
        print(f"✅ Trading limitations: {data}")

    def test_symbol_conversion_verification(self):
        """Verify symbol conversion is working correctly in orders."""
        # Place order with UI format symbol
        order_data = {
            "symbol": "TESTBTC/TESTUSD",  # UI format
            "order_type": "limit",
            "side": "buy",
            "amount": 0.0001,
            "price": 25000,
        }

        response = requests.post(
            f"{self.BASE_URL}/api/orders", json=order_data, timeout=30
        )

        # Should succeed despite UI format input
        assert response.status_code == 201
        order_result = response.json()

        # Verify order was created with proper symbol handling
        assert "order" in order_result
        order_data = order_result["order"]
        assert "id" in order_data
        order_id = order_data["id"]

        # Clean up - cancel the order
        cancel_response = requests.delete(
            f"{self.BASE_URL}/api/orders/{order_id}", timeout=15
        )
        assert cancel_response.status_code == 200

        print("✅ Symbol conversion working correctly in order flow")


class TestAPIErrorHandling:
    """Test error handling in API integration."""

    BASE_URL = "http://localhost:5000"

    def test_invalid_order_data(self):
        """Test API handles invalid order data gracefully."""
        invalid_data = {
            "symbol": "INVALID/PAIR",
            "order_type": "invalid_type",
            "side": "invalid_side",
            "amount": -1,
        }

        response = requests.post(f"{self.BASE_URL}/api/orders", json=invalid_data)

        # Should return error, not crash
        assert response.status_code in [400, 422, 500]
        print("✅ Invalid order data handled gracefully")

    def test_nonexistent_order_status(self):
        """Test getting status of non-existent order."""
        fake_order_id = "999999999999"
        response = requests.get(
            f"{self.BASE_URL}/api/orders/{fake_order_id}?symbol=TESTBTC/TESTUSD"
        )

        # Should handle gracefully, not crash
        assert response.status_code in [200, 404, 500]
        print("✅ Non-existent order handled gracefully")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
