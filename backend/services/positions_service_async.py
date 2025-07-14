"""Async positions service for fetching real positions from Bitfinex."""

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

from backend.services.cache_service import get_cache_service
from backend.services.exchange import ExchangeError
from backend.services.exchange_async import (
    _exchange_instance as async_exchange_instance,
)


async def get_position_type_from_metadata_async(symbol: str) -> str:
    """
    Get position type (margin/spot) from stored order metadata asynchronously.

    Args:
        symbol: Trading pair symbol (e.g. "BTC/USD" or "TESTBTC/TESTUSD")

    Returns:
        "margin" or "spot" based on recent order metadata
    """
    # OBS: Detta är en förenklad implementation som använder statisk data
    # I en fullständig implementation skulle vi använda en databas eller annan persistent lagring
    # istället för att förlita oss på FastAPI app context

    # För närvarande, returnera alltid "spot" som en förenkling
    # Detta kan utökas i framtiden för att hämta data från en databas
    return "spot"


async def fetch_positions_async(
    symbols: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch positions asynchronously from Bitfinex using hybrid approach with caching.

    For Bitfinex SPOT trading, we convert non-zero cryptocurrency balances
    into "position" format since spot trades don't create margin positions.

    Args:
        symbols: Optional list of symbols to filter by

    Returns:
        List of position dictionaries with live data from Bitfinex

    Raises:
        ExchangeError: If Bitfinex API call fails
    """
    cache = get_cache_service()
    cache_key = f"positions_{symbols or 'all'}"

    # Check cache first (20 second TTL for positions)
    cached_positions = cache.get(cache_key, ttl_seconds=20)
    if cached_positions is not None:
        return cached_positions

    if not async_exchange_instance:
        logging.warning(
            "Async exchange service not available, returning empty positions"
        )
        return []

    try:
        # STEP 1: Try to fetch traditional margin positions first
        traditional_positions = []
        try:
            # Använd run_in_executor för att köra den synkrona metoden i en separat tråd
            loop = asyncio.get_event_loop()
            positions = await loop.run_in_executor(
                None, lambda: async_exchange_instance.fetch_positions(symbols)
            )
            traditional_positions = positions
            logging.info(
                f"✅ [Positions Async] Fetched {len(traditional_positions)} "
                f"margin positions"
            )
        except Exception as e:
            logging.info(
                f"📊 [Positions Async] No margin positions found "
                f"(normal for spot trading): {e}"
            )

        # STEP 2: Create "spot positions" from cryptocurrency holdings
        spot_positions = []
        margin_positions_from_holdings = []

        try:
            # Hämta balances asynkront
            loop = asyncio.get_event_loop()
            balances = await loop.run_in_executor(
                None, lambda: async_exchange_instance.fetch_balance()
            )

            # Get current market prices for major cryptocurrencies
            major_cryptos = ["TESTBTC", "TESTETH", "TESTLTC", "BTC", "ETH", "LTC"]

            # Skapa tasks för alla ticker-anrop för att köra dem parallellt
            ticker_tasks = {}
            for crypto in major_cryptos:
                if crypto in balances and balances[crypto] > 0:
                    # Determine symbol for price lookup
                    base_currency = (
                        crypto.replace("TEST", "")
                        if crypto.startswith("TEST")
                        else crypto
                    )
                    symbol = f"{base_currency}/USD"

                    # Skapa en task för att hämta ticker-data
                    ticker_tasks[crypto] = loop.run_in_executor(
                        None, lambda s=symbol: async_exchange_instance.fetch_ticker(s)
                    )

            # Vänta på att alla ticker-tasks ska slutföras
            for crypto, future in ticker_tasks.items():
                try:
                    ticker = await future
                    amount = balances[crypto]
                    current_price = ticker["last"]
                    current_value = amount * current_price

                    # Hämta position-typ asynkront
                    base_currency = (
                        crypto.replace("TEST", "")
                        if crypto.startswith("TEST")
                        else crypto
                    )
                    symbol = f"{base_currency}/USD"
                    position_type = await get_position_type_from_metadata_async(symbol)

                    if position_type == "margin":
                        # Create margin-classified position
                        margin_position = {
                            "id": f"margin_{crypto}_{int(time.time())}",
                            "symbol": symbol,
                            "side": "buy",  # Holdings are always long
                            "amount": amount,
                            "entry_price": current_price,
                            "mark_price": current_price,
                            "pnl": 0.0,  # Would need historical entry data
                            "pnl_percentage": 0.0,
                            "timestamp": int(time.time() * 1000),
                            "contracts": amount,
                            "notional": current_value,
                            "collateral": current_value,
                            "margin_mode": "cross",
                            "maintenance_margin": current_value * 0.1,  # 10%
                            "position_type": "margin",  # From margin trading
                            "leverage": 1.0,  # Conservative estimate
                        }
                        margin_positions_from_holdings.append(margin_position)
                        logging.info(
                            f"📊 [Positions Async] Created MARGIN position: "
                            f"{crypto} = {amount:.6f} @ ${current_price:,.2f}"
                        )
                    else:
                        # Create spot position from crypto holding
                        spot_position = {
                            "id": f"spot_{crypto}_{int(time.time())}",
                            "symbol": symbol,
                            "side": "buy",  # Spot holdings are always long
                            "amount": amount,
                            "entry_price": current_price,
                            "mark_price": current_price,
                            "pnl": 0.0,  # Spot positions show no P&L
                            "pnl_percentage": 0.0,
                            "timestamp": int(time.time() * 1000),
                            "contracts": amount,
                            "notional": current_value,
                            "collateral": current_value,
                            "margin_mode": "spot",
                            "maintenance_margin": 0.0,
                            "position_type": position_type,  # From meta
                            "leverage": 1.0,  # Spot is always 1:1
                        }
                        spot_positions.append(spot_position)
                        logging.info(
                            f"📊 [Positions Async] Created SPOT position: "
                            f"{crypto} = {amount:.6f} @ ${current_price:,.2f}"
                        )
                except Exception as e:
                    logging.warning(
                        f"❌ [Positions Async] Failed to process position for {crypto}: {e}"
                    )

        except Exception as e:
            logging.error(f"❌ [Positions Async] Failed to create positions: {e}")

        # STEP 3: Combine all position types
        all_positions = (
            traditional_positions + margin_positions_from_holdings + spot_positions
        )

        # STEP 4: Filter by symbols if requested
        if symbols and all_positions:
            filtered_positions = []
            for position in all_positions:
                if position["symbol"] in symbols:
                    filtered_positions.append(position)
            all_positions = filtered_positions

        logging.info(
            f"✅ [Positions Async] Total: {len(all_positions)} positions "
            f"(True Margin: {len(traditional_positions)}, "
            f"Classified Margin: {len(margin_positions_from_holdings)}, "
            f"Spot: {len(spot_positions)})"
        )

        # Cache the result for 20 seconds to reduce API calls
        cache.set(cache_key, all_positions)

        return all_positions

    except ExchangeError as e:
        logging.error(f"❌ [Positions Async] Exchange error: {str(e)}")
        raise e
    except Exception as e:
        logging.error(f"❌ [Positions Async] Failed to fetch positions: {str(e)}")
        raise ExchangeError(f"Failed to fetch positions: {str(e)}")


async def get_mock_positions_async() -> List[Dict[str, Any]]:
    """
    Returns mock positions for testing asynchronously.
    This should NOT be used in production!
    """
    return [
        {
            "id": "BTC-PERP-12345",
            "symbol": "BTC/USD",
            "side": "buy",
            "amount": 0.5,
            "entry_price": 45000.0,
            "mark_price": 47500.0,
            "pnl": 1250.0,
            "pnl_percentage": 5.56,
            "timestamp": int(time.time() * 1000),
            "contracts": 0.5,
            "notional": 23750.0,
            "collateral": 23750.0,
            "margin_mode": "cross",
            "maintenance_margin": 1187.5,
            "position_type": "margin",
            "leverage": 1.0,
        },
        {
            "id": "ETH-PERP-23456",
            "symbol": "ETH/USD",
            "side": "sell",
            "amount": 2.5,
            "entry_price": 3500.0,
            "mark_price": 3250.0,
            "pnl": 625.0,
            "pnl_percentage": 7.14,
            "timestamp": int(time.time() * 1000),
            "contracts": 2.5,
            "notional": 8125.0,
            "collateral": 8125.0,
            "margin_mode": "cross",
            "maintenance_margin": 406.25,
            "position_type": "margin",
            "leverage": 1.0,
        },
    ]
