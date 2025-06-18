"""Validation utilities for trading operations."""

from typing import Any, Dict, Tuple


def validate_order_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate order data before processing.

    Args:
        data: Order data dictionary

    Returns:
        Dict containing validation result and any errors
    """
    errors = []

    # Required fields
    required_fields = ["symbol", "order_type", "side", "amount"]
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Validate field types and values
    if "symbol" in data and not isinstance(data["symbol"], str):
        errors.append("Symbol must be a string")

    if "order_type" in data:
        if data["order_type"] not in ["market", "limit"]:
            errors.append("Order type must be 'market' or 'limit'")

    if "side" in data:
        if data["side"] not in ["buy", "sell"]:
            errors.append("Side must be 'buy' or 'sell'")

    if "amount" in data:
        try:
            amount = float(data["amount"])
            if amount <= 0:
                errors.append("Amount must be positive")
        except (TypeError, ValueError):
            errors.append("Amount must be a number")

    # Validate limit order specific fields
    if data.get("order_type") == "limit":
        if "price" not in data:
            errors.append("Price is required for limit orders")
        else:
            try:
                price = float(data["price"])
                if price <= 0:
                    errors.append("Price must be positive")
            except (TypeError, ValueError):
                errors.append("Price must be a number")

    # Validate optional fields
    optional_fields = {
        "leverage": (float, lambda x: x > 0, "Leverage must be positive"),
        "stop_loss": (float, lambda x: x > 0, "Stop loss must be positive"),
        "take_profit": (float, lambda x: x > 0, "Take profit must be positive"),
    }

    for field, (type_, validator, error_msg) in optional_fields.items():
        if field in data:
            try:
                value = type_(data[field])
                if not validator(value):
                    errors.append(error_msg)
            except (TypeError, ValueError):
                errors.append(f"{field} must be a number")

    return {"valid": len(errors) == 0, "errors": errors}


def validate_trading_pair(symbol: str) -> Tuple[bool, str]:
    """
    Validate trading pair format.

    Args:
        symbol: Trading pair symbol (e.g. "BTC/USD" or "BTCUSD")

    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(symbol, str):
        return False, "Symbol must be a string"

    # Check if it's in BASE/QUOTE format
    if "/" in symbol:
        parts = symbol.split("/")
        if len(parts) != 2:
            return False, "Invalid trading pair format. Use 'BASE/QUOTE'"
        
        base, quote = parts
        if not base or not quote:
            return False, "Base and quote currencies cannot be empty"
        
        return True, ""
    
    # Check if it's in BASEUSD or similar format (6 characters typically)
    elif len(symbol) >= 4 and symbol.isalpha():
        # Accept common formats like BTCUSD, ETHUSD, etc.
        # This is a simple validation - could be enhanced with specific currency lists
        return True, ""
    
    else:
        return False, "Invalid trading pair format. Use 'BASE/QUOTE' or 'BASEUSD' format"
