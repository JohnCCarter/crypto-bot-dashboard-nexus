"""
Symbol mapping utility for paper trading environment.
Automatically converts standard symbols to test symbols for Bitfinex paper trading.
"""

import os
from typing import Dict, Optional, Any


class SymbolMapper:
    """Maps standard trading symbols to paper trading symbols."""
    
    # Standard to test symbol mapping
    SYMBOL_MAP = {
        # Major pairs
        "BTC/USD": "TESTBTC/TESTUSD",
        "ETH/USD": "TESTETH/TESTUSD", 
        "LTC/USD": "TESTLTC/TESTUSD",
        "XRP/USD": "TESTXRP/TESTUSD",
        
        # With USDT
        "BTC/USDT": "TESTBTC/TESTUSDT",
        "ETH/USDT": "TESTETH/TESTUSDT",
        "LTC/USDT": "TESTLTC/TESTUSDT",
        
        # Additional common pairs
        "BTC/EUR": "TESTBTC/TESTEUR",
        "ETH/EUR": "TESTETH/TESTEUR",
    }
    
    # Minimum order sizes for Bitfinex paper trading (based on actual API limits)
    MINIMUM_ORDER_SIZES = {
        "BTC/USD": 0.00004,   # TESTBTC/TESTUSD minimum
        "ETH/USD": 0.0008,    # TESTETH/TESTUSD minimum  
        "LTC/USD": 0.04,      # TESTLTC/TESTUSD minimum
        "XRP/USD": 0.1,       # Estimated
        "BTC/USDT": 0.00004,
        "ETH/USDT": 0.0008,
        "LTC/USDT": 0.04,
        "BTC/EUR": 0.00004,
        "ETH/EUR": 0.0008,
    }
    
    # Reverse mapping for converting back
    REVERSE_MAP = {v: k for k, v in SYMBOL_MAP.items()}
    
    @classmethod
    def is_paper_trading_enabled(cls) -> bool:
        """Check if we're in paper trading mode based on environment."""
        # Check if we have paper trading API keys or explicit flag
        return (
            os.getenv("PAPER_TRADING", "").lower() in ("true", "1", "yes") or
            "test" in os.getenv("BITFINEX_API_KEY", "").lower() or
            cls._has_test_symbols_in_env()
        )
    
    @classmethod
    def _has_test_symbols_in_env(cls) -> bool:
        """Check if environment suggests test symbols are being used."""
        # This could be expanded based on your specific setup
        return False
    
    @classmethod
    def to_paper_symbol(cls, symbol: str) -> str:
        """
        Convert standard symbol to paper trading symbol if in paper mode.
        
        Args:
            symbol: Standard trading symbol (e.g. "BTC/USD")
            
        Returns:
            Paper trading symbol if in paper mode, otherwise original symbol
        """
        if cls.is_paper_trading_enabled():
            return cls.SYMBOL_MAP.get(symbol, symbol)
        return symbol
    
    @classmethod
    def to_standard_symbol(cls, symbol: str) -> str:
        """
        Convert paper trading symbol back to standard symbol.
        
        Args:
            symbol: Paper trading symbol (e.g. "TESTBTC/TESTUSD")
            
        Returns:
            Standard trading symbol
        """
        return cls.REVERSE_MAP.get(symbol, symbol)
    
    @classmethod
    def normalize_symbol_for_display(cls, symbol: str) -> str:
        """
        Normalize symbol for UI display (always show standard symbols).
        
        Args:
            symbol: Any symbol (standard or test)
            
        Returns:
            Standard symbol for display
        """
        return cls.to_standard_symbol(symbol)
    
    @classmethod
    def get_available_paper_symbols(cls) -> list:
        """Get list of available paper trading symbols."""
        return list(cls.SYMBOL_MAP.values())
    
    @classmethod
    def get_available_standard_symbols(cls) -> list:
        """Get list of available standard symbols."""
        return list(cls.SYMBOL_MAP.keys())
    
    @classmethod
    def validate_symbol(cls, symbol: str) -> bool:
        """
        Validate if symbol is supported.
        
        Args:
            symbol: Symbol to validate
            
        Returns:
            True if symbol is supported
        """
        if cls.is_paper_trading_enabled():
            # In paper mode, accept both standard and test symbols
            return symbol in cls.SYMBOL_MAP or symbol in cls.REVERSE_MAP
        else:
            # In live mode, only accept standard symbols
            return symbol in cls.SYMBOL_MAP
    
    @classmethod
    def get_minimum_order_size(cls, symbol: str) -> float:
        """
        Get minimum order size for a symbol.
        
        Args:
            symbol: Standard symbol (e.g. "BTC/USD")
            
        Returns:
            Minimum order size as float
        """
        return cls.MINIMUM_ORDER_SIZES.get(symbol, 0.001)  # Default fallback
    
    @classmethod
    def validate_order_amount(cls, symbol: str, amount: float) -> Dict[str, Any]:
        """
        Validate if order amount meets minimum requirements.
        
        Args:
            symbol: Standard symbol (e.g. "BTC/USD")
            amount: Order amount to validate
            
        Returns:
            Dict with validation result and details
        """
        minimum = cls.get_minimum_order_size(symbol)
        
        if amount >= minimum:
            return {
                "valid": True,
                "minimum": minimum,
                "amount": amount
            }
        else:
            return {
                "valid": False,
                "minimum": minimum,
                "amount": amount,
                "error": f"Order amount {amount} is below minimum {minimum} for {symbol}"
            }
    
    @classmethod
    def suggest_minimum_amount(cls, symbol: str) -> float:
        """
        Suggest a reasonable minimum amount for trading.
        
        Args:
            symbol: Standard symbol
            
        Returns:
            Suggested minimum amount (slightly above exchange minimum)
        """
        minimum = cls.get_minimum_order_size(symbol)
        # Add 10% buffer above minimum to ensure orders go through
        return round(minimum * 1.1, 8)
    
    @classmethod
    def get_mapping_info(cls) -> Dict[str, Any]:
        """Get current symbol mapping information for debugging."""
        return {
            "paper_trading_enabled": cls.is_paper_trading_enabled(),
            "mappings": cls.SYMBOL_MAP if cls.is_paper_trading_enabled() else {},
            "minimums": cls.MINIMUM_ORDER_SIZES,
            "available_symbols": (
                cls.get_available_paper_symbols() 
                if cls.is_paper_trading_enabled() 
                else cls.get_available_standard_symbols()
            )
        }