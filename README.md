# 📘 Bitfinex API Integration for Flask Trading Dashboard

This document is a complete technical reference for integrating the Bitfinex REST and WebSocket APIs with a trading dashboard built in Flask. It includes authentication, endpoint overview, rate limits, WebSocket channels, and practical Python code using `ccxt` and `websocket`.

## Getting Started

1. Clone the project  

  ```bash
  git clone git@github.com:<user>/crypto-bot-dashboard-nexus.git
  cd crypto-bot-dashboard-nexus
  ```

2. Create and activate a virtual environment  

  ```bash
  python3 -m venv venv
  source venv/bin/activate     # Windows: venv\Scripts\activate
  ```

3. Install dependencies

  ```bash
  # Run from the project root
  pip install -r backend/requirements.txt
  ```

  Or change directory first:

  ```bash
  cd backend
  pip install -r requirements.txt
  cd ..
  ```

4. Create `.env` in the project root  

  ```dotenv
  BITFINEX_API_KEY=YOUR_API_KEY
  BITFINEX_API_SECRET=YOUR_API_SECRET
  ```

5. Start the Flask server

  ```bash
  # From the backend directory
  cd backend
  flask run --host=0.0.0.0 --port=5000
  ```

  Open <http://localhost:5000> in your browser.
6. Run the tests

  ```bash
  pytest backend/tests
  ```

7. Start the frontend

   ```bash
   npm install
   npm run dev
   ```

   Open <http://localhost:8080> in your browser.

8. Trading strategies and indicators
   All strategy and indicator files are placed in `backend/strategies/`.
   Each strategy must implement a `run_strategy(data: pd.DataFrame) -> TradeSignal` function:

   ```python
   def run_strategy(data: pd.DataFrame) -> TradeSignal:
       """Implements the strategy logic.
       :param data: Historical price data as a pandas DataFrame.
       :return: A TradeSignal with action and confidence."""
       pass
   ```

   Indicators (pure, stateless functions) can be added to `backend/strategies/indicators.py`, e.g.:

   ```python
   def ema(data: pd.Series, length: int) -> pd.Series:
       """Exponential moving average (EMA).
       :param data: Series of price values.
       :param length: EMA window length.
       :return: Series with EMA values."""
       pass
   ```

   Example code to run a strategy:

   ```python
   from backend.strategies.sample_strategy import run_strategy
   import pandas as pd

   df = pd.DataFrame(...)  # historical price data
   signal = run_strategy(df)
   print(signal.action, signal.confidence)
   ```

---

## 🔐 Bitfinex API – Authentication, Requirements, and Limitations

### 📌 API Overview  

The API is fast and efficient, with support for Python, NodeJS, Ruby, and Golang.  
Docs: <https://docs.bitfinex.com/docs/introduction>

### 🔑 Authentication  

For REST calls:

```json
{
  "apiKey": "YOUR_API_KEY",
  "authSig": "SIGNATURE",
  "authNonce": 1680000000000
}
```

For WebSocket:

```json
{
  "event": "auth",
  "apiKey": "YOUR_API_KEY",
  "authSig": "SIGNATURE",
  "authPayload": "AUTH" + NONCE,
  "authNonce": NONCE
}
```

Use separate keys per client to avoid nonce conflicts.

### ⚠️ Rate Limits

#### REST API

* 10–90 requests/minute depending on endpoint  
* Error: `{"error":"ERR_RATE_LIMIT"}`  
* IP is blocked for 60 seconds if exceeded

#### WebSocket API

* Max 5 authenticated connections/15 s  
* Max 20 public connections/min  
* Up to 25 channels per connection  
* Rate-limited for 15 s (auth) or 60 s (pub)

---

## 🌐 Public REST Endpoints

Domain: `https://api-pub.bitfinex.com/v2/`

### Common endpoints

* GET /tickers  
* GET /ticker/:symbol  
* GET /book/:symbol  
* GET /trades/:symbol  
* GET /candles/trade:{timeframe}:symbol/hist

### Example (curl)

```bash
curl https://api-pub.bitfinex.com/v2/ticker/tBTCUSD
curl https://api-pub.bitfinex.com/v2/book/tBTCUSD/P0
curl https://api-pub.bitfinex.com/v2/trades/tBTCUSD/hist
```

---

## 🔐 Authenticated REST Endpoints

Domain: `https://api.bitfinex.com/v2/`

### Features

* 📊 Balances and wallets  
* 📈 Order placement, cancellation, history  
* 📉 Positions (futures/margin)  
* 🧾 Billing and settings

Full docs: <https://docs.bitfinex.com/docs/rest-auth>

---

## 🔌 Bitfinex WebSocket API

### Endpoints

* Public: `wss://api-pub.bitfinex.com/ws/2`  
* Authenticated: `wss://api.bitfinex.com/ws/2`

### Subscription example

```json
{
  "event": "subscribe",
  "channel": "ticker",
  "symbol": "tBTCUSD"
}
```

---

## 💻 Example Code and Use Cases

### Fetch balance with ccxt

```python
import ccxt, os

exchange = ccxt.bitfinex({
   'apiKey': os.getenv("BITFINEX_API_KEY"),
   'secret': os.getenv("BITFINEX_API_SECRET"),
})
balance = exchange.fetch_balance()
print(balance)
```

### Place market order

```python
order = exchange.create_order(
   symbol='BTC/USD',
   type='market',
   side='buy',
   amount=0.001
)
print(order)
```

### Fetch open positions

```python
positions = exchange.private_get_positions()
print(positions)
```

> NOTE: `fetch_positions()` requires margin/futures activation.

### Fetch candlestick data (OHLCV)

```python
ohlcv = exchange.fetch_ohlcv('BTC/USD', timeframe='1m', limit=10)
for candle in ohlcv:
   print(candle)
```

### WebSocket: Listen to ticker

```python
import websocket, json

def on_message(ws, message):
   print("Received:", message)

def on_open(ws):
   ws.send(json.dumps({
      "event": "subscribe",
      "channel": "ticker",
      "symbol": "tBTCUSD"
   }))

ws = websocket.WebSocketApp(
   "wss://api-pub.bitfinex.com/ws/2",
   on_message=on_message
)
ws.on_open = on_open
ws.run_forever()
```

---

> Adjust code examples as needed. For more info, see Bitfinex official documentation: <https://docs.bitfinex.com/docs/introduction>

---

# 🚀 Crypto Bot Dashboard Nexus

## Project Overview

This repository provides a full-stack trading dashboard integrating Bitfinex's REST and WebSocket APIs via a Flask backend and a React + TypeScript frontend. It allows you to view balances, order books, positions, place orders, and monitor a trading bot in real time.

## Repository Structure

```text
.
├── backend/             # Flask API (routes, services, tests, Dockerfile)
├── public/              # Static assets for the frontend
├── src/                 # React + TypeScript source (pages, components, hooks)
├── docker-compose.yml   # Docker setup for backend and frontend
├── start-dev.sh         # Quick start script for local development
├── Dockerfile.frontend  # Frontend Dockerfile (dist via Nginx)
├── .env.example         # Template for environment variables
└── README.md            # This file
```

## Local Development (no Docker)

1. Backend:

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   export FLASK_APP=app.py
   flask run --host=0.0.0.0 --port=5000
   ```

2. Frontend:

   ```bash
   npm install
   npm run dev                # Vite dev server on http://localhost:8080
   ```

## Docker Setup

```bash
docker-compose up --build
```  

This launches the Flask API on port 5000 and serves the built frontend on port 8080 via Nginx.

## API Endpoints

| Method | Endpoint                  | Description                      |
|--------|---------------------------|----------------------------------|
| GET    | /api/balances             | List all balances per currency   |
| GET    | /api/orderbook/<symbol>   | Get order book for a trading pair|
| GET    | /api/positions            | Get current positions            |
| GET    | /api/status               | Get API status and mock balance  |
| GET    | /api/config               | Get current strategy configuration|
| POST   | /api/config               | Update strategy configuration     |
| POST   | /api/order                | Place a new order                 |
| POST   | /api/start-bot            | Start the trading bot (returns message, status)             |
| POST   | /api/stop-bot             | Stop the trading bot (returns message, status)              |
| GET    | /api/bot-status           | Get current trading bot status (status, uptime, last_update) |

### Example: Activating the Trading Bot

```bash
# Start the trading bot
curl -X POST http://127.0.0.1:5000/api/start-bot

# Check bot status (status, uptime, last_update)
curl http://127.0.0.1:5000/api/bot-status

# Stop the trading bot
curl -X POST http://127.0.0.1:5000/api/stop-bot
```

## Testing

### Backend

* **Run all tests:**

  ```bash
  pytest backend/tests
  ```

* **Tools:**
  * [pytest](https://docs.pytest.org/)
  * [pytest-cov] for coverage
  * [flake8], [black], [mypy], [isort] for code style and type checking

* **Interpreting results:**
  * All tests should pass ("passed").
  * Error messages are shown directly in the terminal.

### Frontend

* **Run linter:**

  ```bash
  npm run lint
  ```

* **Run tests:**

  ```bash
  npm run test
  ```

* **Tools:**
  * [Vitest](https://vitest.dev/) (test runner)
  * [@testing-library/react](https://testing-library.com/docs/react-testing-library/intro/)
  * [@testing-library/jest-dom] for DOM matchers
  * [jsdom] for simulated DOM environment
  * [MSW (Mock Service Worker)](https://mswjs.io/) for mocked API responses and integration tests

* **Interpreting results:**
  * All tests should pass ("passed").
  * Error messages and code lines are shown directly in the terminal.

#### Integration tests with MSW

* **Purpose:**
  Integration tests ensure that frontend components handle API responses, errors, and edge cases correctly without needing to run a real backend.

* **Setup:**
  * MSW is started automatically via `src/__tests__/setup-msw.ts` (see `vitest.config.ts`).
  * Place integration tests in `src/__tests__/`.
  * Mocked endpoints are defined with `rest.get/post/put...` from MSW.

* **Example:**

  ```ts
  // src/__tests__/balance-card.integration.test.tsx
  import { render, screen } from '@testing-library/react';
  import { rest } from 'msw';
  import { server } from './setup-msw';
  import { BalanceCard } from '../components/BalanceCard';
  import type { Balance } from '../types/trading';

  const mockBalances: Balance[] = [
    { currency: 'BTC', total_balance: 1.234, available: 1.0 },
    { currency: 'ETH', total_balance: 10.5, available: 8.2 },
  ];

  beforeAll(() => {
    server.use(
      rest.get('/api/balances', (req, res, ctx) => {
        return res(ctx.status(200), ctx.json(mockBalances));
      })
    );
  });

  it('renders balances from API', () => {
    render(<BalanceCard balances={mockBalances} isLoading={false} />);
    expect(screen.getByText('BTC')).toBeInTheDocument();
    expect(screen.getByText('ETH')).toBeInTheDocument();
  });
  ```

* **Tips:**
  * Mock more endpoints by adding more handlers in the test files.
  * For components that fetch data themselves, mock fetch/axios calls in the test or expand the integration test.
  * E2E tests are recommended for full user flows.

#### Example component tests

* See `src/components/ui/button.test.tsx`, `src/components/ui/input.test.tsx`, `src/components/ui/textarea.test.tsx`, `src/components/ui/toggle.test.tsx`, `src/components/ui/tabs.test.tsx`, `src/components/ui/dialog.test.tsx` for example component tests.

> **Note:**
> Some advanced UI components (e.g. Select, Dialog, Tabs, and other Radix UI components) use interactions and events that are not always fully supported by jsdom/Vitest. To test these components and full user flows in a real browser, E2E tools like [Cypress](https://www.cypress.io/) or [Playwright](https://playwright.dev/) are recommended.

## Konfiguration

Projektet använder en konfigurationsfil (`backend/config.json`) för att styra tradingstrategier, riskhantering och notifieringar. Strukturen och reglerna för denna fil definieras i `backend/config.schema.json` (JSON Schema).

### Viktiga parametrar

* **strategy**: Inställningar för symbol, timeframe och indikatorer.

* **trading_window**: Handelsfönster och max trades per dag.
* **risk**: Riskparametrar, stop loss, take profit, max daglig förlust.
* **notifications**: E-postnotifieringar och SMTP-inställningar.

Se `backend/config.schema.json` för fullständig beskrivning av alla fält, typer och krav.

### Exempel på config.json

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
    "end_hour": 24,
    "max_trades_per_day": 5
  },
  "risk": {
    "max_daily_loss": 2,
    "lookback": 5,
    "stop_loss_percent": 2,
    "take_profit_percent": 2,
    "risk_per_trade": 0.02
  },
  "notifications": {
    "email_enabled": true,
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 465,
    "sender": "din@email.com",
    "receiver": "din@email.com"
  }
}
```

### Miljövariabler

För känsliga värden (t.ex. e-post, lösenord) rekommenderas att använda miljövariabler och/eller `.env`-fil. Se `.env.example` för mall.

### Validering

Vid uppstart valideras `config.json` automatiskt mot `config.schema.json` för att säkerställa korrekt struktur och giltiga värden.

## FVG-strategi (Fair Value Gap)

FVG-strategin identifierar obalanser i priset (gaps) och genererar tradesignaler när priset återbesöker dessa zoner. Den kan filtrera på gap-storlek och riktning (bullish/bearish).

**Parametrar:**

* `min_gap_size`: Minsta gap-storlek (absolut, i pris) för att inkluderas.
* `direction`: "bullish", "bearish" eller "both" – vilken typ av gap som ska handlas.
* `position_size`: Andel av portfölj att använda per trade (0-1).
* `lookback`: Hur många candles bakåt som FVG-zoner är giltiga.

**Exempel på config.json:**

```json
{
  "fvg_strategy": {
    "min_gap_size": 10,
    "direction": "both",
    "position_size": 0.1,
    "lookback": 5
  }
}
```

**Exempel på API-anrop:**

```json
{
  "strategy": "fvg",
  "data": { ... },
  "parameters": {
    "min_gap_size": 10,
    "direction": "bullish",
    "position_size": 0.1,
    "lookback": 5
  }
}
```

Se även `backend/config.schema.json` för fullständig beskrivning av parametrar.

Leta efter något specifikt i en kod kan du använda dig av  Select-String -Path .\localhost.har -Pattern '"status": 4' i powershell. terminalen.
i bash kan du använda dig av grep '"status": 4' localhost.har
Alternativt ctrl f i vscode.

## 🛠️ API Endpoints – Tradingbot Backend

### **Order API**

#### Skapa order

**POST** `/api/orders`

```json
{
  "symbol": "BTC/USD",
  "order_type": "limit",
  "side": "buy",
  "amount": 0.1,
  "price": 27000
}
```

**Response (201):**

```json
{
  "message": "Order placed successfully",
  "order": {
    "id": "123",
    "symbol": "BTC/USD",
    "order_type": "limit",
    "side": "buy",
    "amount": 0.1,
    "price": 27000,
    "status": "filled"
  }
}
```

#### Hämta order

**GET** `/api/orders/<order_id>`

```json
// Response (200)
{
  "id": "123",
  "symbol": "BTC/USD",
  "status": "filled"
}
```

#### Avbryta order

**DELETE** `/api/orders/<order_id>`

```json
// Response (200)
{
  "message": "Order cancelled successfully"
}
```

#### Lista öppna ordrar

**GET** `/api/orders`

```json
// Response (200)
{
  "orders": [
    { "id": "1", "symbol": "BTC/USD", "status": "open" },
    { "id": "2", "symbol": "ETH/USD", "status": "open" }
  ]
}
```

#### Orderhistorik

**GET** `/api/orders/history`

```json
// Response (200)
[
  {
    "id": "1",
    "symbol": "BTC/USD",
    "order_type": "limit",
    "side": "buy",
    "amount": 0.1,
    "price": 27000,
    "fee": 1.5,
    "status": "filled"
  }
]
```

---

### **Backtest API**

#### Kör backtest

**POST** `/api/backtest/run`

```json
{
  "strategy": "fvg",
  "data": {
    "timestamp": ["2024-01-01 00:00:00", ...],
    "open": [100.0, ...],
    "high": [101.0, ...],
    "low": [99.0, ...],
    "close": [100.0, ...],
    "volume": [1000.0, ...]
  },
  "parameters": {
    "initial_capital": 10000.0,
    "commission": 0.001,
    "slippage": 0.0005
  }
}
```

**Response (200):**

```json
{
  "total_trades": 12,
  "win_rate": 0.58,
  "total_pnl": 1234.56,
  "max_drawdown": -0.12,
  "sharpe_ratio": 1.23,
  "trade_history": [ ... ],
  "equity_curve": { "2024-01-01": 10000, ... }
}
```

#### Optimera strategi

**POST** `/api/backtest/optimize`

```json
{
  "strategy": "fvg",
  "data": { ... },
  "param_grid": {
    "min_gap_size": [5, 10],
    "direction": ["bullish", "bearish"],
    "position_size": [0.05, 0.1],
    "lookback": [3, 5]
  }
}
```

**Response (200):**

```json
{
  "parameters": { "min_gap_size": 5, "direction": "bullish", ... },
  "performance": { "sharpe_ratio": 1.23, ... }
}
```

---

### **Exempel: cURL-anrop**

```bash
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{"symbol":"BTC/USD","order_type":"limit","side":"buy","amount":0.1,"price":27000}'
```

```bash
curl http://localhost:5000/api/orders/history
```

---

## 📝 Git Cheat Sheet

| Kommando                        | Beskrivning                                      |
|----------------------------------|-------------------------------------------------|
| git clone <repo-url>             | Klona repo första gången till ny dator           |
| git status                       | Visa status på ändringar och branch              |
| git pull                         | Hämta och integrera senaste ändringar            |
| git add .                        | Lägg till alla ändrade filer för commit          |
| git commit -m "Meddelande"        | Spara ändringar lokalt med ett meddelande        |
| git push                         | Skicka dina commits till GitHub                  |
| git checkout <branch>            | Byt till en annan branch                         |
| git branch                       | Lista alla brancher                              |
| git branch <ny-branch>           | Skapa en ny branch                               |
| git merge <branch>               | Slå ihop annan branch till aktuell               |
| git stash                        | Tillfälligt spara undan ändringar                |
| git stash pop                    | Återställ senaste stash                          |
| git log --oneline                | Visa commit-historik i kort format               |
| git rebase <branch>              | Lägg dina commits ovanpå annan branch            |
| git rebase --continue            | Fortsätt rebase efter konflikt                   |
| git rebase --abort               | Avbryt pågående rebase                           |
| git reset --hard                 | Återställ allt till senaste commit (var försiktig!) |
