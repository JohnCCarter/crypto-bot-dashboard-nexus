# Implementation av Asynkrona Risk- och Portfoliotjänster

Detta dokument beskriver implementationen av de asynkrona versionerna av RiskManager och PortfolioManager för FastAPI-migrationen.

## Översikt

Som en del av den pågående migrationen från Flask till FastAPI har vi implementerat asynkrona versioner av två kritiska tjänster:

1. **RiskManagerAsync** - Hanterar riskbedömning och riskkontroll
2. **PortfolioManagerAsync** - Hanterar portföljallokering och signalbehandling

Dessa tjänster är centrala för handelssystemet och deras asynkrona implementationer möjliggör förbättrad prestanda och skalbarhet.

## RiskManagerAsync

### Funktionalitet

RiskManagerAsync tillhandahåller följande funktionalitet:

- Validering av order mot riskregler
- Beräkning av positionsstorlek baserat på risktolerans
- Riskbedömning av hela portföljen
- Sannolikhetsbaserad riskbedömning
- Dynamisk justering av risknivåer

### Implementation

```python
class RiskManagerAsync:
    """Asynkron riskhanterare för trading-systemet."""

    def __init__(self, risk_params: RiskParameters):
        """
        Initialisera RiskManagerAsync med riskparametrar.
        
        Args:
            risk_params: Riskparametrar för att konfigurera riskhantering
        """
        self.risk_params = risk_params
        self.daily_pnl = 0.0
        self.last_reset = datetime.now(UTC)
        self._lock = asyncio.Lock()

    async def validate_order(self, order: Dict[str, Any], positions: List[Dict[str, Any]]) -> Tuple[bool, str]:
        """
        Validera en order mot riskregler.
        
        Args:
            order: Order att validera
            positions: Nuvarande positioner
            
        Returns:
            Tuple med (valid, reason)
        """
        # Implementation...

    async def calculate_position_size(self, symbol: str, entry_price: float, 
                                     stop_loss: float, account_balance: float) -> float:
        """
        Beräkna optimal positionsstorlek baserat på risk.
        
        Args:
            symbol: Symbol att beräkna för
            entry_price: Ingångspris
            stop_loss: Stop-loss nivå
            account_balance: Kontobalans
            
        Returns:
            Optimal positionsstorlek
        """
        # Implementation...

    async def assess_portfolio_risk(self, positions: List[Dict[str, Any]], 
                                   account_balance: float) -> Dict[str, Any]:
        """
        Utför en fullständig riskbedömning av portföljen.
        
        Args:
            positions: Lista med positioner
            account_balance: Kontobalans
            
        Returns:
            Riskbedömning
        """
        # Implementation...
```

## PortfolioManagerAsync

### Funktionalitet

PortfolioManagerAsync tillhandahåller följande funktionalitet:

- Hantering av strategisignaler
- Beräkning av portföljallokering
- Rebalansering av portföljen
- Statusrapportering för portföljen

### Implementation

```python
class PortfolioManagerAsync:
    """Asynkron portföljhanterare för att kombinera strategisignaler."""

    def __init__(self, risk_manager: RiskManagerAsync, strategy_weights: List[StrategyWeight]):
        """
        Initialisera PortfolioManagerAsync.
        
        Args:
            risk_manager: RiskManagerAsync-instans för riskhantering
            strategy_weights: Lista med strategivikter
        """
        self.risk_manager = risk_manager
        self.strategy_weights = {sw.strategy_name: sw for sw in strategy_weights}
        self.last_signals = {}
        self.portfolio_status = {}
        self._lock = asyncio.Lock()

    async def process_signals(self, signals: Dict[str, List[TradeSignal]]) -> CombinedSignal:
        """
        Bearbeta signaler från flera strategier.
        
        Args:
            signals: Dictionary med strateginamn som nycklar och listor av signaler som värden
            
        Returns:
            Kombinerad signal
        """
        # Implementation...

    async def calculate_allocations(self, combined_signal: CombinedSignal, 
                                   account_balance: float) -> Dict[str, float]:
        """
        Beräkna portföljallokering baserat på kombinerad signal.
        
        Args:
            combined_signal: Kombinerad signal
            account_balance: Kontobalans
            
        Returns:
            Dictionary med symbol som nycklar och allokering som värden
        """
        # Implementation...

    async def rebalance_portfolio(self, current_positions: Dict[str, Any], 
                                 target_allocations: Dict[str, float]) -> List[Dict[str, Any]]:
        """
        Generera orders för att rebalansera portföljen.
        
        Args:
            current_positions: Nuvarande positioner
            target_allocations: Målallokeringar
            
        Returns:
            Lista med orders för rebalansering
        """
        # Implementation...

    async def get_portfolio_status(self, positions: Dict[str, Any], 
                                  account_balance: float) -> Dict[str, Any]:
        """
        Hämta portföljstatus.
        
        Args:
            positions: Nuvarande positioner
            account_balance: Kontobalans
            
        Returns:
            Portföljstatus
        """
        # Implementation...
```

## API-integrering

De asynkrona tjänsterna har integrerats med FastAPI genom:

1. Dependency injection i `backend/api/dependencies.py`
2. API-endpoints i `backend/api/portfolio.py` och `backend/api/risk_management.py`

### Dependency Injection

```python
# Exempel från dependencies.py
async def get_risk_manager(config: ConfigService = Depends(get_config_service)) -> RiskManagerAsync:
    """Hämta en RiskManagerAsync-instans."""
    risk_params = config.get_risk_parameters()
    return RiskManagerAsync(risk_params)

async def get_portfolio_manager(
    risk_manager: RiskManagerAsync = Depends(get_risk_manager),
    config: ConfigService = Depends(get_config_service),
) -> PortfolioManagerAsync:
    """Hämta en PortfolioManagerAsync-instans."""
    strategy_weights = []
    for name, weight_config in config.get_strategy_weights().items():
        strategy_weights.append(
            StrategyWeight(
                strategy_name=name,
                weight=weight_config.get("weight", 1.0),
                min_confidence=weight_config.get("min_confidence", 0.5),
                enabled=weight_config.get("enabled", True)
            )
        )
    return PortfolioManagerAsync(risk_manager, strategy_weights)
```

## Endpoints

### Portfolio Endpoints

```python
@router.get("/status", response_model=PortfolioStatusResponse)
async def get_portfolio_status(
    portfolio_manager: PortfolioManagerAsync = Depends(get_portfolio_manager),
    positions_service: PositionsServiceAsync = Depends(get_positions_service_async),
    exchange_service: ExchangeService = Depends(get_exchange_service),
):
    """Hämta portföljstatus."""
    positions = await positions_service.get_positions()
    balances = exchange_service.get_balances()
    
    # Beräkna total kontovärde
    total_balance = sum(balance.get("total", 0) for balance in balances.values())
    
    portfolio_status = await portfolio_manager.get_portfolio_status(positions, total_balance)
    return {
        "status": "success",
        "portfolio_status": portfolio_status,
        "timestamp": datetime.now(UTC).isoformat()
    }
```

### Risk Management Endpoints

```python
@router.get("/assessment", response_model=RiskAssessmentResponse)
async def assess_portfolio_risk(
    risk_manager: RiskManagerAsync = Depends(get_risk_manager),
    positions_service: PositionsServiceAsync = Depends(get_positions_service_async),
    exchange_service: ExchangeService = Depends(get_exchange_service),
):
    """Utför en riskbedömning av nuvarande portfölj."""
    positions = await positions_service.get_positions()
    balances = exchange_service.get_balances()
    
    # Beräkna total kontovärde
    total_balance = sum(balance.get("total", 0) for balance in balances.values())
    
    risk_assessment = await risk_manager.assess_portfolio_risk(positions, total_balance)
    return {
        "status": "success",
        "risk_assessment": risk_assessment,
        "timestamp": datetime.now(UTC).isoformat()
    }
```

## Förbättringar och Fördelar

1. **Prestanda**: Asynkrona tjänster möjliggör parallell exekvering av operationer
2. **Skalbarhet**: Systemet kan hantera fler samtidiga förfrågningar
3. **Responsivitet**: API:et förblir responsivt även under hög belastning
4. **Kodkvalitet**: Tydligare separation av ansvar och bättre testbarhet

## Kända Problem och Framtida Förbättringar

1. **Testning**: Behov av förbättrad testning av asynkrona tjänster
2. **Felhantering**: Förbättra felhantering i asynkrona kontexter
3. **Fullständig Asynkron Implementation**: Vissa delar använder fortfarande synkrona anrop
4. **Caching**: Implementera caching för att minska beräkningsbelastning

## Slutsats

Implementationen av RiskManagerAsync och PortfolioManagerAsync representerar ett viktigt steg i migrationen till FastAPI. Dessa tjänster tillhandahåller kritisk funktionalitet för handelssystemet och deras asynkrona natur förbättrar systemets prestanda och skalbarhet.

Nästa steg är att implementera en fullständig BotManagerAsync-klass och förbättra testningen av de asynkrona tjänsterna.

Uppdaterad: 2025-07-02 