# 📄 Bitfinex Paper Trading Setup Guide

## Översikt

Detta projekt stöder både **utvecklingsläge** (mock data) och **Bitfinex Paper Trading** för realistisk testning av trading-strategier utan att riskera riktiga pengar.

## ✅ Nuvarande Status

- ✅ Backend kör på port 5000
- ✅ Frontend kör på port 8081 
- ✅ API proxy fungerar (frontend → backend)
- ✅ Utvecklingsläge aktivt (mock balance data)
- ✅ Enhetlig API-nyckel konfiguration (BITFINEX_API_KEY/SECRET)

## 🔑 Steg 1: Skapa Bitfinex Paper Trading Account

### 1.1 Logga in på Bitfinex
1. Gå till [bitfinex.com](https://bitfinex.com)
2. Logga in på ditt huvudkonto

### 1.2 Skapa Sub Account för Paper Trading
1. Gå till **Settings** → **Sub Accounts**
2. Klicka **Create Sub Account**
3. Välj **Paper Trading** som account type
4. Namnge kontot (t.ex. "Trading Bot Paper")
5. Sätt initial paper balance (t.ex. $10,000)

### 1.3 Skapa API Nycklar
1. Gå till **Settings** → **API** 
2. Klicka **Create New Key**
3. **Viktigt**: Välj din Paper Trading sub account
4. Aktivera permissions:
   - ✅ **Account History**: ON
   - ✅ **Orders**: ON  
   - ✅ **Positions**: ON
   - ✅ **Wallets**: ON
   - ⚠️ **Funding**: ON (endast om du vill använda margin)
5. **Kopiera API Key och Secret** (visas endast en gång!)

## 🔧 Steg 2: Konfigurera Bot

### 2.1 Uppdatera .env filen
```bash
# Öppna .env filen
nano .env

# Ersätt placeholder-värdena:
BITFINEX_API_KEY=din_riktiga_paper_api_key_här
BITFINEX_API_SECRET=din_riktiga_paper_api_secret_här
```

### 2.2 Starta om Backend
```bash
# Stoppa nuvarande backend
pkill -f flask

# Aktivera virtual environment
source venv/bin/activate

# Starta backend på nytt
cd backend && python -m flask run --debug --host=0.0.0.0 --port=5000
```

## 🧪 Steg 3: Testa Paper Trading

### 3.1 Verifiera Balance API
```bash
curl -s http://localhost:5000/api/balances
```

**Förväntat resultat med paper trading:**
```json
[
  {
    "available": 10000.0,
    "currency": "USD", 
    "total_balance": 10000.0
  }
]
```

### 3.2 Testa Order Placement
```bash
curl -X POST http://localhost:5000/api/orders \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTC/USD",
    "order_type": "limit",
    "side": "buy", 
    "amount": 0.001,
    "price": 40000
  }'
```

## 🔍 Felsökning

### Problem: "API keys not configured properly"
- ✅ Kontrollera att du har ersatt placeholder-värdena i .env
- ✅ Starta om backend efter .env ändringar
- ✅ Kontrollera att API-nycklarna är från Paper Trading sub account

### Problem: "Failed to fetch balances from Bitfinex"
- ✅ Kontrollera att API permissions är korrekt satta
- ✅ Verifiera att sub account är Paper Trading typ
- ✅ Testa API-nycklar direkt mot Bitfinex API

### Problem: WebSocket fel i frontend
- ✅ Detta är normalt i development mode (React Strict Mode)
- ✅ WebSocket fungerar korrekt i production builds
- ✅ Data hämtas ändå via REST API

## 📊 Vad Du Kan Göra Nu

### Med Paper Trading Aktivt:
1. **Testa Trading Strategier**: Se hur EMA Crossover, RSI, FVG strategier presterar
2. **Backtest mot Live Data**: Jämför historiska backtest med paper trading
3. **Risk Management**: Testa stop-loss, take-profit, position sizing
4. **Portfolio Management**: Testa multi-strategy approach
5. **Real-time Data**: WebSocket market data från Bitfinex

### Säkerhetsfördelar:
- 🛡️ **Inga riktiga pengar** påverkas
- 🛡️ **Realistic orderbook** och execution
- 🛡️ **Real market conditions** och latency
- 🛡️ **Full API compatibility** med live trading

## ⚡ Nästa Steg

1. **Konfigurera dina Paper Trading API-nycklar**
2. **Testa order placement och management**  
3. **Optimera trading strategier med real data**
4. **Förbered för eventuell live trading**

---

**🚨 Viktigt**: Paper Trading-nycklar fungerar ENDAST med Paper Trading sub accounts. De kan inte användas för live trading, vilket ger extra säkerhet.