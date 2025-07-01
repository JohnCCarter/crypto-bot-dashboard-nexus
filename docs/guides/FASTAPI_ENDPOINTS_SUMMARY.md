# FastAPI Endpoints - Sammanfattning

Detta dokument innehåller en sammanställning av alla implementerade FastAPI-endpoints.

## Grundläggande endpoints

- **GET /** - Root-endpoint som omdirigerar till dokumentation
- **GET /api/health** - Hälsokontroll som returnerar serverstatus
- **GET /api/status** - Mer detaljerad statusinformation

## Balans-endpoints

- **GET /api/balances** - Hämta alla tillgängliga balanser
- **GET /api/balances/{currency}** - Hämta balans för specifik valuta

## Order-endpoints

- **GET /api/orders** - Hämta alla öppna ordrar
- **GET /api/orders/{order_id}** - Hämta specifik order med ID
- **POST /api/orders** - Skapa ny order
- **DELETE /api/orders/{order_id}** - Annullera specifik order

## Backtest-endpoints

- **GET /api/backtest/strategies** - Lista alla tillgängliga backtest-strategier
- **POST /api/backtest/run** - Kör en backtest med specifika parametrar
- **GET /api/backtest/{id}** - Hämta resultat från specifik backtest

## Konfiguration-endpoints

- **GET /api/config** - Hämta komplett konfiguration
- **GET /api/config/summary** - Hämta konfigurationssammanfattning
- **GET /api/config/strategies** - Lista alla strategier och vikter
- **GET /api/config/strategy/{name}** - Hämta parametrar för specifik strategi
- **PUT /api/config/strategy/{name}/weight** - Uppdatera vikt för specifik strategi
- **GET /api/config/probability** - Hämta sannolikhetsramverksparametrar
- **PUT /api/config/probability** - Uppdatera sannolikhetsramverksparametrar
- **POST /api/config/validate** - Validera aktuell konfiguration
- **POST /api/config/reload** - Ladda om konfiguration från fil

## Positions-endpoints

- **GET /api/positions** - Hämta alla aktuella positioner
- **GET /api/positions/{symbol}** - Hämta positioner för specifikt handelsinstrument

## Bot-control-endpoints

- **GET /api/bot-status** - Hämta aktuell status för tradingbot
- **POST /api/bot/start** - Starta tradingbot
- **POST /api/bot/stop** - Stoppa tradingbot

## Market-data-endpoints

- **GET /api/market/ohlcv/{symbol}** - Hämta OHLCV-data (ljusstakar) för handelsinstrument
- **GET /api/market/orderbook/{symbol}** - Hämta orderbok för handelsinstrument
- **GET /api/market/ticker/{symbol}** - Hämta ticker-data för handelsinstrument
- **GET /api/market/trades/{symbol}** - Hämta senaste trades för handelsinstrument
- **GET /api/market/markets** - Lista alla tillgängliga marknader

## Orderbok-endpoints

- **GET /api/orderbook/{symbol}** - Hämta detaljerad orderbok för handelsinstrument
- **GET /api/indicators/fvg** - Analysera orderbok för Fair Value Gaps

## Monitoring-endpoints

- **GET /api/monitoring/nonce** - Övervaka nonce-status för API-anrop
- **GET /api/monitoring/cache** - Övervaka cache-prestanda
- **GET /api/monitoring/hybrid-setup** - Kontrollera status för hybrid WebSocket/REST-uppsättning

## Riskhantering-endpoints (nya)

- **GET /api/risk/assessment** - Bedöm portföljens övergripande risknivå baserat på nuvarande positioner och ordrar
- **POST /api/risk/validate/order** - Validera en order mot riskparametrar och aktuell portfölj
- **GET /api/risk/score** - Beräkna risknivån baserat på sannolikhetsdata

## Portföljhantering-endpoints (nya)

- **POST /api/portfolio/allocate** - Beräkna optimal portföljallokering
- **POST /api/portfolio/process-signals** - Bearbeta strategisignaler för att bestämma handelsåtgärder
- **GET /api/portfolio/status** - Hämta aktuell portföljstatus med allokeringar och metriker
- **POST /api/portfolio/rebalance** - Balansera om portföljen för att matcha målallokeringar
- **GET /api/portfolio/live/snapshot** - Hämta realtidsöversikt över portföljen med aktuella marknadspriser
- **GET /api/portfolio/live/performance** - Hämta prestandametriker för portföljen
- **POST /api/portfolio/live/validate-trade** - Validera om en specifik handel kan utföras baserat på aktuella balanser

## Åtkomst till dokumentation

- **GET /docs** - OpenAPI/Swagger UI dokumentation (interaktiv)
- **GET /redoc** - ReDoc dokumentation (alternativ format)
- **GET /openapi.json** - OpenAPI schema i JSON-format

## Fördelar

FastAPI-implementationen ger flera fördelar jämfört med Flask-versionen:

1. **Automatisk validering** av indata och utdata med Pydantic-modeller
2. **Interaktiv dokumentation** med Swagger UI
3. **Förbättrad prestanda** genom asynkron hantering
4. **Bättre felhantering** med detaljerade felmeddelanden
5. **Dependency Injection** för enklare testning och resurssdelning
6. **Typannotering** för förbättrad kodkvalitet och IDE-stöd

FastAPI-servern körs på port 8001 parallellt med Flask-servern på port 5000 för att möjliggöra stegvis testning och övergång. 

## Sammanfattning av implementationsstatus

| Endpoint-kategori | Antal endpoints | Status |
|-------------------|----------------|--------|
| Status | 2 | ✅ Implementerad |
| Balances | 2 | ✅ Implementerad |
| Orders | 4 | ✅ Implementerad |
| Backtest | 4 | ✅ Implementerad |
| Config | 8 | ✅ Implementerad |
| Positions | 2 | ✅ Implementerad |
| Bot Control | 3 | ✅ Implementerad |
| Market Data | 5 | ✅ Implementerad |
| Orderbook | 2 | ✅ Implementerad |
| Monitoring | 3 | ✅ Implementerad |
| Risk Management | 3 | ✅ Implementerad |
| Portfolio Management | 7 | ✅ Implementerad |
| WebSocket | 3 | ⚠️ Delvis implementerad | 