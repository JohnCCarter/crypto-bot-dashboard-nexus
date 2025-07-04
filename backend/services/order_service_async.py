"""Order management service - async version."""

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.services.exchange import ExchangeService
from backend.services.exchange_async import (
    create_order_async,
    fetch_order_async,
    cancel_order_async,
    fetch_open_orders_async
)
from backend.services.validation import validate_order_data, validate_trading_pair


class OrderServiceAsync:
    """Async service for managing trading orders."""

    def __init__(self, exchange_service: ExchangeService):
        """
        Initialize order service.

        Args:
            exchange_service: Exchange service for executing orders
        """
        self.exchange = exchange_service
        self.orders: Dict[str, Dict[str, Any]] = {}

    async def place_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a new order asynchronously.

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
            # Execute order on exchange using async method
            exchange_order = await create_order_async(
                exchange=self.exchange,
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

    async def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order status by ID asynchronously.

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
                # Update order status from exchange using async method
                exchange_order = await fetch_order_async(
                    exchange=self.exchange,
                    order_id=order["exchange_order_id"],
                    symbol=order["symbol"]
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

    async def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order asynchronously.

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
            # Cancel order on exchange using async method
            await cancel_order_async(
                exchange=self.exchange,
                order_id=order["exchange_order_id"],
                symbol=order["symbol"]
            )

            order["status"] = "cancelled"
            order["cancelled_at"] = datetime.utcnow().isoformat()
            return True

        except Exception as e:
            order["error"] = str(e)
            return False

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders asynchronously.

        Args:
            symbol: Optional filter by trading pair

        Returns:
            List of open orders
        """
        # First, try to get open orders from the exchange
        try:
            exchange_orders = await fetch_open_orders_async(
                exchange=self.exchange,
                symbol=symbol
            )
            
            # Update local order cache with exchange data
            for exchange_order in exchange_orders:
                order_id = None
                # Find matching order in local cache by exchange_order_id
                for local_id, local_order in self.orders.items():
                    if local_order.get("exchange_order_id") == exchange_order["id"]:
                        order_id = local_id
                        break
                
                if order_id:
                    # Update existing order
                    self.orders[order_id].update({
                        "status": exchange_order["status"],
                        "filled_amount": exchange_order["filled"],
                        "remaining_amount": exchange_order["remaining"],
                    })
                else:
                    # Create new order entry if not in local cache
                    new_id = str(uuid.uuid4())
                    self.orders[new_id] = {
                        "id": new_id,
                        "exchange_order_id": exchange_order["id"],
                        "symbol": exchange_order["symbol"],
                        "type": exchange_order["type"],
                        "side": exchange_order["side"],
                        "amount": float(exchange_order["amount"]),
                        "price": float(exchange_order.get("price", 0)),
                        "status": exchange_order["status"],
                        "filled_amount": float(exchange_order.get("filled", 0)),
                        "remaining_amount": float(exchange_order.get("remaining", 0)),
                        "created_at": datetime.utcnow().isoformat(),
                    }
        except Exception as e:
            # If exchange call fails, just use local cache
            pass
        
        # Return orders from local cache
        open_orders = [
            order for order in self.orders.values() if order["status"] == "open"
        ]

        if symbol:
            open_orders = [order for order in open_orders if order["symbol"] == symbol]

        return open_orders


# Singleton instance
_order_service_async: Optional[OrderServiceAsync] = None


async def get_order_service_async(
    exchange_service: ExchangeService
) -> OrderServiceAsync:
    """
    Get or create a singleton instance of OrderServiceAsync.
    
    Args:
        exchange_service: Exchange service instance
        
    Returns:
        OrderServiceAsync: Async order service instance
    """
    global _order_service_async
    if _order_service_async is None:
        _order_service_async = OrderServiceAsync(exchange_service)
    return _order_service_async 