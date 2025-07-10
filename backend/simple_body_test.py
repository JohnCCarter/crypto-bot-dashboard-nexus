#!/usr/bin/env python3
"""Simple test to understand our specific Body(...) problem."""

from fastapi import Body, FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI()


class OrderData(BaseModel):
    symbol: str
    side: str
    type: str
    amount: float
    price: float


# Test our exact scenario
@app.post("/test")
async def test(order_data: OrderData = Body(..., embed=False)):
    return {"received": order_data.model_dump()}


def test_our_scenario():
    """Test our exact scenario."""
    client = TestClient(app)

    order_data = {
        "symbol": "BTC/USD",
        "side": "buy",
        "type": "limit",
        "amount": 0.1,
        "price": 13000.0,
    }

    print("=== Testing our exact scenario ===\n")

    print("Sending direct JSON:")
    print(f"  {order_data}")
    try:
        response = client.post("/test", json=order_data)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"  Error: {e}")
    print()

    print("Sending wrapped JSON:")
    wrapped_data = {"order_data": order_data}
    print(f"  {wrapped_data}")
    try:
        response = client.post("/test", json=wrapped_data)
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.json()}")
    except Exception as e:
        print(f"  Error: {e}")
    print()


if __name__ == "__main__":
    test_our_scenario()
