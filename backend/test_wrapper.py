#!/usr/bin/env python3
"""Test if wrapper works with our endpoint."""

from fastapi.testclient import TestClient

from fastapi_app import app


def test_wrapper():
    """Test if wrapper works."""
    client = TestClient(app)

    order_data = {
        "symbol": "BTC/USD",
        "side": "buy",
        "type": "limit",
        "amount": 0.1,
        "price": 13000.0,
        "stop_price": None,
        "take_profit": 14000.0,
        "stop_loss": 12000.0,
    }

    print("=== Testing wrapper approach ===\n")

    print("Test 1: Direct JSON (current failing approach)")
    try:
        response = client.post("/api/risk/validate/order", json=order_data)
        print(f"  Status: {response.status_code}")
        if response.status_code == 422:
            print(f"  Error: {response.json()}")
    except Exception as e:
        print(f"  Exception: {e}")
    print()

    print("Test 2: Wrapped JSON")
    wrapped_data = {"order_data": order_data}
    try:
        response = client.post("/api/risk/validate/order", json=wrapped_data)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            print(f"  Success: {response.json()}")
        else:
            print(f"  Error: {response.json()}")
    except Exception as e:
        print(f"  Exception: {e}")
    print()


if __name__ == "__main__":
    test_wrapper()
