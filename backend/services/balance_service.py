"""Balance service using shared exchange service to avoid nonce conflicts."""

from flask import current_app


def get_shared_exchange_service():
    """Get shared exchange service from app context to avoid nonce conflicts."""
    try:
        if hasattr(current_app, "_services") and current_app._services:
            return current_app._services.get("exchange")
        
        current_app.logger.warning(
            "Exchange service not available in app context"
        )
        return None
    except Exception as e:
        current_app.logger.error(
            f"Failed to get shared exchange service: {e}"
        )
        return None


def fetch_balances():
    """
    Hämtar saldon från Bitfinex via shared exchange service.
    Använder thread-safe shared connection för att undvika nonce conflicts.
    :return: dict med balansdata från exchange
    :raises: ValueError, ExchangeError
    """
    exchange_service = get_shared_exchange_service()
    if not exchange_service:
        raise ValueError(
            "Exchange service not available - check API configuration"
        )
    
    try:
        # Use shared exchange service (thread-safe nonce handling)
        balance_dict = exchange_service.fetch_balance()
        
        # Convert to expected format for API response
        balance_list = []
        for currency, amount in balance_dict.items():
            if amount > 0:  # Only include non-zero balances
                balance_list.append({
                    "currency": currency,
                    "available": amount,
                    "total_balance": amount
                })
        
        return balance_list
        
    except Exception as e:
        current_app.logger.error(f"Failed to fetch balances: {e}")
        raise
