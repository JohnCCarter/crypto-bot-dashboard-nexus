#!/usr/bin/env python3
"""Debug script to test API call directly."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from fastapi_app import app

def test_api_call():
    """Test the API call directly."""
    
    client = TestClient(app)
    
    # Test data
    order_data = {
        "symbol": "BTC/USD",
        "side": "buy",
        "type": "limit",
        "amount": 0.1,
        "price": 13000.0,
        "stop_price": None,
        "take_profit": 14000.0,
        "stop_loss": 12000.0
    }
    
    print("Testing API call with data:")
    print(f"  {order_data}")
    
    try:
        # Test 1: Direct JSON (current test format)
        print("\nTest 1: Direct JSON")
        response = client.post("/api/risk/validate/order", json=order_data)
        print(f"Response status: {response.status_code}")
        if response.status_code == 422:
            error_data = response.json()
            print(f"422 error details: {error_data}")
        
        # Test 2: Wrapped in order_data
        print("\nTest 2: Wrapped in order_data")
        wrapped_data = {"order_data": order_data}
        response2 = client.post("/api/risk/validate/order", json=wrapped_data)
        print(f"Response status: {response2.status_code}")
        if response2.status_code == 422:
            error_data = response2.json()
            print(f"422 error details: {error_data}")
        else:
            print(f"Response body: {response2.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_api_call() 