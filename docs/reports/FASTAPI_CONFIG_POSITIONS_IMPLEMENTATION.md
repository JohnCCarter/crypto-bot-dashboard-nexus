# FastAPI Config och Positions Implementation

## Översikt

Detta dokument beskriver implementationen av Config- och Positions-endpoints för FastAPI-migrationen. Dessa endpoints är viktiga för systemets konfigurationshantering och positionsövervakning.

## Config-endpoints

### Implementerade endpoints

Vi har implementerat följande config-endpoints för FastAPI:

1. **GET /api/config** - Hämta komplett konfiguration
2. **POST /api/config** - Uppdatera konfiguration
3. **GET /api/config/summary** - Hämta konfigurationssammanfattning
4. **GET /api/config/strategies** - Lista alla strategier och vikter
5. **GET /api/config/strategy/{name}** - Hämta parametrar för specifik strategi
6. **PUT /api/config/strategy/{name}/weight** - Uppdatera vikt för specifik strategi
7. **GET /api/config/probability** - Hämta sannolikhetsramverksparametrar
8. **PUT /api/config/probability** - Uppdatera sannolikhetsramverksparametrar
9. **GET /api/config/validate** - Validera aktuell konfiguration
10. **POST /api/config/reload** - Ladda om konfiguration från fil

### Förbättringar jämfört med Flask-implementationen

1. **Dependency Injection**:
   - Implementerat `get_config_service()` som en dependency för att förenkla testning och mocking
   - Konsekvent användning av DI i alla endpoints

2. **Pydantic-modeller**:
   - Skapat `StrategyWeight` och `ProbabilitySettings` för validering av indata
   - Använder `Body()` för flexibel validering av JSON-data

3. **Asynkrona funktioner**:
   - Alla endpoints använder `async/await` för förbättrad prestanda
   - Anropar asynkrona metoder från ConfigService

4. **Förbättrad felhantering**:
   - Mer detaljerade felmeddelanden
   - Specifik validering för numeriska värden (t.ex. vikter mellan 0.0 och 1.0)
   - Separata felhanterare för olika typer av fel

5. **Standardiserade svar**:
   - Alla svar följer samma format med `status`, `message` och data
   - Använder `ResponseStatus` enum för konsekvent statusrapportering

### Kodexempel: Uppdatera strategivikt

```python
@router.put("/strategy/{strategy_name}/weight")
async def update_strategy_weight(
    strategy_name: str,
    data: Dict[str, float] = Body(...),
    config_service: ConfigService = Depends(get_config_service),
) -> Dict[str, Any]:
    """
    Update strategy weight.
    
    Parameters:
        strategy_name: Name of the strategy
        data: Dictionary with weight value
        
    Returns:
        Dict: Update result
    """
    try:
        new_weight = data.get("weight")
        
        if new_weight is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weight value is required"
            )
            
        if not (0.0 <= new_weight <= 1.0):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Weight must be between 0.0 and 1.0"
            )
            
        success = await config_service.update_strategy_weight_async(
            strategy_name, new_weight
        )
        
        if success:
            return {
                "status": ResponseStatus.SUCCESS,
                "message": f"Updated {strategy_name} weight to {new_weight}",
                "strategy_name": strategy_name,
                "new_weight": new_weight,
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update strategy weight"
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update strategy weight: {str(e)}"
        )
```

## Positions-endpoints

### Implementerade endpoints

Vi har implementerat följande positions-endpoint för FastAPI:

1. **GET /api/positions** - Hämta alla aktuella positioner

### Förbättringar jämfört med Flask-implementationen

1. **Asynkrona funktioner**:
   - Använder `fetch_live_positions_async()` för asynkron hämtning av positioner
   - Förbättrad prestanda genom att undvika blockering vid API-anrop

2. **Förbättrad felhantering**:
   - Separata felhanterare för ExchangeError och andra fel
   - Mer detaljerade felmeddelanden

3. **Utökad svarsdata**:
   - Inkluderar antal positioner (`count`)
   - Inkluderar timestamp från positionsdata
   - Använder `ResponseStatus` för att indikera varningsstatus vid exchange-fel

4. **Standardiserade svar**:
   - Alla svar följer samma format med `status`, `positions`, `count` och metadata

### Kodexempel: Hämta positioner

```python
@router.get("")
async def get_positions() -> Dict[str, Any]:
    """
    Fetch current positions from Bitfinex.

    Returns live positions if API keys are configured,
    otherwise returns empty list (no mock data for live trading).

    Returns:
        Dict: List of positions and metadata
    """
    try:
        # Attempt to fetch live positions from Bitfinex
        positions = await fetch_live_positions_async()

        return {
            "status": ResponseStatus.SUCCESS,
            "positions": positions,
            "count": len(positions),
            "timestamp": positions[0].get("timestamp") if positions else None,
        }

    except ExchangeError as e:
        # For exchange errors, return empty list rather than mock data for safety
        return {
            "status": ResponseStatus.WARNING,
            "positions": [],
            "count": 0,
            "message": f"Exchange error: {str(e)}",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch positions: {str(e)}"
        )
```

## Utmaningar och lösningar

### 1. Asynkrona metoder i ConfigService

**Utmaning**: ConfigService saknade asynkrona metoder för att passa FastAPI:s asynkrona modell.

**Lösning**: Implementerade asynkrona versioner av alla ConfigService-metoder som används av API-endpointsen:
- `get_config_summary_async()`
- `get_strategy_weights_async()`
- `get_strategy_params_async()`
- `update_strategy_weight_async()`
- `load_config_async()`
- `validate_config_async()`
- `update_probability_settings_async()`

### 2. Dependency Injection

**Utmaning**: Flask-implementationen använde globala tjänstinstanser, vilket inte passar FastAPI:s DI-modell.

**Lösning**: Skapade dependency-funktioner för alla tjänster:
- `get_config_service()` för ConfigService
- Använde befintliga asynkrona funktioner för positions-endpointsen

### 3. Standardiserade svarsformat

**Utmaning**: Olika endpoints returnerade olika svarsformat i Flask-implementationen.

**Lösning**: Standardiserade alla svar att inkludera:
- `status` (SUCCESS, WARNING, ERROR)
- Relevant data (positions, config, etc.)
- Metadata (count, timestamp, etc.)
- Felmeddelande vid behov

## Slutsats

Implementationen av Config- och Positions-endpoints för FastAPI har förbättrat kodkvaliteten, prestandan och användarupplevelsen. Genom att använda FastAPI:s funktioner för asynkrona operationer, dependency injection och Pydantic-modeller har vi skapat en mer robust och underhållbar API. 