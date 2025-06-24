"""
📋 Integrated Order Service - SUPABASE VERSION
==============================================
Ersätter den gamla OrderService som använde self.orders = {} dictionary
Nu använder Supabase för persistent order storage.
"""

import uuid
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.services.exchange import ExchangeService
from backend.services.validation import validate_order_data, validate_trading_pair
from backend.services.simple_database_service import simple_db

logger = logging.getLogger(__name__)


class IntegratedOrderService:
    """
    📋 Order Service with Supabase Integration
    
    ERSÄTTER: gamla OrderService som använde self.orders = {} dictionary
    ANVÄNDER: Supabase för persistent order storage
    """

    def __init__(self, exchange_service: ExchangeService):
        """Initialize order service with Supabase integration."""
        self.exchange = exchange_service
        self.db = simple_db
        
        logger.info("✅ IntegratedOrderService initialized with Supabase")

    def place_order(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Place a new order with persistent storage.
        
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

        try:
            # Execute order on exchange first
            exchange_order = self.exchange.create_order(
                symbol=data["symbol"],
                order_type=data["order_type"],
                side=data["side"],
                amount=float(data["amount"]),
                price=float(data.get("price", 0)),
            )

            # Create order record in database (PERSISTENT!)
            order_data = {
                'symbol': data["symbol"],
                'order_type': data["order_type"],
                'side': data["side"],
                'amount': str(data["amount"]),
                'price': str(data.get("price", 0)),
                'status': 'open',
                'exchange_order_id': exchange_order["id"],
                'filled_amount': "0.0",
                'remaining_amount': str(data["amount"]),
                'metadata': {
                    'internal_order_id': order_id,
                    'leverage': float(data.get("leverage", 1.0)),
                    'stop_loss': float(data.get("stop_loss", 0)),
                    'take_profit': float(data.get("take_profit", 0)),
                    'created_at': datetime.utcnow().isoformat(),
                }
            }

            # Store in database
            db_order = self.db.client.table('orders').insert(order_data).execute()
            
            if db_order.data:
                stored_order = db_order.data[0]
                logger.info(f"✅ Order stored in database: {order_id} ({data['symbol']} {data['side']})")
                
                # Create trade record as well
                trade_record = self.db.create_trade(
                    symbol=data["symbol"],
                    side=data["side"],
                    amount=float(data["amount"]),
                    price=float(data.get("price", 0))
                )
                
                # Return combined order info
                return {
                    "id": order_id,
                    "database_id": stored_order["id"],
                    "trade_id": trade_record.get("id"),
                    "symbol": data["symbol"],
                    "type": data["order_type"],
                    "side": data["side"],
                    "amount": float(data["amount"]),
                    "price": float(data.get("price", 0)),
                    "status": "open",
                    "exchange_order_id": exchange_order["id"],
                    "created_at": stored_order["created_at"],
                    "filled_amount": 0.0,
                    "remaining_amount": float(data["amount"]),
                }
            else:
                raise Exception("Failed to store order in database")

        except Exception as e:
            # Store failed order for tracking
            failed_order_data = {
                'symbol': data["symbol"],
                'order_type': data["order_type"],
                'side': data["side"],
                'amount': str(data["amount"]),
                'price': str(data.get("price", 0)),
                'status': 'failed',
                'metadata': {
                    'internal_order_id': order_id,
                    'error': str(e),
                    'created_at': datetime.utcnow().isoformat(),
                }
            }
            
            try:
                self.db.client.table('orders').insert(failed_order_data).execute()
            except:
                pass  # Don't fail if we can't store the failure
            
            logger.error(f"❌ Order placement failed: {e}")
            raise

    def get_order_status(self, order_id: str) -> Optional[Dict[str, Any]]:
        """
        Get order status by ID from database.
        
        Args:
            order_id: Order identifier (internal or database ID)

        Returns:
            Order details or None if not found
        """
        try:
            # Try to find by internal order ID first
            result = (self.db.client.table('orders')
                     .select('*')
                     .eq('metadata->>internal_order_id', order_id)
                     .execute())
            
            if not result.data:
                # Try by database ID
                try:
                    db_id = int(order_id)
                    result = (self.db.client.table('orders')
                             .select('*')
                             .eq('id', db_id)
                             .execute())
                except ValueError:
                    pass
            
            if not result.data:
                logger.warning(f"⚠️ Order not found: {order_id}")
                return None

            order = result.data[0]
            
            # Update order status from exchange if it's still open
            if order["status"] == "open" and order.get("exchange_order_id"):
                try:
                    exchange_order = self.exchange.fetch_order(
                        order["exchange_order_id"], order["symbol"]
                    )

                    # Update order in database with fresh exchange data
                    update_data = {
                        'status': exchange_order["status"],
                        'filled_amount': str(exchange_order["filled"]),
                        'remaining_amount': str(exchange_order["remaining"]),
                    }
                    
                    self.db.client.table('orders').update(update_data).eq('id', order['id']).execute()
                    
                    # Update our local order data
                    order.update(update_data)
                    
                    logger.debug(f"📊 Order status updated: {order_id} -> {exchange_order['status']}")

                except Exception as e:
                    logger.warning(f"⚠️ Could not update order status from exchange: {e}")

            return self._format_order_response(order)

        except Exception as e:
            logger.error(f"❌ Failed to get order status: {e}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an existing order.
        
        Args:
            order_id: Order identifier

        Returns:
            True if order was cancelled, False if not found or failed
        """
        order = self.get_order_status(order_id)
        if not order:
            return False

        if order["status"] not in ["open", "pending"]:
            logger.warning(f"⚠️ Cannot cancel order {order_id}: status is {order['status']}")
            return False

        try:
            # Cancel order on exchange
            self.exchange.cancel_order(order["exchange_order_id"], order["symbol"])

            # Update order status in database
            update_data = {
                'status': 'cancelled',
                'metadata': {
                    **order.get('metadata', {}),
                    'cancelled_at': datetime.utcnow().isoformat()
                }
            }
            
            self.db.client.table('orders').update(update_data).eq('id', order['database_id']).execute()
            
            logger.info(f"✅ Order cancelled: {order_id}")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to cancel order {order_id}: {e}")
            return False

    def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get all open orders from database.
        
        Args:
            symbol: Optional filter by trading pair

        Returns:
            List of open orders
        """
        try:
            query = self.db.client.table('orders').select('*').eq('status', 'open')
            
            if symbol:
                query = query.eq('symbol', symbol)
            
            result = query.execute()
            
            orders = [self._format_order_response(order) for order in result.data]
            
            logger.debug(f"📊 Retrieved {len(orders)} open orders" + (f" for {symbol}" if symbol else ""))
            return orders

        except Exception as e:
            logger.error(f"❌ Failed to get open orders: {e}")
            return []

    def get_all_orders(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get all orders from database."""
        try:
            result = (self.db.client.table('orders')
                     .select('*')
                     .order('created_at', desc=True)
                     .limit(limit)
                     .execute())
            
            orders = [self._format_order_response(order) for order in result.data]
            
            logger.debug(f"📊 Retrieved {len(orders)} total orders")
            return orders

        except Exception as e:
            logger.error(f"❌ Failed to get all orders: {e}")
            return []

    def _format_order_response(self, db_order: Dict[str, Any]) -> Dict[str, Any]:
        """Format database order record for API response."""
        metadata = db_order.get('metadata', {})
        
        return {
            "id": metadata.get('internal_order_id', str(db_order['id'])),
            "database_id": db_order['id'],
            "symbol": db_order['symbol'],
            "type": db_order['order_type'],
            "side": db_order['side'],
            "amount": float(db_order['amount']),
            "price": float(db_order['price']),
            "status": db_order['status'],
            "exchange_order_id": db_order.get('exchange_order_id'),
            "created_at": db_order['created_at'],
            "filled_amount": float(db_order.get('filled_amount', 0)),
            "remaining_amount": float(db_order.get('remaining_amount', 0)),
            "leverage": metadata.get('leverage', 1.0),
            "stop_loss": metadata.get('stop_loss', 0),
            "take_profit": metadata.get('take_profit', 0),
            "error": metadata.get('error'),
        }


# Global integrated order service instance
# Will be initialized with actual exchange service when needed
integrated_order_service = None  # Initialize with exchange service in app.py