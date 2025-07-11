# 🚀 Crypto Trading Bot Dashboard Nexus

[![Python](https://img.shields.io/badge/python-3.11.9-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/react-18+-blue.svg)](https://reactjs.org/)
[![TypeScript](https://img.shields.io/badge/typescript-5+-blue.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/fastapi-0.115+-green.svg)](https://fastapi.tiangolo.com/)
[![Bitfinex](https://img.shields.io/badge/exchange-bitfinex-orange.svg)](https://www.bitfinex.com/)
[![Status](https://img.shields.io/badge/status-under%20development-yellow.svg)](https://github.com/your-username/crypto-bot-dashboard-nexus)
[![Tests](https://img.shields.io/badge/tests-205%20passed-brightgreen.svg)](https://github.com/your-username/crypto-bot-dashboard-nexus)
[![Code Quality](https://img.shields.io/badge/code%20quality-optimized-blue.svg)](https://github.com/your-username/crypto-bot-dashboard-nexus)

> **Advanced cryptocurrency trading bot with real-time dashboard, live data integration, and comprehensive risk management.**

## ⚠️ **Project Status: Under Active Development**

This project is currently **under active development** and may contain experimental features, breaking changes, and incomplete functionality.

**⚠️ Important Notes:**

- This is **not production-ready** software
- API endpoints and features may change without notice
- Use at your own risk for trading activities
- Always test thoroughly in a safe environment before using with real funds

**🎯 Current Development Focus:**

- ✅ **Code Quality Optimization** (Completed January 2025)
- ✅ **Dependency Cleanup** (Completed January 2025)
- ✅ **Frontend TypeScript Cleanup** (Completed January 2025)
- 🔄 FastAPI migration from Flask
- 🔄 Enhanced WebSocket integration
- 🔄 Improved risk management features
- 🔄 Frontend dashboard enhancements

---

## 📋 Table of Contents

1. [🎯 Project Overview](#project-overview)
2. [⚡ Quick Start](#quick-start)  
3. [🏗 Architecture](#architecture)
4. [📁 Project Structure](#project-structure)
5. [🔧 Installation & Setup](#installation--setup)
6. [🚀 Running the Application](#running-the-application)
7. [🧪 Testing](#testing)
8. [📡 API Documentation](#api-documentation)
9. [⚙️ Configuration](#configuration)
10. [📊 Trading Strategies](#trading-strategies)
11. [🔍 Troubleshooting](#troubleshooting)
12. [🤝 Contributing](#contributing)
13. [🚀 Testning & Optimering](#testning--optimering)
14. [🧹 Recent Cleanup & Optimizations](#recent-cleanup--optimizations)

---

## 🎯 Project Overview

**Crypto Trading Bot Dashboard Nexus** is a sophisticated full-stack application that combines algorithmic trading with real-time market data visualization. Built with modern technologies, it provides a complete trading ecosystem with:

### ✨ Key Features

- 🔴 **Live Trading**: Real-time Bitfinex API integration with WebSocket feeds
- 📊 **Advanced Analytics**: Technical indicators, backtesting, and probability analysis  
- 🎯 **Strategy Engine**: Modular strategy system (EMA, RSI, FVG patterns)
- ⚡ **Real-time Dashboard**: React-based interface with live charts and data
- 🛡️ **Risk Management**: Stop-loss, take-profit, daily loss limits
- 🔔 **Smart Notifications**: Email alerts and system monitoring
- 🧪 **Comprehensive Testing**: 205+ automated tests with optimized execution
- 🐳 **Docker Ready**: Complete containerization support
- 🧹 **Optimized Codebase**: Clean, maintainable code with modern standards

### 🎯 Supported Exchanges

- **Bitfinex** (Primary) - Full REST + WebSocket integration
- Extensible architecture for additional exchanges

---

## 🧹 Recent Cleanup & Optimizations

### ✅ **Completed January 2025**

**Backend Optimizations:**
- ✅ **Null-byte cleanup** - Fixed import errors in API modules
- ✅ **Dependency optimization** - Removed 15+ unused packages
- ✅ **Code formatting** - Applied Black + isort standards
- ✅ **Dead code removal** - Cleaned up unused imports and functions
- ✅ **Test optimization** - 205 tests passing, 12 skipped, 1 expected failure

**Frontend Optimizations:**
- ✅ **TypeScript cleanup** - Reduced ESLint errors from 915 to 53 (94% improvement)
- ✅ **Modern React configuration** - Removed unnecessary React imports
- ✅ **ESLint optimization** - Updated configuration for React 18+ standards
- ✅ **Code quality** - Applied automatic fixes for common issues

**Performance Improvements:**
- ✅ **Test execution** - 47% faster with parallel processing
- ✅ **Dependency management** - Optimized package sizes
- ✅ **Build optimization** - Cleaner development environment

---

## ⚡ Quick Start

Get up and running in under 5 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/your-username/crypto-bot-dashboard-nexus.git
cd crypto-bot-dashboard-nexus

# 2. Set up environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies  
pip install -r backend/requirements.txt
npm install

# 4. Configure API keys
cp .env.example .env
# Edit .env with your Bitfinex credentials

# 5. Start the application
./scripts/deployment/start-dev.sh
```

Open **<http://localhost:8080>** for the dashboard and **<http://localhost:8001>** for API docs.

---

## 🏗 Architecture

```mermaid
graph TB
    %% Frontend
    subgraph "🎨 Frontend"
        UI["⚛️ React UI<br/>TypeScript + Tailwind"]
        WS["🔌 WebSocket Client"]
        API["🌐 API Client"]
    end

    %% API Layer
    subgraph "🚀 API Gateway"
        FastAPI["⚡ FastAPI<br/>Port 8001"]
        WS_API["📡 WebSocket API"]
    end

    %% Core Services
    subgraph "🧠 Core Services"
        BotManager["🤖 Bot Manager"]
        MainBot["🎯 Main Bot"]
        Config["⚙️ Config Service"]
    end

    %% Trading Services
    subgraph "📈 Trading Engine"
        LiveData["🔥 Live Data"]
        OrderService["📋 Order Service"]
        Positions["💼 Positions"]
        Portfolio["📊 Portfolio"]
        Risk["🛡️ Risk Manager"]
    end

    %% Exchange
    subgraph "🔗 Exchange Hub"
        BitfinexWrapper["🔄 Bitfinex Wrapper"]
        ExchangeAsync["⚡ Exchange Async"]
    end

    %% Strategies
    subgraph "🎯 Strategies"
        EMA["📈 EMA Strategy"]
        RSI["📊 RSI Strategy"]
        FVG["🎯 FVG Strategy"]
    end

    %% External
    subgraph "🌍 External"
        BitfinexAPI["🏦 Bitfinex API"]
        Supabase["🗄️ Supabase DB"]
    end

    %% Connections
    UI --> FastAPI
    WS --> WS_API

    FastAPI --> BotManager
    FastAPI --> LiveData
    FastAPI --> OrderService
    FastAPI --> Positions
    FastAPI --> Portfolio
    FastAPI --> Risk

    BotManager --> MainBot
    MainBot --> LiveData
    MainBot --> OrderService
    MainBot --> Positions
    MainBot --> Portfolio
    MainBot --> Risk
    MainBot --> Config

    LiveData --> ExchangeAsync
    OrderService --> ExchangeAsync
    Positions --> ExchangeAsync
    Portfolio --> ExchangeAsync

    ExchangeAsync --> BitfinexWrapper
    BitfinexWrapper --> BitfinexAPI

    MainBot --> EMA
    MainBot --> RSI
    MainBot --> FVG
```

### 🔄 Trading Flow

```mermaid
sequenceDiagram
    participant UI as "🎨 React UI"
    participant API as "🚀 FastAPI"
    participant Bot as "🤖 Bot Manager"
    participant Main as "🎯 Main Bot"
    participant Data as "🔥 Live Data"
    participant Exchange as "⚡ Exchange"
    participant Strategy as "🎯 Strategies"
    participant Risk as "🛡️ Risk Manager"
    participant Orders as "📋 Orders"
    participant Bitfinex as "🏦 Bitfinex"

    Note over UI,Bitfinex: 🚀 Trading Bot Startup
    UI->>API: 🚀 Start Bot Request
    API->>Bot: ⚡ start_bot()
    Bot->>Main: 🎯 main_async()
    
    Note over Main,Bitfinex: 📈 Trading Cycle Begins
    loop 🔄 Every 5 Minutes
        Main->>Data: 📊 Get Live Market Context
        Data->>Exchange: 🔥 Fetch OHLCV Data
        Exchange->>Bitfinex: 🌐 REST API Calls
        Bitfinex-->>Exchange: 📈 Real-time Market Data
        Exchange-->>Data: ⚡ Processed Data
        Data-->>Main: 🎯 Market Context Ready
        
        Note over Main,Strategy: 🧠 Strategy Analysis
        Main->>Strategy: 🎯 Run EMA, RSI, FVG
        Strategy-->>Main: 📊 Trading Signals Generated
        
        Note over Main,Risk: 🛡️ Risk Assessment
        Main->>Risk: 🛡️ Calculate Position Size
        Risk-->>Main: ✅ Position Size & Validation
        
        alt 🎯 Valid Trading Signal
            Note over Main,Orders: 📋 Order Execution
            Main->>Orders: 📋 Place Order
            Orders->>Exchange: ⚡ Submit Order
            Exchange->>Bitfinex: 🏦 Order API Call
            Bitfinex-->>Exchange: ✅ Order Confirmation
            Exchange-->>Orders: 📊 Order Result
            Orders-->>Main: 🎯 Order Status Update
        else ⚠️ Invalid Signal
            Main->>Main: ⏸️ Skip Trading Cycle
        end
        
        Main->>Bot: 📈 Increment Cycle Counter
    end
    
    Note over UI,Bitfinex: 🎉 Trading Cycle Complete
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | React 18 + TypeScript | Modern UI with real-time updates |
| **Backend** | FastAPI + Python 3.11.9 | RESTful API and trading logic |
| **Database** | Supabase (PostgreSQL) | Persistent data storage |
| **Exchange** | Bitfinex API + WebSocket | Live market data and trading |
| **Testing** | Pytest + Vitest + MSW | Comprehensive test coverage |
| **Deployment** | Docker + Docker Compose | Containerized deployment |
| **Code Quality** | Black + ESLint + TypeScript | Modern development standards |

---

## 📁 Project Structure

```
crypto-bot-dashboard-nexus/
├── backend/                    # 🐍 Python FastAPI Backend
│   ├── routes/                # API endpoint definitions
│   ├── services/              # Business logic & external APIs
│   ├── strategies/            # Trading strategy implementations
│   ├── tests/                 # Backend test suite (205+ tests)
│   │   └── integration/       # Real API integration tests
│   ├── fastapi_app.py         # FastAPI application entry point
│   └── requirements.txt       # Python dependencies
├── src/                       # ⚛️ React Frontend
│   ├── components/            # Reusable UI components
│   ├── hooks/                 # Custom React hooks
│   ├── pages/                 # Application pages/views
│   ├── types/                 # TypeScript type definitions
│   └── __tests__/             # Frontend test suite
├── docs/                      # 📚 Documentation
│   ├── development/           # Development guides and roadmaps
│   ├── guides/                # Implementation and usage guides
│   ├── reports/               # Analysis and status reports
│   └── solutions/             # Problem solutions and fixes
├── scripts/                   # 🛠 Development & Deployment Scripts
│   ├── deployment/            # Server startup scripts
│   ├── development/           # Code formatting and utilities
│   └── testing/               # Test automation tools
├── temp/                      # 🗂 Temporary files (Git ignored)
├── public/                    # Static assets
├── docker-compose.yml         # 🐳 Multi-container setup
└── README.md                  # 📖 This file
```

---

## 🔧 Installation & Setup

### Prerequisites

- **Python 3.11.9** ([Download](https://www.python.org/downloads/))
- **Node.js 18+** ([Download](https://nodejs.org/))
- **Git** ([Download](https://git-scm.com/))
- **Bitfinex Account** with API access

### Step 1: Clone Repository

```bash
git clone https://github.com/your-username/crypto-bot-dashboard-nexus.git
cd crypto-bot-dashboard-nexus
```

### Step 2: Backend Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r backend/requirements.txt

# Verify installation
pytest backend/tests/ -v
```

### Step 3: Frontend Setup

```bash
# Install Node.js dependencies
npm install

# Run tests to verify setup
npm run test
```

### Step 4: Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit with your configuration
nano .env  # or use your preferred editor
```

**Required Environment Variables:**

```env
# Bitfinex API Configuration
BITFINEX_API_KEY=your_api_key_here
BITFINEX_API_SECRET=your_api_secret_here

# Supabase Configuration (Optional)
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_key

# Trading Configuration
ENVIRONMENT=development  # development | production
DEBUG=true
```

---

## 🚀 Running the Application

### Option A: Quick Development Start (Recommended)

```bash
# ⚡ Fast start - runs from project root
./scripts/deployment/start-dev.sh
```

### Option B: Flexible Server Management

```bash
# Start both servers with health checks
./scripts/deployment/start-servers.sh

# Start only backend
./scripts/deployment/start-servers.sh backend

# Start only frontend
./scripts/deployment/start-servers.sh frontend
```

### Option C: Windows PowerShell

```powershell
# Windows users with PowerShell
.\scripts\deployment\start-servers.ps1

# With specific mode
.\scripts\deployment\start-servers.ps1 backend
```

### Option D: Manual Start (For Debugging)

```bash
# ⚠️ CRITICAL: Always run from project root!
cd crypto-bot-dashboard-nexus

# Terminal 1 - Backend
cd backend
source venv/Scripts/activate  # Windows Git Bash
python -m uvicorn fastapi_app:app --host 0.0.0.0 --port 8001 --reload

# Terminal 2 - Frontend  
npm run dev
```

> **🚨 Important:** FastAPI must run from backend directory for proper module resolution!

### Docker Deployment

```bash
# Build and start all services
docker-compose up --build

# Background mode
docker-compose up -d
```

### Access Points

| Service | URL | Description |
|---------|-----|-------------|
| **Dashboard** | <http://localhost:8080> | Main trading interface |
| **API** | <http://localhost:8001> | Backend API endpoints |
| **API Docs** | <http://localhost:8001/docs> | Interactive API documentation |

---

## 🧪 Testing

### Running Tests

**Fast Parallel Testing (Recommended):**
```bash
# Run all tests in parallel (auto-detects CPU cores)
python -m pytest backend/tests/

# Run only fast tests in parallel
python scripts/testing/run_tests_optimized.py --fast-only

# Run specific test categories
python scripts/testing/run_tests_optimized.py --category "risk"
python scripts/testing/run_tests_optimized.py --markers "fast or api"
```

**Test Performance:**
- **Parallel execution:** 8 workers (auto-detected)
- **Speed improvement:** 47% faster (from 6min to 3:10min)
- **Test categories:** Fast, slow, integration, unit, api, mock
- **Current status:** 205 passed, 12 skipped, 1 expected failure

**Test Categories:**
- `fast`: Tests < 1s each
- `slow`: Tests > 5s each  
- `integration`: End-to-end tests (requires server)
- `unit`: Isolated unit tests
- `api`: API endpoint tests
- `mock`: Mock-based tests

**Integration Tests:**
```bash
# Run integration tests (requires running server)
pytest backend/tests/integration/ -v
```

**Test Configuration:**
- Parallel execution enabled by default (`-n auto`)
- Integration and slow tests excluded by default
- Max 5 failures before stopping (`--maxfail=5`)
- Duration reporting for slow tests

### Backend Testing

The project uses a **smart test separation strategy** to optimize test execution and avoid false failures from server-dependent tests.

#### Test Categories

```bash
# Standard test run (excludes integration tests requiring server)
pytest backend/tests/ -v --cov=backend

# Run only integration tests (requires FastAPI server on localhost:8001)
pytest backend/tests/ -v -m "integration"

# Run specific test categories
pytest backend/tests/test_strategies.py -v     # Trading strategies
pytest backend/tests/test_indicators.py -v    # Technical indicators
pytest backend/tests/test_fastapi_*.py -v     # FastAPI endpoints
```

#### Test Configuration

- **Standard tests**: Exclude integration tests that require running server
- **Integration tests**: Marked with `@pytest.mark.integration` and run separately
- **Fast tests**: Unit tests and mocked API tests (recommended for development)
- **Slow tests**: Tests with real API calls or complex setup

#### Test Commands

```bash
# Development workflow (fast tests only)
pytest backend/tests/ -v

# Full test suite (including integration)
pytest backend/tests/ -v -m "not integration"  # Standard tests
pytest backend/tests/ -v -m "integration"      # Integration tests

# Specific test files
pytest backend/tests/test_fastapi_orders.py -v
pytest backend/tests/test_risk_manager_async.py -v
```

**Test Coverage:** 205+ tests covering:

- ✅ Trading strategies and signals
- ✅ Technical indicators (EMA, RSI, FVG)
- ✅ API endpoints and responses
- ✅ Risk management logic
- ✅ Database connections
- ✅ WebSocket user data handlers
- ✅ Probability analysis systems
- ✅ Backtest engine and optimization

### Frontend Testing

```bash
# Run component tests
npm run test

# Run with coverage
npm run test:coverage

# Run linting
npm run lint
```

**Test Coverage:** Comprehensive testing with:

- ✅ Component unit tests
- ✅ Integration tests with MSW
- ✅ User interaction testing
- ✅ API response handling

> **Note:** Due to a limitation in FastAPI's dependency override system, some error-path tests for the positions API (e.g. simulating ExchangeError/Exception via query params) are currently skipped. See `backend/tests/test_fastapi_positions.py` and the FastAPI migration status documentation for details.

### Teststatus (2025-01-10)

- **Backend:** 205 passed, 12 skipped, 1 expected failure
- **Frontend:** ESLint errors reduced from 915 to 53 (94% improvement)
- **Code Quality:** Optimized with modern standards
- **Performance:** 47% faster test execution

---

## 📡 API Documentation

### Authentication Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/status` | System health and status |

### Trading Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/balances` | Account balances |
| GET | `/api/positions` | Open positions |
| GET | `/api/orderbook/<symbol>` | Order book data |
| POST | `/api/orders` | Place new order |
| GET | `/api/orders/history` | Order history |

### Bot Control Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/bot/start` | Start trading bot |
| POST | `/api/bot/stop` | Stop trading bot |
| GET | `/api/bot/status` | Bot status and metrics |

### Configuration Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/config` | Current configuration |
| POST | `/api/config` | Update configuration |
| GET | `/api/strategies` | Available strategies |

### Example API Usage

```bash
# Get account balances
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8001/api/balances

# Place a market order
curl -X POST \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{"symbol":"BTC/USD","type":"market","side":"buy","amount":0.001}' \
     http://localhost:8001/api/orders

# Start trading bot
curl -X POST \
     -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8001/api/bot/start
```

---

## ⚙️ Configuration

### Trading Configuration

The system uses `backend/config.json` with JSON Schema validation (`backend/config.schema.json`):

```json
{
  "strategy": {
    "symbol": "BTC/USD",
    "timeframe": "1h",
    "ema_length": 20,
    "ema_fast": 12,
    "ema_slow": 26,
    "rsi_period": 14,
    "atr_multiplier": 2,
    "volume_multiplier": 1.5
  },
  "trading_window": {
    "start_hour": 0,
    "end_hour": 23
  },
  "risk_management": {
    "max_position_size": 0.1,
    "stop_loss_percentage": 0.02,
    "take_profit_percentage": 0.04,
    "daily_loss_limit": 0.05
  }
}
```

### Environment Variables

Create `.env` file from `.env.example`:

```env
# Required - Bitfinex API
BITFINEX_API_KEY=your_api_key
BITFINEX_API_SECRET=your_api_secret

# Optional - Database
DATABASE_URL=sqlite:///./local.db

# Optional - Supabase
SUPABASE_URL=your_url
SUPABASE_ANON_KEY=your_key

# Application
ENVIRONMENT=development
DEBUG=true
FASTAPI_ENV=development
```

---

## 📊 Trading Strategies

### Available Strategies

| Strategy | Description | Parameters |
|----------|-------------|------------|
| **EMA Crossover** | Uses fast/slow EMA crossovers | `ema_fast`, `ema_slow` |
| **RSI Strategy** | Overbought/oversold RSI signals | `rsi_period`, `rsi_overbought`, `rsi_oversold` |
| **FVG Strategy** | Fair Value Gap pattern detection | `atr_multiplier`, `volume_multiplier` |
| **Sample Strategy** | Template for custom strategies | Configurable parameters |

### Strategy Implementation

Each strategy must implement the interface:

```python
def run_strategy(data: pd.DataFrame) -> TradeSignal:
    """
    Execute trading strategy logic.
    
    Args:
        data: OHLCV price data with indicators
        
    Returns:
        TradeSignal: BUY, SELL, or HOLD
    """
    # Strategy implementation
    pass
```

### Backtesting

```bash
# Run strategy backtest
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"strategy":"ema_crossover","symbol":"BTC/USD","timeframe":"1h"}' \
     http://localhost:8001/api/backtest
```

---

## 🔍 Troubleshooting

### Common Issues

#### Backend Won't Start

```bash
# Check if running from project root
pwd  # Should show crypto-bot-dashboard-nexus

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Check FastAPI app path
cd backend
```

#### Frontend Proxy Errors

```bash
# Ensure backend is running on port 8001
curl http://localhost:8001/api/status

# Check Vite proxy configuration in vite.config.ts
```

#### Database Issues

```bash
# Reset SQLite database (if using SQLite)
rm local.db
python -c "from backend.persistence.models import init_db; init_db()"
```

#### Virtual Environment Issues

```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

### Debug Mode

Enable debug logging:

```env
# In .env file
DEBUG=true
FASTAPI_DEBUG=true
```

### Health Checks

```bash
# Backend health
curl http://localhost:8001/api/status

# Frontend health
curl http://localhost:8080

# WebSocket connectivity
# Check browser console for WebSocket errors
```

---

## 🤝 Contributing

### Development Workflow

1. **Fork** the repository
2. **Create** feature branch: `git checkout -b feature/amazing-feature`
3. **Follow** coding standards (see `.cursor/rules/`)
4. **Write** tests for new functionality
5. **Run** full test suite: `pytest backend/tests/ && npm test`
6. **Commit** with conventional format: `feat: add amazing feature`
7. **Push** to branch: `git push origin feature/amazing-feature`
8. **Create** Pull Request

### Code Standards

- **Python**: PEP 8, Black formatting, type hints
- **TypeScript**: Strict mode, ESLint, Prettier
- **Tests**: 80%+ coverage requirement
- **Documentation**: JSDoc for functions, docstrings for Python

### Testing Requirements

```bash
# Backend tests must pass
pytest backend/tests/ -v --cov=backend --cov-report=term-missing

# Frontend tests must pass
npm run test

# Linting must pass
npm run lint
flake8 backend/
```

### Project Structure Guidelines

- **Routes**: RESTful API design only
- **Services**: Business logic separation
- **Components**: Reusable React components
- **Types**: Comprehensive TypeScript definitions

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Bitfinex** for comprehensive API and WebSocket support
- **React + TypeScript** community for excellent tooling
- **FastAPI** ecosystem for robust backend framework
- **ccxt** library for exchange integration

---

## 📞 Support

- **Documentation**: [docs/](docs/)
- **Issues**: [GitHub Issues](https://github.com/your-username/crypto-bot-dashboard-nexus/issues)
- **Wiki**: [Project Wiki](https://github.com/your-username/crypto-bot-dashboard-nexus/wiki)

---

**🚀 Happy Trading!** Built with ❤️ for the crypto community.

## 🚀 Testning & Optimering

Projektet har nu en optimerad teststruktur med:

- Snabba unit- och mock-tester
- Markerade testkategorier (unit, mock, api, integration, e2e, fast, slow)
- Nya test-runner-skript för snabb och CI-optimerad körning

### Exempel på testkommandon

```bash
python scripts/testing/run_tests_fast.py --fast-only      # Endast snabba tester
python scripts/testing/run_tests_fast.py --mock-only      # Endast mock-tester
python scripts/testing/run_tests_fast.py --api-only       # Endast API-tester
python scripts/testing/run_tests_fast.py --slow-only      # Endast långsamma tester
python scripts/testing/run_tests_ci.py --all              # Kör alla tester i optimal ordning
```

Se [docs/guides/TESTING_OPTIMIZATION_GUIDE.md](docs/guides/TESTING_OPTIMIZATION_GUIDE.md) för fullständig dokumentation och rekommenderad arbetsordning.

## Flask phase-out and test status (January 2025)

- Flask is now fully removed from the codebase (no routes, services, requirements, or scripts).
- All start scripts, environment variables, and documentation are updated for FastAPI.
- All legacy Flask tests have been removed (with backup) as they cannot be migrated directly.
- The test suite is free from Flask- and marker-blockers. Remaining test failures are due to logic, data, or mocking issues and will be addressed stepwise.
- **Recommendation:** New API tests should be written using FastAPI's TestClient and modern async patterns.

Backend (FastAPI): <http://localhost:8001>

# Example: Start backend (FastAPI)

python -m uvicorn backend.fastapi_app:app --host 0.0.0.0 --port 8001

# Environment variables (FastAPI only)

FASTAPI_ENV_FILE=.env
FASTAPI_DEV_MODE=true

## Known Issues

- WebSocket User Data: "Cannot run the event loop while another loop is running" may appear in logs. This does not block core functionality but is under investigation.
                                                                                  