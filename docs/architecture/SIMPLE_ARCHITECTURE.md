# 🏗️ Crypto Trading Bot - Enkel Arkitektur

## 📊 Systemöversikt

```mermaid
graph TB
    %% Frontend
    subgraph "🌐 Frontend"
        UI[React UI]
    end

    %% API Layer
    subgraph "🚪 API Layer"
        FastAPI[FastAPI<br/>Port 8001]
        Flask[Flask<br/>Port 5000]
    end

    %% Core Services
    subgraph "⚙️ Core Services"
        BotManager[Bot Manager]
        MainBot[Main Bot]
        Config[Config Service]
    end

    %% Trading Services
    subgraph "📈 Trading Services"
        LiveData[Live Data]
        Orders[Order Service]
        Positions[Positions]
        Portfolio[Portfolio]
        Risk[Risk Manager]
    end

    %% Exchange
    subgraph "🔗 Exchange"
        Bitfinex[Bitfinex API]
    end

    %% Strategies
    subgraph "🧠 Strategies"
        EMA[EMA Strategy]
        RSI[RSI Strategy]
        FVG[FVG Strategy]
    end

    %% Connections
    UI --> FastAPI
    UI --> Flask
    FastAPI --> BotManager
    Flask --> BotManager
    BotManager --> MainBot
    MainBot --> LiveData
    MainBot --> Orders
    MainBot --> Positions
    MainBot --> Portfolio
    MainBot --> Risk
    MainBot --> EMA
    MainBot --> RSI
    MainBot --> FVG
    LiveData --> Bitfinex
    Orders --> Bitfinex
    Positions --> Bitfinex
```

## 🔄 Trading Flow

```mermaid
sequenceDiagram
    participant Bot as Trading Bot
    participant Data as Live Data
    participant Strategy as Strategies
    participant Risk as Risk Manager
    participant Orders as Order Service
    participant Exchange as Bitfinex

    Bot->>Data: Get market data
    Data->>Exchange: Fetch OHLCV
    Exchange-->>Data: Market data
    Data-->>Bot: Processed data
    
    Bot->>Strategy: Run EMA, RSI, FVG
    Strategy-->>Bot: Trading signals
    
    Bot->>Risk: Calculate position size
    Risk-->>Bot: Position & validation
    
    Bot->>Orders: Place order
    Orders->>Exchange: Submit order
    Exchange-->>Orders: Confirmation
    Orders-->>Bot: Order status
```

## 🏛️ Komponenter

| Komponent | Syfte | Status |
|-----------|-------|--------|
| **Frontend** | React UI för kontroll | ✅ Aktiv |
| **FastAPI** | Modern API (Port 8001) | 🔄 Migration |
| **Flask** | Legacy API (Port 5000) | ✅ Aktiv |
| **Bot Manager** | Bot-kontroll | ✅ Aktiv |
| **Main Bot** | Trading-logik | ✅ Aktiv |
| **Live Data** | Realtidsdata | ✅ Aktiv |
| **Order Service** | Orderhantering | ✅ Aktiv |
| **Risk Manager** | Riskhantering | ✅ Aktiv |
| **Strategies** | EMA, RSI, FVG | ✅ Aktiva |
| **Bitfinex API** | Exchange-integration | ✅ Aktiv |

## 🔧 Teknisk Stack

- **Frontend**: React + TypeScript + Tailwind CSS
- **Backend**: Python 3.11 + FastAPI + Flask
- **Database**: Supabase (PostgreSQL)
- **Exchange**: Bitfinex API
- **Deployment**: Docker + Docker Compose

## 📈 Funktioner

- ✅ **Realtidsdata** från Bitfinex
- ✅ **Multi-strategy** trading (EMA, RSI, FVG)
- ✅ **Risk management** med position sizing
- ✅ **Portfolio tracking** och P&L
- ✅ **WebSocket** för realtidsuppdateringar
- ✅ **Event logging** och övervakning
- ✅ **Paper trading** för testning
- 🔄 **FastAPI migration** pågår 