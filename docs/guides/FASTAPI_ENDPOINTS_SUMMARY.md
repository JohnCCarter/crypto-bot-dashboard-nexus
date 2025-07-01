# FastAPI Endpoints Summary

Detta dokument innehåller en sammanfattning av alla endpoints som implementerats i FastAPI-versionen av systemet.

## Status Endpoints

| Metod | Endpoint | Beskrivning | Status |
|-------|----------|-------------|--------|
| GET | `/api/status` | Hämta systemstatus | ✅ Implementerad |
| GET | `/api/health` | Hälsokontroll | ✅ Implementerad |

## Balances Endpoints

| Metod | Endpoint | Beskrivning | Status |
|-------|----------|-------------|--------|
| GET | `/api/balances` | Hämta saldoinformation | ✅ Implementerad |

## Orders Endpoints

| Metod | Endpoint | Beskrivning | Status |
|-------|----------|-------------|--------|
| GET | `/api/orders` | Hämta ordrar | ✅ Implementerad |
| POST | `/api/orders` | Skapa order | ✅ Implementerad |
| DELETE | `/api/orders/{order_id}` | Avbryt order | ✅ Implementerad |

## Backtest Endpoints

| Metod | Endpoint | Beskrivning | Status |
|-------|----------|-------------|--------|
| GET | `/api/backtest/strategies` | Hämta tillgängliga strategier | ✅ Implementerad |
| POST | `/api/backtest/run` | Kör backtest | ✅ Implementerad |
| GET | `/api/backtest/results/{backtest_id}` | Hämta backtestresultat | ✅ Implementerad |

## Config Endpoints

| Metod | Endpoint | Beskrivning | Status |
|-------|----------|-------------|--------|
| GET | `/api/config` | Hämta aktuell konfiguration | ✅ Implementerad |
| POST | `/api/config` | Uppdatera konfiguration | ✅ Implementerad |
| GET | `/api/config/summary` | Hämta konfigurationssammanfattning | ✅ Implementerad |
| GET | `/api/config/strategies` | Hämta strategikonfiguration | ✅ Implementerad |
| GET | `/api/config/strategy/{strategy_name}` | Hämta parametrar för en specifik strategi | ✅ Implementerad |
| PUT | `/api/config/strategy/{strategy_name}/weight` | Uppdatera strategivikt | ✅ Implementerad |
| GET | `/api/config/probability` | Hämta sannolikhetskonfiguration | ✅ Implementerad |
| PUT | `/api/config/probability` | Uppdatera sannolikhetskonfiguration | ✅ Implementerad |
| GET | `/api/config/validate` | Validera aktuell konfiguration | ✅ Implementerad |
| POST | `/api/config/reload` | Tvinga omläsning av konfiguration från fil | ✅ Implementerad |

## Positions Endpoints

| Metod | Endpoint | Beskrivning | Status |
|-------|----------|-------------|--------|
| GET | `/api/positions` | Hämta aktuella positioner | ✅ Implementerad |

## Bot Control Endpoints

| Metod | Endpoint | Beskrivning | Status |
|-------|----------|-------------|--------|
| GET | `/api/bot/status` | Hämta botstatus | ✅ Implementerad |
| POST | `/api/bot/start` | Starta bot | ✅ Implementerad |
| POST | `/api/bot/stop` | Stoppa bot | ✅ Implementerad |

## Market Data Endpoints

| Metod | Endpoint | Beskrivning | Status |
|-------|----------|-------------|--------|
| GET | `/api/market/ohlcv` | Hämta OHLCV-data | ✅ Implementerad |
| GET | `/api/market/ticker` | Hämta ticker-data | ✅ Implementerad |
| GET | `/api/market/orderbook` | Hämta orderbook-data | ✅ Implementerad |
| GET | `/api/market/trades` | Hämta senaste trades | ✅ Implementerad |
| GET | `/api/market/markets` | Hämta tillgängliga marknader | ✅ Implementerad |
| GET | `/api/market/status` | Hämta marknadsstatus | ✅ Implementerad |
| GET | `/api/market/validate` | Validera marknadssymbol | ✅ Implementerad |

## Orderbook Endpoints

| Metod | Endpoint | Beskrivning | Status |
|-------|----------|-------------|--------|
| GET | `/api/orderbook/{symbol}` | Hämta orderbook för en specifik symbol | ✅ Implementerad |

## Monitoring Endpoints

| Metod | Endpoint | Beskrivning | Status |
|-------|----------|-------------|--------|
| GET | `/api/monitoring/nonce` | Hämta nonce-statistik | ✅ Implementerad |
| GET | `/api/monitoring/cache` | Hämta cache-statistik | ✅ Implementerad |
| GET | `/api/monitoring/hybrid` | Hämta hybrid-setup-information | ✅ Implementerad |

## Risk Management Endpoints

| Metod | Endpoint | Beskrivning | Status |
|-------|----------|-------------|--------|
| GET | `/api/risk/validate-order` | Validera order mot riskparametrar | ⬜ Planerad |
| GET | `/api/risk/assessment` | Utför riskbedömning | ⬜ Planerad |
| GET | `/api/risk/score` | Beräkna riskscore | ⬜ Planerad |

## Portfolio Endpoints

| Metod | Endpoint | Beskrivning | Status |
|-------|----------|-------------|--------|
| GET | `/api/portfolio/allocation` | Hämta portföljallokeringar | ⬜ Planerad |
| POST | `/api/portfolio/optimize` | Optimera portfölj | ⬜ Planerad |

## Sammanfattning

- **Totalt antal endpoints:** 32
- **Implementerade endpoints:** 27
- **Planerade endpoints:** 5
- **Implementationsprocent:** 84%

Uppdaterad: 2025-07-01 