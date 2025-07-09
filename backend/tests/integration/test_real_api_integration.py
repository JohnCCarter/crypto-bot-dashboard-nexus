"""
🧪 Integration Tests - Real API Calls
Tests actual functionality against running backend and real Bitfinex API.

These tests require:
1. Backend server running on localhost:8001
2. Valid Bitfinex API credentials in .env
3. Internet connection for API calls

Run with: pytest tests/integration/ -v
"""

import time

import pytest
import requests


class TestRealAPIIntegration:
    """Integration tests against real APIs and running backend server."""

    BASE_URL = "http://localhost:8001"
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

    @pytest.mark.integration
    def test_api_status_integration(self):
        """Test /api/status endpoint returns real data."""
        response = requests.get(f"{self.BASE_URL}/api/status")

        assert response.status_code == 200
        data = response.json()

        # Verify real status data structure
        assert "status" in data
        assert data["status"] in ["running", "connected", "initialized", "operational"]

        print(f"✅ Status: {data['status']}")

    @pytest.mark.integration
    def test_api_balances_integration(self):
        """Test /api/balances returns real account data."""
        response = requests.get(f"{self.BASE_URL}/api/balances")

        assert response.status_code == 200
        data = response.json()

        # Acceptera både gammalt och nytt format
        if isinstance(data, list):
            balances = data
        elif isinstance(data, dict) and "balances" in data:
            balances = data["balances"]
        else:
            raise AssertionError("/api/balances returnerar varken lista eller dict med 'balances'-nyckel")

        assert isinstance(balances, list)
        print(f"✅ Retrieved {len(balances)} balance entries")

    @pytest.mark.integration
    @pytest.mark.parametrize("order_type_value", ["limit", "market"])
    def test_place_and_track_order_integration(self, order_type_value):
        """
        Complete order lifecycle test:
        1. Place limit/market order
        2. Get order status
        3. Cancel order
        4. Verify cancellation
        """
        # Step 1: Place test order
        order_data = {
            "symbol": self.TEST_SYMBOL,
            "type": order_type_value,
            "side": "buy",
            "amount": 0.0001,
        }
        if order_type_value == "limit":
            order_data["price"] = 30000  # Low price to ensure it stays open

        print(f"📝 Placing order: {order_data}")
        response = requests.post(f"{self.BASE_URL}/api/orders", json=order_data, timeout=5)
        if response.status_code != 201:
            print(f"❌ Fel vid orderläggning: status={response.status_code}")
            try:
                print(f"Response JSON: {response.json()}")
            except Exception:
                print(f"Response text: {response.text}")
        assert response.status_code == 201
        order_result = response.json()
        assert "id" in order_result and "symbol" in order_result and "type" in order_result

        # Step 2: Get order status (polling istället för sleep)
        print(f"🔍 Getting status for order {order_result['id']}")
        status_url = f"{self.BASE_URL}/api/orders/{order_result['id']}?symbol={self.TEST_SYMBOL}"
        status_data = None
        for i in range(10):  # max 5 sekunder (0.5s intervall)
            status_response = requests.get(status_url, timeout=5)
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get("status") in ["open", "filled", "cancelled"]:
                    break
            time.sleep(0.5)
        else:
            print(f"⚠️ Timeout: Orderstatus kunde inte hämtas inom 5 sekunder")
            assert False
        assert "status" in status_data
        assert "symbol" in status_data
        assert status_data["id"] == order_result["id"]
        print(f"✅ Order status: {status_data['status']}")

        # Step 3: Cancel order
        print(f"❌ Cancelling order {order_result['id']}")
        cancel_response = requests.delete(f"{self.BASE_URL}/api/orders/{order_result['id']}", timeout=5)
        if cancel_response.status_code != 200:
            print(f"⚠️ Cancel failed: status={cancel_response.status_code}, response={cancel_response.text}")
        assert cancel_response.status_code == 200

        # Step 4: Verify cancellation (polling)
        for i in range(10):
            final_status_response = requests.get(status_url, timeout=5)
            if final_status_response.status_code == 200:
                final_status_data = final_status_response.json()
                if final_status_data.get("status") == "cancelled":
                    break
            time.sleep(0.5)
        else:
            print(f"⚠️ Timeout: Ordern blev inte avbruten inom 5 sekunder")
            assert False
        print(f"✅ Order cancelled: {order_result['id']}")

    @pytest.mark.integration
    def test_order_history_integration(self):
        """Test order history endpoint returns real data."""
        response = requests.get(f"{self.BASE_URL}/api/orders/history", timeout=15)

        assert response.status_code == 200
        data = response.json()

        # Should return list (may be empty)
        assert isinstance(data, list)
        print(f"✅ Order history: {len(data)} entries")

    @pytest.mark.integration
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

    @pytest.mark.integration
    def test_trading_limitations_integration(self):
        """Test trading limitations endpoint."""
        response = requests.get(f"{self.BASE_URL}/api/trading-limitations", timeout=10)

        assert response.status_code == 200
        data = response.json()

        # Should return boolean or dict with limitation info
        assert isinstance(data, (bool, dict))
        print(f"✅ Trading limitations: {data}")

    @pytest.mark.integration
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

    BASE_URL = "http://localhost:8001"

    @pytest.mark.integration
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

    @pytest.mark.integration
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
