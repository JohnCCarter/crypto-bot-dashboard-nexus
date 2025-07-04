# Implementation av RiskManagerAsync och PortfolioManagerAsync

## Översikt

Detta dokument beskriver implementationen av de asynkrona tjänsterna RiskManagerAsync och PortfolioManagerAsync, samt integrationen med FastAPI-endpoints. Dessa tjänster utgör kärnan i systemets riskhantering och portföljhantering.

## RiskManagerAsync

### Arkitektur

RiskManagerAsync är en asynkron implementation av riskhanteringsfunktionalitet med fokus på:

1. **Ordervalidering** - Validera att ordrar uppfyller riskkrav
2. **Portföljriskbedömning** - Bedöma risknivån för hela portföljen
3. **Sannolikhetsbaserad riskhantering** - Använda sannolikhetsmodeller för beslut
4. **Positionsstorleksberäkning** - Intelligent beräkning av positionsstorlekar

### Huvudfunktioner

- **validate_order** - Validerar en order mot riskparametrar
- **validate_order_with_probabilities** - Validerar en order med sannolikhetsdata
- **assess_portfolio_risk** - Bedömer risknivån för hela portföljen
- **calculate_intelligent_position_size** - Beräknar optimal positionsstorlek
- **calculate_dynamic_stop_loss** - Beräknar dynamiska stop loss-nivåer

### Integration med FastAPI

RiskManagerAsync integreras i FastAPI via dependency injection-systemet:

```python
async def get_risk_manager() -> RiskManagerAsync:
    """
    Get or create singleton instance of RiskManagerAsync.
    """
    global _risk_manager_async
    if _risk_manager_async is None:
        config = get_config_service()
        risk_params = RiskParameters(
            max_position_size=config.get("risk.max_position_size", 0.1),
            max_leverage=config.get("risk.max_leverage", 3.0),
            max_daily_loss=config.get("risk.max_daily_loss", 0.05),
            max_positions=config.get("risk.max_positions", 5),
            min_confidence=config.get("risk.min_confidence", 0.6),
        )
        _risk_manager_async = RiskManagerAsync(risk_params)
    return _risk_manager_async
```

Endpoints använder sedan denna dependency för att utföra riskhantering:

```python
@router.post("/validate/order", response_model=OrderValidationResponse)
async def validate_order(
    order_data: OrderData,
    probability_data: Optional[ProbabilityDataModel] = None,
    risk_manager: RiskManagerAsync = Depends(get_risk_manager),
    ...
):
    # Använd risk_manager för validering
    validation_result = await risk_manager.validate_order(...)
```

## PortfolioManagerAsync

### Arkitektur

PortfolioManagerAsync är en asynkron implementation av portföljhantering med fokus på:

1. **Signalhantering** - Kombinera signaler från olika strategier
2. **Positionshantering** - Hantera öppna positioner
3. **Portföljallokering** - Beräkna optimal allokering av kapital
4. **Rebalansering** - Rebalansera portföljen vid behov

### Huvudfunktioner

- **combine_strategy_signals** - Kombinerar signaler från olika strategier
- **calculate_portfolio_position_size** - Beräknar optimal positionsstorlek
- **should_execute_trade** - Avgör om en handel bör genomföras
- **rebalance_portfolio** - Rebalanserar portföljen
- **calculate_allocations** - Beräknar optimal allokering

### Integration med FastAPI

PortfolioManagerAsync integreras i FastAPI via dependency injection:

```python
async def get_portfolio_manager(
    risk_manager: RiskManagerAsync = Depends(get_risk_manager),
    config: ConfigService = Depends(get_config_service),
) -> PortfolioManagerAsync:
    """
    Get or create singleton instance of PortfolioManagerAsync.
    """
    global _portfolio_manager_async
    if _portfolio_manager_async is None:
        # Läs strategi-vikter från konfigurationen
        strategy_weights = []
        strategies_config = config.get("strategies", {})
        for name, weight in strategies_config.items():
            if isinstance(weight, (int, float)) and weight > 0:
                strategy_weights.append(
                    StrategyWeight(strategy_name=name, weight=float(weight))
                )
        
        _portfolio_manager_async = PortfolioManagerAsync(
            risk_manager=risk_manager,
            strategy_weights=strategy_weights,
        )
    return _portfolio_manager_async
```

Endpoints använder denna dependency för portföljhantering:

```python
@router.post("/allocate", response_model=PortfolioAllocationResponse)
async def allocate_portfolio(
    request: PortfolioAllocationRequest,
    portfolio_manager: PortfolioManagerAsync = Depends(get_portfolio_manager),
    risk_manager: RiskManagerAsync = Depends(get_risk_manager),
) -> Dict[str, Any]:
    # Använd portfolio_manager för allokering
    allocations = await portfolio_manager.calculate_allocations(...)
```

## Testning

### RiskManagerAsync

RiskManagerAsync har omfattande tester som täcker:

1. **ProbabilityData** - Test för sannolikhetsberäkningar
2. **Grundläggande funktionalitet** - Initialisering och persistens
3. **Ordervalidering** - Test för olika validerings-scenarios 
4. **Avancerade funktioner** - Intelligent position sizing, dynamisk stop loss

### PortfolioManagerAsync

PortfolioManagerAsync har omfattande tester som täcker:

1. **Grundläggande funktionalitet** - Initialisering och viktvalidering
2. **Signalhantering** - Kombinera strategisignaler
3. **Positionsberäkning** - Beräkning av positionsstorlekar
4. **Handelsutförande** - Utvärdering om handel bör genomföras

## Asynkron datahantering

Både RiskManagerAsync och PortfolioManagerAsync använder sig av asynkron datahantering:

1. **IO-operationer** - Asynkrona anrop till exchange och databas
2. **Filoperationer** - Asynkron persistens av data
3. **Tidskrävande beräkningar** - Möjlighet att köra beräkningar asynkront

## Förbättringar jämfört med synkrona implementationer

1. **Bättre prestanda** - Asynkrona anrop blockerar inte server-tråden
2. **Skalbarhet** - Kan hantera fler samtidiga anslutningar
3. **Responsivitet** - Snabbare svarstider för användare
4. **Flexibilitet** - Enklare att integrera med andra asynkrona tjänster

## Kvarstående uppgifter

1. **Förbättra felhantering** - Mer detaljerad felrapportering
2. **Utökad loggning** - Bättre loggning för felsökning
3. **Ytterligare integration** - Integration med websocket för realtidsuppdateringar
4. **Prestandaoptimering** - Ytterligare optimering av kritiska funktioner

## Sammanfattning

Implementationen av RiskManagerAsync och PortfolioManagerAsync utgör en viktig del i migrationen till FastAPI och asynkron datahantering. Dessa tjänster ger en solid grund för riskhantering och portföljhantering med förbättrad prestanda och skalbarhet.

Uppdaterad: 2025-07-05 