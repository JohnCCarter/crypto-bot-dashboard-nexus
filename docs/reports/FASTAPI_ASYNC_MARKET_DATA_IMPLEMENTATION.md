# FastAPI Async Market Data Implementation

## Översikt

Detta dokument beskriver implementationen av LiveDataServiceAsync för att hantera marknadsdata i FastAPI-migrationen. LiveDataServiceAsync är en asynkron tjänst som hanterar hämtning av marknadsdata från kryptovalutabörser via CCXT-biblioteket.

## Implementation

### Huvudklassen: LiveDataServiceAsync

LiveDataServiceAsync implementerar följande funktionalitet:

- Asynkron hämtning av OHLCV-data (Open, High, Low, Close, Volume)
- Asynkron hämtning av ticker-data (aktuella priser och volymer)
- Asynkron hämtning av orderbook-data (köp- och säljordrar)
- Beräkning av marknadskontext för handelsstrategier
- Validering av marknadsförhållanden för säker handel

### Singleton-mönster

LiveDataServiceAsync implementerar ett singleton-mönster via två hjälpfunktioner:

```python
# Singleton instance
_live_data_service_async: Optional[LiveDataServiceAsync] = None

async def get_live_data_service_async() -> LiveDataServiceAsync:
    """Get or create a singleton instance of LiveDataServiceAsync."""
    global _live_data_service_async
    
    if _live_data_service_async is None:
        _live_data_service_async = LiveDataServiceAsync()
        
    return _live_data_service_async

async def close_live_data_service_async():
    """Close the singleton instance of LiveDataServiceAsync."""
    global _live_data_service_async
    
    if _live_data_service_async is not None:
        await _live_data_service_async.close()
        _live_data_service_async = None
```

### Nyckelmetoder

#### fetch_live_ohlcv

```python
async def fetch_live_ohlcv(
    self, symbol: str, timeframe: str = "1h", limit: int = 100
) -> pd.DataFrame:
    """
    Fetch live OHLCV data for a symbol asynchronously.
    
    Args:
        symbol: Trading pair symbol
        timeframe: Timeframe for candles
        limit: Number of candles to fetch
        
    Returns:
        DataFrame with OHLCV data
    """
    try:
        # Fetch OHLCV data from exchange
        ohlcv_data = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
        
        # Convert to DataFrame
        df = pd.DataFrame(
            ohlcv_data,
            columns=["timestamp", "open", "high", "low", "close", "volume"],
        )
        
        # Drop timestamp column (not needed for analysis)
        df = df.drop(columns=["timestamp"])
        
        return df
    except Exception as e:
        logging.error(f"Error fetching OHLCV data: {e}")
        # Return empty DataFrame with correct columns
        return pd.DataFrame(columns=["open", "high", "low", "close", "volume"])
```

#### get_live_market_context

```python
async def get_live_market_context(
    self, symbol: str, timeframe: str = "1h", limit: int = 100
) -> Dict[str, Any]:
    """
    Get comprehensive market context for a symbol asynchronously.
    
    Args:
        symbol: Trading pair symbol
        timeframe: Timeframe for historical data
        limit: Number of candles to fetch
        
    Returns:
        Dictionary with market context data
    """
    # Fetch OHLCV data
    ohlcv_df = await self.fetch_live_ohlcv(symbol, timeframe, limit)
    
    # Fetch ticker data
    ticker = await self.fetch_live_ticker(symbol)
    
    # Fetch orderbook data
    orderbook = await self.fetch_live_orderbook(symbol, 20)
    
    # Extract key metrics
    current_price = ticker.get("last", 0.0)
    
    # Get best bid and ask
    best_bid = orderbook["bids"][0][0] if orderbook["bids"] else 0.0
    best_ask = orderbook["asks"][0][0] if orderbook["asks"] else 0.0
    spread = best_ask - best_bid if (best_bid and best_ask) else 0.0
    
    # Calculate volatility
    if not ohlcv_df.empty:
        volatility_pct = (ohlcv_df["high"].max() - ohlcv_df["low"].min()) / ohlcv_df["close"].mean() * 100
    else:
        volatility_pct = 0.0
    
    # Build market context
    context = {
        "symbol": symbol,
        "ohlcv_data": ohlcv_df,
        "ticker": ticker,
        "orderbook": orderbook,
        "current_price": current_price,
        "best_bid": best_bid,
        "best_ask": best_ask,
        "spread": spread,
        "volume_24h": ticker.get("baseVolume", 0.0),
        "volatility_pct": volatility_pct,
        "timestamp": datetime.now().isoformat(),
    }
    
    return context
```

## Integration med FastAPI

LiveDataServiceAsync är integrerad med FastAPI via dependency injection i `api/dependencies.py`:

```python
# Market data service dependency provider
async def get_market_data_service() -> LiveDataServiceAsync:
    """
    Get the market data service dependency.
    
    Returns:
    --------
    LiveDataServiceAsync: The async market data service instance
    """
    return await get_live_data_service_async()
```

Detta används sedan i `api/market_data.py` för att implementera endpoints för marknadsdata:

```python
@router.get("/ohlcv/{symbol}")
async def get_ohlcv(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 100,
    market_data_service: LiveDataServiceAsync = Depends(get_market_data_service),
):
    """Get OHLCV data for a symbol."""
    df = await market_data_service.fetch_live_ohlcv(symbol, timeframe, limit)
    return df.to_dict(orient="records")

@router.get("/market-context/{symbol}")
async def get_market_context(
    symbol: str,
    timeframe: str = "1h",
    limit: int = 100,
    market_data_service: LiveDataServiceAsync = Depends(get_market_data_service),
):
    """Get comprehensive market context for a symbol."""
    context = await market_data_service.get_live_market_context(symbol, timeframe, limit)
    
    # Convert DataFrame to records for JSON serialization
    if "ohlcv_data" in context and isinstance(context["ohlcv_data"], pd.DataFrame):
        context["ohlcv_data"] = context["ohlcv_data"].to_dict(orient="records")
        
    return context
```

## Testning

Testning av LiveDataServiceAsync görs i `tests/test_live_data_service_async.py` med hjälp av pytest och AsyncMock. Testerna verifierar att alla asynkrona metoder fungerar korrekt och att data formateras och returneras på rätt sätt.

Nyckelaspekter i testningen:

- Användning av AsyncMock för att mocka asynkrona metoder i CCXT-biblioteket
- Verifiering av att metoderna anropas med rätt parametrar
- Kontroll av att returnerad data har rätt format och struktur

## Prestandaförbättringar

Jämfört med den tidigare synkrona implementationen ger LiveDataServiceAsync flera prestandaförbättringar:

1. **Asynkrona anrop**: Möjliggör parallell exekvering av API-anrop, vilket minskar väntetider
2. **Effektiv resursanvändning**: Blockerar inte tråden under I/O-operationer
3. **Bättre skalbarhet**: Kan hantera fler samtidiga anslutningar
4. **Minskad latens**: Snabbare svarstider för API-endpoints

## Slutsats

LiveDataServiceAsync är en viktig komponent i FastAPI-migrationen som möjliggör effektiv och skalbar hämtning av marknadsdata. Tjänsten är nu fullt implementerad, testad och integrerad med FastAPI-endpoints. Den asynkrona implementationen ger betydande prestandaförbättringar jämfört med den tidigare synkrona implementationen. 