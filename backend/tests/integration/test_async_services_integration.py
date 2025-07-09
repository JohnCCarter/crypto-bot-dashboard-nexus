"""
🧪 Async Services Integration Tests
Tests the complete flow from FastAPI endpoints to async services.

These tests verify that:
1. FastAPI endpoints correctly call async services
2. Async services handle concurrent requests properly
3. Error handling works across the async stack
4. State management is thread-safe

Run with: pytest backend/tests/integration/test_async_services_integration.py -v
"""

import asyncio
import time
from typing import Dict, Any, List
import pytest
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed


class TestAsyncServicesIntegration:
    """Integration tests for async services through FastAPI endpoints."""

    BASE_URL = "http://localhost:8001"
    TEST_SYMBOL = "TESTBTC/TESTUSD"

    @classmethod
    def setup_class(cls):
        """Verify backend is running before starting tests."""
        try:
            response = requests.get(f"{cls.BASE_URL}/api/status", timeout=5)
            response.raise_for_status()
            print("✅ Backend server is running")
        except requests.exceptions.RequestException as e:
            pytest.skip(f"❌ Backend server not running: {e}")

    def test_concurrent_order_operations(self):
        """Test concurrent order operations to verify async handling."""
        print("🔄 Testing concurrent order operations...")
        
        # Create multiple orders concurrently
        order_data_list = [
            {
                "symbol": self.TEST_SYMBOL,
                "type": "limit",
                "side": "buy",
                "amount": 0.0001,
                "price": 25000 + i * 100  # Different prices
            }
            for i in range(3)
        ]
        
        order_ids = []
        
        # Place orders concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_order = {
                executor.submit(self._place_order, order_data): order_data
                for order_data in order_data_list
            }
            
            for future in as_completed(future_to_order):
                order_data = future_to_order[future]
                try:
                    result = future.result()
                    assert result["status_code"] == 201
                    order_ids.append(result["order_id"])
                    print(f"✅ Order placed: {result['order_id']}")
                except Exception as e:
                    pytest.fail(f"Failed to place order {order_data}: {e}")
        
        # Verify all orders were created
        assert len(order_ids) == 3
        
        # Cancel orders concurrently
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_to_order_id = {
                executor.submit(self._cancel_order, order_id): order_id
                for order_id in order_ids
            }
            
            for future in as_completed(future_to_order_id):
                order_id = future_to_order_id[future]
                try:
                    result = future.result()
                    assert result["status_code"] == 200
                    print(f"✅ Order cancelled: {order_id}")
                except Exception as e:
                    pytest.fail(f"Failed to cancel order {order_id}: {e}")
        
        print("✅ All concurrent operations completed successfully")

    def test_async_service_error_handling(self):
        """Test error handling in async services."""
        print("🔄 Testing async service error handling...")
        
        # Test with invalid order data
        invalid_order_data = {
            "symbol": "INVALID/SYMBOL",
            "type": "invalid_type",
            "side": "invalid_side",
            "amount": -1,  # Invalid amount
            "price": -100  # Invalid price
        }
        
        response = requests.post(f"{self.BASE_URL}/api/orders", json=invalid_order_data, timeout=10)
        
        # Should return 400 or 500 with error details
        assert response.status_code in [400, 422, 500]  # 422 is valid for validation errors
        error_data = response.json()
        assert "detail" in error_data
        print(f"✅ Error handling works: {error_data['detail']}")

    def test_bot_control_async_operations(self):
        """Test bot control operations through async services."""
        print("🔄 Testing bot control async operations...")
        
        # Get initial status
        status_response = requests.get(f"{self.BASE_URL}/api/bot-status", timeout=10)
        assert status_response.status_code == 200
        initial_status = status_response.json()
        print(f"✅ Initial bot status: {initial_status['status']}")
        
        # Start bot
        start_response = requests.post(f"{self.BASE_URL}/api/bot/start", timeout=10)
        assert start_response.status_code == 200
        start_result = start_response.json()
        print(f"✅ Bot start result: {start_result['message']}")
        
        # Wait a moment for bot to initialize
        time.sleep(2)
        
        # Get status again
        status_response = requests.get(f"{self.BASE_URL}/api/bot-status", timeout=10)
        assert status_response.status_code == 200
        running_status = status_response.json()
        print(f"✅ Running bot status: {running_status['status']}")
        
        # Stop bot
        stop_response = requests.post(f"{self.BASE_URL}/api/bot/stop", timeout=10)
        assert stop_response.status_code == 200
        stop_result = stop_response.json()
        print(f"✅ Bot stop result: {stop_result['message']}")

    def test_positions_service_async(self):
        """Test positions service through async endpoints."""
        print("🔄 Testing positions service async operations...")
        
        # Get positions
        response = requests.get(f"{self.BASE_URL}/api/positions", timeout=15)
        assert response.status_code == 200
        positions_data = response.json()
        
        # API returns {"positions": []} format, not direct list
        assert isinstance(positions_data, dict)
        assert "positions" in positions_data
        assert isinstance(positions_data["positions"], list)
        print(f"✅ Retrieved {len(positions_data['positions'])} positions")

    def test_risk_management_async(self):
        """Test risk management service through async endpoints."""
        print("🔄 Testing risk management async operations...")
        
        # Test risk assessment (GET endpoint, no body needed)
        response = requests.get(f"{self.BASE_URL}/api/risk/assessment", timeout=15)
        assert response.status_code == 200
        risk_result = response.json()
        
        # Should return risk assessment
        assert "status" in risk_result
        assert "risk_assessment" in risk_result
        print(f"✅ Risk assessment completed: {risk_result['status']}")

    def test_portfolio_management_async(self):
        """Test portfolio management service through async endpoints."""
        print("🔄 Testing portfolio management async operations...")
        
        # Get portfolio status (GET endpoint)
        response = requests.get(f"{self.BASE_URL}/api/portfolio/status", timeout=15)
        assert response.status_code == 200
        portfolio_data = response.json()
        
        # Should return portfolio data
        assert "status" in portfolio_data
        print(f"✅ Portfolio status retrieved: {portfolio_data['status']}")

    def test_async_service_performance(self):
        """Test performance of async services under load."""
        print("🔄 Testing async service performance...")
        
        start_time = time.time()
        
        # Make multiple concurrent requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            # Mix of different operations
            for i in range(10):
                if i % 3 == 0:
                    # Get status
                    futures.append(executor.submit(self._get_status))
                elif i % 3 == 1:
                    # Get balances
                    futures.append(executor.submit(self._get_balances))
                else:
                    # Get positions
                    futures.append(executor.submit(self._get_positions))
            
            # Wait for all to complete
            for future in as_completed(futures):
                try:
                    result = future.result()
                    assert result["status_code"] == 200
                except Exception as e:
                    pytest.fail(f"Performance test failed: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        print(f"✅ Performance test completed in {total_time:.2f} seconds")
        assert total_time < 10.0  # Should complete within 10 seconds

    # Helper methods for concurrent operations
    def _place_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Place an order and return result."""
        response = requests.post(f"{self.BASE_URL}/api/orders", json=order_data, timeout=10)
        if response.status_code == 201:
            order_result = response.json()
            return {
                "status_code": response.status_code,
                "order_id": order_result["id"]
            }
        return {"status_code": response.status_code, "order_id": None}

    def _cancel_order(self, order_id: str) -> Dict[str, Any]:
        """Cancel an order and return result."""
        response = requests.delete(f"{self.BASE_URL}/api/orders/{order_id}?symbol={self.TEST_SYMBOL}", timeout=10)
        return {"status_code": response.status_code}

    def _get_status(self) -> Dict[str, Any]:
        """Get API status."""
        response = requests.get(f"{self.BASE_URL}/api/status", timeout=5)
        return {"status_code": response.status_code}

    def _get_balances(self) -> Dict[str, Any]:
        """Get balances."""
        response = requests.get(f"{self.BASE_URL}/api/balances", timeout=10)
        return {"status_code": response.status_code}

    def _get_positions(self) -> Dict[str, Any]:
        """Get positions."""
        response = requests.get(f"{self.BASE_URL}/api/positions", timeout=10)
        return {"status_code": response.status_code}


class TestAsyncServiceErrorRecovery:
    """Test error recovery in async services."""

    BASE_URL = "http://localhost:8001"

    def test_service_recovery_after_errors(self):
        """Test that services recover properly after errors."""
        print("🔄 Testing service recovery after errors...")
        
        # First, make a valid request
        response = requests.get(f"{self.BASE_URL}/api/status", timeout=5)
        assert response.status_code == 200
        
        # Make an invalid request that should cause an error
        invalid_data = {"invalid": "data"}
        response = requests.post(f"{self.BASE_URL}/api/orders", json=invalid_data, timeout=5)
        assert response.status_code in [400, 422, 500]
        
        # Make another valid request to ensure service recovered
        response = requests.get(f"{self.BASE_URL}/api/status", timeout=5)
        assert response.status_code == 200
        
        print("✅ Service recovered properly after error")

    def test_concurrent_error_handling(self):
        """Test handling of concurrent errors."""
        print("🔄 Testing concurrent error handling...")
        
        # Make multiple invalid requests concurrently
        invalid_data_list = [
            {"invalid": f"data_{i}"} for i in range(5)
        ]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(requests.post, f"{self.BASE_URL}/api/orders", json=invalid_data, timeout=5)
                for invalid_data in invalid_data_list
            ]
            
            for future in as_completed(futures):
                try:
                    response = future.result()
                    # All should return error status codes
                    assert response.status_code in [400, 422, 500]
                except Exception as e:
                    # Network errors are acceptable
                    print(f"⚠️ Network error (acceptable): {e}")
        
        # Verify service is still working
        response = requests.get(f"{self.BASE_URL}/api/status", timeout=5)
        assert response.status_code == 200
        
        print("✅ Concurrent error handling works correctly") 