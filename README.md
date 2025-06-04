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
