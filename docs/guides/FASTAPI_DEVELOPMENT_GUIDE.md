# FastAPI Development Guide

Detta dokument beskriver hur du kan använda optimerade utvecklingsverktyg för att minska CPU-användning och anpassa konfigurationen efter dina aktuella utvecklingsbehov.

## CPU-användningsproblem

Vid utveckling av FastAPI-applikationen har vi identifierat att flera komponenter kan orsaka hög CPU-användning:

1. **Multipla GlobalNonceManager-instanser** - Var och en av dessa kör en separat thread för att hantera nonces, vilket kan leda till flera parallella processer
2. **WebSocket-anslutningar** - Kontinuerlig data-polling mot Bitfinex API
3. **Watchfiles/hot reload** - Kontinuerlig filövervakning
4. **Uvicorn-servern** med arbetare och reloader-processer

## Optimerad utveckling med `fastapi_dev.py`

För att adressera dessa problem har vi skapat ett utvecklingsskript som låter dig starta FastAPI-servern med olika konfigurationsalternativ beroende på vad du arbetar med.

### Installation

Skriptet finns i `scripts/development/fastapi_dev.py`.

### Användning

```bash
# Windows/PowerShell
python scripts\development\fastapi_dev.py --mode minimal --no-reload

# Linux/macOS
python scripts/development/fastapi_dev.py --mode minimal --no-reload
```

### Tillgängliga lägen

1. **minimal** (standard) - Stänger av WebSockets och GlobalNonceManager för lägsta CPU-användning
   ```
   python scripts/development/fastapi_dev.py --mode minimal
   ```

2. **api** - Stänger av WebSockets men behåller GlobalNonceManager för API-utveckling
   ```
   python scripts/development/fastapi_dev.py --mode api
   ```

3. **websocket** - Aktiverar WebSockets och GlobalNonceManager för WebSocket-utveckling
   ```
   python scripts/development/fastapi_dev.py --mode websocket
   ```

4. **full** - Aktiverar alla tjänster (samma som standardbeteende)
   ```
   python scripts/development/fastapi_dev.py --mode full
   ```

### Andra alternativ

- `--no-reload` - Inaktiverar hot reload för ytterligare CPU-besparing
- `--port PORT` - Ange port (standard: 8001)

## Exempel på användning

### När du arbetar med enbart API-endpoints

```bash
python scripts/development/fastapi_dev.py --mode api
```

### När du arbetar med WebSockets

```bash
python scripts/development/fastapi_dev.py --mode websocket
```

### För minimal CPU-användning när du testar frontend utan behov av realtidsdata

```bash
python scripts/development/fastapi_dev.py --mode minimal --no-reload
```

## Teknisk information

Skriptet använder miljövariabler via en temporär `.env.fastapi_dev`-fil för att kontrollera vilka komponenter som ska aktiveras:

- `DISABLE_WEBSOCKET=true` - Inaktiverar WebSocket-tjänsterna
- `DISABLE_NONCE_MANAGER=true` - Inaktiverar GlobalNonceManager
- `MOCK_EXCHANGE_SERVICE=true` - Använder mock exchange-tjänst för snabbare utveckling

Dessa inställningar appliceras i FastAPI-applikationen i `backend/fastapi_app.py`.

## Felsökning

Om du fortfarande upplever hög CPU-användning, prova följande:

1. Använd `--no-reload` flaggan för att stänga av filövervakning
2. Kontrollera att inga andra FastAPI-instanser körs i bakgrunden
3. Om du arbetar i VS Code, stäng av automatisk typkontroll/linting om möjligt 