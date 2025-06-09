# 📘 Bitfinex API Integration for Flask Trading Dashboard

Detta dokument är en komplett teknisk referens för att integrera Bitfinex REST- och WebSocket-API med en trading-dashboard byggd i Flask. Det inkluderar autentisering, endpoint-översikt, rate limits, WebSocket-kanaler och praktisk Python-kod med `ccxt` och `websocket`.

## Kom igång

1. Klona projektet  
  ```bash
  git clone git@github.com:<användare>/crypto-bot-dashboard-nexus.git
  cd crypto-bot-dashboard-nexus
  ```
2. Skapa och aktivera virtuell miljö  
  ```bash
  python3 -m venv venv
  source venv/bin/activate     # Windows: venv\Scripts\activate
  ```
3. Installera beroenden
  ```bash
  # Kör från projektets rot
  pip install -r backend/requirements.txt
  ```
  Eller byt katalog först:
  ```bash
  cd backend
  pip install -r requirements.txt
  cd ..
  ```
4. Skapa `.env` i projektets rot  
  ```dotenv
  BITFINEX_API_KEY=DIN_API_KEY
  BITFINEX_API_SECRET=DIN_API_SECRET
  ```
5. Starta Flask-servern
  ```bash
  # Från katalogen backend
  cd backend
  flask run --host=0.0.0.0 --port=5000
  ```
  Öppna http://localhost:5000 i din webbläsare.
6. Kör testerna
  ```bash
  pytest backend/tests
  ```

7. Starta frontend
   ```bash
   npm install
   npm run dev
   ```
   Öppna http://localhost:8080 i din webbläsare.

8. Tradingstrategier och indikatorer
   Alla strategi- och indikatorfiler placeras i `backend/strategies/`.
   Varje strategi måste implementera en `run_strategy(data: pd.DataFrame) -> TradeSignal`-funktion:

   ```python
   def run_strategy(data: pd.DataFrame) -> TradeSignal:
       """Implementerar strategins logik.
       :param data: Historisk prisdata som pandas DataFrame.
       :return: Ett TradeSignal med action och confidence."""
       pass
   ```
   Indikatorer (rena, stateless funktioner) kan läggas till i `backend/strategies/indicators.py`, t.ex.:

   ```python
   def ema(data: pd.Series, length: int) -> pd.Series:
       """Exponential moving average (EMA).
       :param data: Serie av prisvärden.
       :param length: EMA-fönsterlängd.
       :return: Serie med EMA-värden."""
       pass
   ```

   Exempelkod för att köra en strategi:

   ```python
   from backend.strategies.sample_strategy import run_strategy
   import pandas as pd

   df = pd.DataFrame(...)  # historisk prisdata
   signal = run_strategy(df)
   print(signal.action, signal.confidence)
   ```

---

## 🔐 Bitfinex API – Autentisering, Krav och Begränsningar

### 📌 API-Översikt  
API:n är snabb och effektiv, med stöd för Python, NodeJS, Ruby och Golang.  
Docs: https://docs.bitfinex.com/docs/introduction

### 🔑 Autentisering  
För REST-anrop:
```json
{
  "apiKey": "DIN_API_KEY",
  "authSig": "SIGNATUR",
  "authNonce": 1680000000000
}
```
För WebSocket:
```json
{
  "event": "auth",
  "apiKey": "DIN_API_KEY",
  "authSig": "SIGNATUR",
  "authPayload": "AUTH" + NONCE,
  "authNonce": NONCE
}
```
Använd separata nycklar per klient för att undvika nonce-konflikter.

### ⚠️ Rate Limits

#### REST API
* 10–90 förfrågningar/minut beroende på endpoint  
* Fel: `{"error":"ERR_RATE_LIMIT"}`  
* IP blockeras i 60 sek vid överskridande

#### WebSocket API
* Max 5 autentiserade anslutningar/15 s  
* Max 20 offentliga anslutningar/min  
* Upp till 25 kanaler per anslutning  
* Rate-limited i 15 s (auth) eller 60 s (pub)

---

## 🌐 Offentliga REST-endpoints

Domän: `https://api-pub.bitfinex.com/v2/`

### Vanliga endpoints
* GET /tickers  
* GET /ticker/:symbol  
* GET /book/:symbol  
* GET /trades/:symbol  
* GET /candles/trade:{timeframe}:symbol/hist

### Exempel (curl)
```bash
curl https://api-pub.bitfinex.com/v2/ticker/tBTCUSD
curl https://api-pub.bitfinex.com/v2/book/tBTCUSD/P0
curl https://api-pub.bitfinex.com/v2/trades/tBTCUSD/hist
```

---

## 🔐 Autentiserade REST-endpoints

Domän: `https://api.bitfinex.com/v2/`

### Funktioner
* 📊 Saldo och plånböcker  
* 📈 Orderläggning, avbokning, historik  
* 📉 Positioner (futures/margin)  
* 🧾 Fakturering och inställningar

Fullständig doc: https://docs.bitfinex.com/docs/rest-auth

---

## 🔌 Bitfinex WebSocket API

### Endpoints
* Publik: `wss://api-pub.bitfinex.com/ws/2`  
* Autentiserad: `wss://api.bitfinex.com/ws/2`

### Prenumerationsexempel
```json
{
  "event": "subscribe",
  "channel": "ticker",
  "symbol": "tBTCUSD"
}
```

---

## 💻 Exempelkod och användningsfall

### Hämta saldo med ccxt
```python
import ccxt, os

exchange = ccxt.bitfinex({
   'apiKey': os.getenv("BITFINEX_API_KEY"),
   'secret': os.getenv("BITFINEX_API_SECRET"),
})
balance = exchange.fetch_balance()
print(balance)
```

### Placera market-order
```python
order = exchange.create_order(
   symbol='BTC/USD',
   type='market',
   side='buy',
   amount=0.001
)
print(order)
```

### Hämta öppna positioner
```python
positions = exchange.private_get_positions()
print(positions)
```
> OBS: `fetch_positions()` kräver margin/futures-aktivering.

### Hämta candlestick-data (OHLCV)
```python
ohlcv = exchange.fetch_ohlcv('BTC/USD', timeframe='1m', limit=10)
for candle in ohlcv:
   print(candle)
```

### WebSocket: Lyssna på ticker
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

> Anpassa kodexemplen efter behov. För mer info, se Bitfinex officiella dokumentation: https://docs.bitfinex.com/docs/introduction

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
```bash
pytest backend/tests
```

### Frontend
```bash
npm run lint
```
