"""
Symbol converter utility for Bitfinex API integration.

Handles conversion between UI format and Bitfinex API format for:
- Spot trading pairs
- Margin trading pairs
- Funding currencies
- WebSocket subscriptions
"""

import logging
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


class BitfinexSymbolConverter:
    """
    Centralized symbol format converter for Bitfinex API.

    Format conversions:
    - UI format: TESTBTC/TESTUSD
    - Bitfinex base: TESTBTC:TESTUSD
    - Trading pairs: tTESTBTC:TESTUSD (with 't' prefix)
    - Funding currencies: fTESTBTC, fTESTUSD (with 'f' prefix)
    """

    @staticmethod
    def ui_to_bitfinex_base(symbol: str) -> str:
        """
        Convert UI format to Bitfinex base format.

        Args:
            symbol: UI format (e.g., 'TESTBTC/TESTUSD')

        Returns:
            Bitfinex base format (e.g., 'TESTBTC:TESTUSD')
        """
        if "/" in symbol:
            return symbol.replace("/", ":")
        return symbol

    @staticmethod
    def ui_to_trading_pair(symbol: str) -> str:
        """
        Convert UI format to Bitfinex trading pair format.

        Args:
            symbol: UI format (e.g., 'TESTBTC/TESTUSD')

        Returns:
            Trading pair format (e.g., 'tTESTBTC:TESTUSD')
        """
        base_symbol = BitfinexSymbolConverter.ui_to_bitfinex_base(symbol)

        if not base_symbol.startswith("t"):
            return f"t{base_symbol}"
        return base_symbol

    @staticmethod
    def ui_to_funding_currency(currency: str) -> str:
        """
        Convert currency to Bitfinex funding format.

        Args:
            currency: Currency (e.g., 'TESTBTC', 'TESTUSD')

        Returns:
            Funding format (e.g., 'fTESTBTC', 'fTESTUSD')
        """
        if not currency.startswith("f"):
            return f"f{currency}"
        return currency

    @staticmethod
    def bitfinex_to_ui(symbol: str) -> str:
        """
        Convert Bitfinex format back to UI format.

        Args:
            symbol: Bitfinex format (e.g., 'tTESTBTC:TESTUSD')

        Returns:
            UI format (e.g., 'TESTBTC/TESTUSD')
        """
        # Remove prefixes
        clean_symbol = symbol
        if symbol.startswith("t") or symbol.startswith("f"):
            clean_symbol = symbol[1:]

        # Convert colon to slash
        if ":" in clean_symbol:
            return clean_symbol.replace(":", "/")
        return clean_symbol

    @staticmethod
    def extract_base_quote(symbol: str) -> Tuple[str, str]:
        """
        Extract base and quote currencies from symbol.

        Args:
            symbol: Any format symbol

        Returns:
            Tuple of (base_currency, quote_currency)
        """
        # Convert to UI format first
        ui_symbol = BitfinexSymbolConverter.bitfinex_to_ui(symbol)

        if "/" in ui_symbol:
            parts = ui_symbol.split("/")
            return parts[0], parts[1]

        # Fallback for symbols without separator
        if ui_symbol.endswith("USD"):
            return ui_symbol[:-3], "USD"
        elif ui_symbol.endswith("USDT"):
            return ui_symbol[:-4], "USDT"

        return ui_symbol, ""

    @staticmethod
    def is_test_symbol(symbol: str) -> bool:
        """
        Check if symbol contains TEST currencies.

        Args:
            symbol: Symbol in any format

        Returns:
            True if symbol contains TEST currencies
        """
        clean_symbol = BitfinexSymbolConverter.bitfinex_to_ui(symbol)
        return "TEST" in clean_symbol.upper()

    @staticmethod
    def convert_for_api_call(symbol: str, operation: str = "trading") -> str:
        """
        Convert symbol for specific API operation.

        Args:
            symbol: UI format symbol
            operation: 'trading', 'market_data', 'websocket', 'funding'

        Returns:
            Properly formatted symbol for the operation
        """
        if operation == "trading":
            # For order placement, balance checks, etc.
            return BitfinexSymbolConverter.ui_to_trading_pair(symbol)

        elif operation == "market_data":
            # For ticker, OHLCV, orderbook
            return BitfinexSymbolConverter.ui_to_trading_pair(symbol)

        elif operation == "websocket":
            # For WebSocket subscriptions
            return BitfinexSymbolConverter.ui_to_trading_pair(symbol)

        elif operation == "funding":
            # For funding operations - return just the currency part
            base, quote = BitfinexSymbolConverter.extract_base_quote(symbol)
            return BitfinexSymbolConverter.ui_to_funding_currency(base)

        else:
            # Default to trading pair format
            return BitfinexSymbolConverter.ui_to_trading_pair(symbol)

    @staticmethod
    def validate_symbol_format(symbol: str) -> Dict[str, Any]:
        """
        Validate and analyze symbol format.

        Args:
            symbol: Symbol to validate

        Returns:
            Dict with validation results and metadata
        """
        result = {
            "valid": False,
            "format": "unknown",
            "base": "",
            "quote": "",
            "is_test": False,
            "prefixed": False,
            "errors": [],
        }

        try:
            # Check for prefixes
            if symbol.startswith("t") or symbol.startswith("f"):
                result["prefixed"] = True

            # Extract base and quote
            base, quote = BitfinexSymbolConverter.extract_base_quote(symbol)
            result["base"] = base
            result["quote"] = quote

            # Check if test symbol
            result["is_test"] = BitfinexSymbolConverter.is_test_symbol(symbol)

            # Determine format
            if "/" in symbol:
                result["format"] = "ui"
            elif ":" in symbol:
                result["format"] = "bitfinex"
            else:
                result["format"] = "compact"

            # Basic validation
            if base and quote:
                result["valid"] = True
            else:
                result["errors"].append("Could not extract base/quote currencies")

        except Exception as e:
            result["errors"].append(f"Validation error: {str(e)}")

        return result


# Convenience functions for common operations
def convert_ui_to_trading(symbol: str) -> str:
    """Quick conversion from UI to trading format."""
    return BitfinexSymbolConverter.ui_to_trading_pair(symbol)


def convert_ui_to_websocket(symbol: str) -> str:
    """Quick conversion from UI to WebSocket format."""
    return BitfinexSymbolConverter.ui_to_trading_pair(symbol)


def convert_trading_to_ui(symbol: str) -> str:
    """Quick conversion from trading format to UI."""
    return BitfinexSymbolConverter.bitfinex_to_ui(symbol)


def is_paper_trading_symbol(symbol: str) -> bool:
    """Quick check if symbol is for paper trading."""
    return BitfinexSymbolConverter.is_test_symbol(symbol)


# Logger for symbol conversions
def log_symbol_conversion(original: str, converted: str, operation: str):
    """Log symbol conversion for debugging."""
    logger.debug(f"🔄 Symbol conversion [{operation}]: {original} → {converted}")


if __name__ == "__main__":
    # Test the converter
    test_symbols = [
        "TESTBTC/TESTUSD",
        "TESTETH/TESTUSD",
        "TESTLTC/TESTUSD",
        "BTC/USD",
        "ETH/USD",
    ]

    print("=== Symbol Converter Test ===")
    for symbol in test_symbols:
        print(f"\nOriginal: {symbol}")
        print(f"Trading:  {convert_ui_to_trading(symbol)}")
        print(f"WebSocket: {convert_ui_to_websocket(symbol)}")
        back_to_ui = convert_trading_to_ui(convert_ui_to_trading(symbol))
        print(f"Back to UI: {back_to_ui}")

        validation = BitfinexSymbolConverter.validate_symbol_format(symbol)
        print(
            f"Valid: {validation['valid']}, "
            f"Format: {validation['format']}, "
            f"Test: {validation['is_test']}"
        )
