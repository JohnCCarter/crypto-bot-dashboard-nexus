"""Order management service."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.services.exchange import ExchangeService
from backend.services.validation import (validate_order_data,
                                         validate_trading_pair)


class OrderService:
    """Service for managing trading orders."""

    def __init__(self, exchange_service: ExchangeService):
        """
        Initialize order service.

        Args:
            exchange_service: Exchange service for executing orders
        """
        self.exchange = exchange_service
        self.orders: Dict[str, Dict[str, Any]] = {}

    def place_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a new order.

        Args:
            data: Order data dictionary

        Returns:
            Dict containing order details

        Raises:
            ValueError: If order data is invalid
            ExchangeError: If order placement fails
        """
        # Validate order data
        validation_result = validate_order_data(data)
        if not validation_result["valid"]:
            raise ValueError(f"Invalid order data: {validation_result['errors']}")

        # Validate trading pair
        is_valid, error = validate_trading_pair(data["symbol"])
        if not is_valid:
            raise ValueError(error)

        # Generate order ID
        order_id = str(uuid.uuid4())

        # Create order record
        order = {
            "id": order_id,
            "symbol": data["symbol"],
            "type": data["order_type"],
            "side": data["side"],
            "amount": float(data["amount"]),
            "price": float(data.get("price", 0)),
            "status": "pending",
            "created_at": datetime.utcnow().isoformat(),
            "leverage": float(data.get("leverage", 1.0)),
            "stop_loss": float(data.get("stop_loss", 0)),
            "take_profit": float(data.get("take_profit", 0)),
        }

        try:
            # Execute order on exchange
            exchange_order = self.exchange.create_order(
                symbol=data["symbol"],
                order_type=data["order_type"],
                side=data["side"],
                amount=float(data["amount"]),
                price=float(data.get("price", 0)),
            )

            # Update order with exchange details
            order.update(
                {
                    "status": "open",
                    "exchange_order_id": exchange_order["id"],
                    "filled_amount": 0.0,
                    "remaining_amount": float(data["amount"]),
                }
            )

            # Store order
            self.orders[order_id] = order

            return order

        except Exception as e:
            order["status"] = "failed"
            order["error"] = str(e)
            self.orders[order_id] = order
            raise

    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order status by ID.

        Args:
            order_id: Order identifier

        Returns:
            Order details or None if not found
        """
        if order_id not in self.orders:
            return None

        order = self.orders[order_id]
        if order["status"] == "open":
            try:
                # Update order status from exchange
                exchange_order = self.exchange.fetch_order(
                    order["exchange_order_id"], order["symbol"]
                )

                order.update(
                    {
                        "status": exchange_order["status"],
                        "filled_amount": exchange_order["filled"],
                        "remaining_amount": exchange_order["remaining"],
                    }
                )

            except Exception as e:
                order["error"] = str(e)

        return order

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.

        Args:
            order_id: Order identifier

        Returns:
            True if order was cancelled, False if not found
        """
        if order_id not in self.orders:
            return False

        order = self.orders[order_id]
        if order["status"] not in ["open", "pending"]:
            return False

        try:
            # Cancel order on exchange
            self.exchange.cancel_order(order["exchange_order_id"], order["symbol"])

            order["status"] = "cancelled"
            order["cancelled_at"] = datetime.utcnow().isoformat()
            return True

        except Exception as e:
            order["error"] = str(e)
            return False

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders.

        Args:
            symbol: Optional filter by trading pair

        Returns:
            List of open orders
        """
        open_orders = [
            order for order in self.orders.values() if order["status"] == "open"
        ]

        if symbol:
            open_orders = [order for order in open_orders if order["symbol"] == symbol]

        return open_orders
