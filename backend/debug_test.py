#!/usr/bin/env python3
"""Debug script to test OrderData validation."""

import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api.models import OrderData, OrderSide, OrderType


def test_order_data_validation():
    """Test OrderData validation with different inputs."""

    print("Testing OrderData validation...")
    print(f"OrderSide.BUY = {OrderSide.BUY}")
    print(f"OrderType.LIMIT = {OrderType.LIMIT}")

    # Test 1: Using enum values
    try:
        order_data_enum = OrderData(
            symbol="BTC/USD",
            side=OrderSide.BUY,
            type=OrderType.LIMIT,
            amount=0.1,
            price=13000.0,
            stop_price=None,
            take_profit=14000.0,
            stop_loss=12000.0,
        )
        print("✅ Test 1 PASSED: Using enum values")
        print(f"   side: {order_data_enum.side} (type: {type(order_data_enum.side)})")
        print(f"   type: {order_data_enum.type} (type: {type(order_data_enum.type)})")
    except Exception as e:
        print(f"❌ Test 1 FAILED: {e}")

    # Test 2: Using string values
    try:
        order_data_string = OrderData(
            symbol="BTC/USD",
            side="buy",
            type="limit",
            amount=0.1,
            price=13000.0,
            stop_price=None,
            take_profit=14000.0,
            stop_loss=12000.0,
        )
        print("✅ Test 2 PASSED: Using string values")
        print(
            f"   side: {order_data_string.side} (type: {type(order_data_string.side)})"
        )
        print(
            f"   type: {order_data_string.type} (type: {type(order_data_string.type)})"
        )
    except Exception as e:
        print(f"❌ Test 2 FAILED: {e}")


if __name__ == "__main__":
    test_order_data_validation()
