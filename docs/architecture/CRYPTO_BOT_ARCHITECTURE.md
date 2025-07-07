# 🏗️ Crypto Trading Bot - Arkitekturdiagram

## 📊 Systemöversikt

```mermaid
graph TB
    %% Frontend Layer
    subgraph "🌐 Frontend (React + TypeScript)"
        UI[UI Components]
        WS[WebSocket Client]
        API[API Client]
    end

    %% API Gateway Layer
    subgraph "🚪 API Gateway (FastAPI + Flask)"
        FastAPI[FastAPI Server<br/>Port 8001]
        Flask[Flask Server<br/>Port 5000]
        WS_API[WebSocket API]
    end

    %% Core Services Layer
    subgraph "⚙️ Core Services"
        BotManager[Bot Manager Async]
        MainBot[Main Bot Async]
        ConfigService[Config Service]
        EventLogger[Event Logger]
    end

    %% Trading Services Layer
    subgraph "📈 Trading Services"
        LiveData[Live Data Service Async]
        OrderService[Order Service Async]
        PositionsService[Positions Service Async]
        PortfolioManager[Portfolio Manager Async]
        RiskManager[Risk Manager Async]
        TradingWindow[Trading Window Async]
    end

    %% Data Services Layer
    subgraph "💾 Data Services"
        CacheService[Cache Service]
        NonceManager[Global Nonce Manager]
        MonitoringService[Monitoring Service]
    end

    %% Exchange Integration Layer
    subgraph "🔗 Exchange Integration"
        BitfinexWrapper[Bitfinex Client Wrapper]
        ExchangeAsync[Exchange Async]
        WebSocketUserData[WebSocket User Data Service]
        WebSocketMarket[WebSocket Market Service]
    end

    %% Strategy Layer
    subgraph "🧠 Trading Strategies"
        EMA[EMA Crossover Strategy]
        RSI[RSI Strategy]
        FVG[FVG Strategy]
        Indicators[Technical Indicators]
    end

    %% External APIs
    subgraph "🌍 External APIs"
        BitfinexAPI[Bitfinex API]
        Supabase[Supabase Database]
    end

    %% Connections
    UI --> API
    UI --> WS
    API --> FastAPI
    API --> Flask
    WS --> WS_API

    FastAPI --> BotManager
    FastAPI --> LiveData
    FastAPI --> OrderService
    FastAPI --> PositionsService
    FastAPI --> PortfolioManager
    FastAPI --> RiskManager
    FastAPI --> MonitoringService

    Flask --> BotManager
    Flask --> LiveData
    Flask --> OrderService
    Flask --> PositionsService
    Flask --> PortfolioManager
    Flask --> RiskManager
    Flask --> MonitoringService

    BotManager --> MainBot
    MainBot --> LiveData
    MainBot --> OrderService
    MainBot --> PositionsService
    MainBot --> PortfolioManager
    MainBot --> RiskManager
    MainBot --> TradingWindow
    MainBot --> ConfigService
    MainBot --> EventLogger

    LiveData --> ExchangeAsync
    OrderService --> ExchangeAsync
    PositionsService --> ExchangeAsync
    PortfolioManager --> ExchangeAsync

    ExchangeAsync --> BitfinexWrapper
    WebSocketUserData --> BitfinexWrapper
    WebSocketMarket --> BitfinexWrapper

    BitfinexWrapper --> BitfinexAPI
    WebSocketUserData --> BitfinexAPI
    WebSocketMarket --> BitfinexAPI

    MainBot --> EMA
    MainBot --> RSI
    MainBot --> FVG
    EMA --> Indicators
    RSI --> Indicators
    FVG --> Indicators

    CacheService --> LiveData
    CacheService --> OrderService
    CacheService --> PositionsService
    NonceManager --> BitfinexWrapper
    MonitoringService --> BotManager
    MonitoringService --> CacheService
    MonitoringService --> NonceManager

    EventLogger --> Supabase
    ConfigService --> Supabase

    %% Styling
    classDef frontend fill:#e1f5fe
    classDef api fill:#f3e5f5
    classDef core fill:#e8f5e8
    classDef trading fill:#fff3e0
    classDef data fill:#fce4ec
    classDef exchange fill:#f1f8e9
    classDef strategy fill:#e0f2f1
    classDef external fill:#fafafa

    class UI,WS,API frontend
    class FastAPI,Flask,WS_API api
    class BotManager,MainBot,ConfigService,EventLogger core
    class LiveData,OrderService,PositionsService,PortfolioManager,RiskManager,TradingWindow trading
    class CacheService,NonceManager,MonitoringService data
    class BitfinexWrapper,ExchangeAsync,WebSocketUserData,WebSocketMarket exchange
    class EMA,RSI,FVG,Indicators strategy
    class BitfinexAPI,Supabase external
```

## 🔄 Dataflöde

```mermaid
sequenceDiagram
    participant UI as Frontend UI
    participant API as FastAPI/Flask
    participant Bot as Bot Manager
    participant Main as Main Bot
    participant Data as Live Data Service
    participant Exchange as Exchange Service
    participant Strategy as Trading Strategies
    participant Risk as Risk Manager
    participant Orders as Order Service
    participant Bitfinex as Bitfinex API

    UI->>API: Start Bot Request
    API->>Bot: start_bot()
    Bot->>Main: main_async()
    
    loop Trading Cycle
        Main->>Data: get_live_market_context()
        Data->>Exchange: fetch_market_data()
        Exchange->>Bitfinex: REST API calls
        Bitfinex-->>Exchange: Market data
        Exchange-->>Data: Processed data
        Data-->>Main: Market context
        
        Main->>Strategy: Run strategies (EMA, RSI, FVG)
        Strategy-->>Main: Trading signals
        
        Main->>Risk: calculate_position_size()
        Risk-->>Main: Position size & validation
        
        alt Valid signal
            Main->>Orders: place_order()
            Orders->>Exchange: submit_order()
            Exchange->>Bitfinex: Order API
            Bitfinex-->>Exchange: Order confirmation
            Exchange-->>Orders: Order result
            Orders-->>Main: Order status
        end
        
        Main->>Bot: increment_cycle()
    end
```

## 🏛️ Komponentarkitektur

### **Frontend Layer**
- **React + TypeScript**: Modern UI med komponenter
- **WebSocket Client**: Realtidsdata för marknadsuppdateringar
- **API Client**: REST API-anrop till backend

### **API Gateway Layer**
- **FastAPI Server** (Port 8001): Modern asynkron API
- **Flask Server** (Port 5000): Legacy API (under migration)
- **WebSocket API**: Realtidskommunikation

### **Core Services Layer**
- **Bot Manager Async**: Central bot-kontroll och tillståndshantering
- **Main Bot Async**: Huvudlogik för trading-cykler
- **Config Service**: Konfigurationshantering
- **Event Logger**: Loggning och övervakning

### **Trading Services Layer**
- **Live Data Service Async**: Realtidsmarknadsdata
- **Order Service Async**: Orderhantering
- **Positions Service Async**: Positioner och P&L
- **Portfolio Manager Async**: Portföljhantering
- **Risk Manager Async**: Riskhantering och position sizing
- **Trading Window Async**: Trading-tidsfönster

### **Data Services Layer**
- **Cache Service**: Aggressiv caching för prestanda
- **Global Nonce Manager**: Nonce-hantering för API-anrop
- **Monitoring Service**: Systemövervakning

### **Exchange Integration Layer**
- **Bitfinex Client Wrapper**: Wrapper för Bitfinex API
- **Exchange Async**: Asynkron exchange-integration
- **WebSocket Services**: Realtidsdata via WebSocket

### **Strategy Layer**
- **EMA Crossover Strategy**: Moving average-strategi
- **RSI Strategy**: Relative Strength Index-strategi
- **FVG Strategy**: Fair Value Gap-strategi
- **Technical Indicators**: Tekniska indikatorer

## 🔧 Teknisk Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Frontend | React + TypeScript + Tailwind | Modern UI |
| API Gateway | FastAPI + Flask | REST API |
| Core Logic | Python 3.11 + asyncio | Trading logic |
| Database | Supabase (PostgreSQL) | Persistence |
| Exchange | Bitfinex API | Market data & trading |
| Caching | In-memory + Redis | Performance |
| Monitoring | Custom logging | System health |

## 🚀 Deployment

```mermaid
graph LR
    subgraph "🐳 Docker Containers"
        Frontend[Frontend Container<br/>Port 3000]
        Backend[Backend Container<br/>Port 8001/5000]
        Database[Database Container<br/>Port 5432]
    end

    subgraph "🌐 External Services"
        Bitfinex[Bitfinex API]
        Supabase[Supabase Cloud]
    end

    Frontend --> Backend
    Backend --> Database
    Backend --> Bitfinex
    Backend --> Supabase
```

## 📈 Prestanda & Skalbarhet

- **Asynkron arkitektur**: Högt genomflöde med asyncio
- **Aggressiv caching**: Minska API-anrop till Bitfinex
- **Nonce-hantering**: Undvik rate limiting
- **Event-driven logging**: Effektiv loggning
- **Modulär design**: Enkel att skala och underhålla

## 🔒 Säkerhet

- **API Key Management**: Säker hantering av Bitfinex-nycklar
- **Nonce Validation**: Förhindra replay-attacker
- **Input Validation**: Pydantic-modeller för validering
- **Error Handling**: Robust felhantering
- **Logging**: Säker loggning utan känslig data 