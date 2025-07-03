# FastAPI Development CPU Optimization

## Översikt

Denna PR implementerar optimeringar för att minska CPU-användningen under utveckling med FastAPI. Den löser problemet med hög CPU-belastning som orsakas av multipla GlobalNonceManager-instanser, WebSocket-tjänster och hot reload-funktioner.

## Ändringar

1. **Nytt utvecklingsskript (`scripts/development/fastapi_dev.py`)**:
   - Starta FastAPI i olika konfigurationslägen (minimal, api, websocket, full)
   - Inaktivera/aktivera GlobalNonceManager och WebSocket-tjänster
   - Möjlighet att inaktivera hot reload
   - Styrning via miljövariabler

2. **Förbättringar i `fastapi_app.py`**:
   - Stöd för miljövariabler (DISABLE_WEBSOCKET, DISABLE_NONCE_MANAGER)
   - Korrekt hantering av app.state med dictionary istället för dynamiskt skapad klass
   - Korrekt shutdown-procedur för alla tjänster

3. **Modifierad `global_nonce_manager.py`**:
   - Stöd för utvecklingsläge via miljövariabel
   - Inaktivering av kö-processor och logger i utvecklingsläge
   - Förenklad nonce-generering i utvecklingsläge
   - Korrekt shutdown-hantering

4. **Ny dokumentation**:
   - `docs/guides/FASTAPI_DEVELOPMENT_GUIDE.md` med detaljerade instruktioner
   - Uppdaterad `FASTAPI_MIGRATION_STATUS.md` med optimeringsframsteg

## Problemlösning

Ändringarna åtgärdar följande problem:

1. **Multipla GlobalNonceManager-instanser**: Tidigare skapades flera instanser vid omstart av FastAPI-servern som alla körde separata trådar, vilket orsakade hög CPU-användning.
2. **Kontinuerliga WebSocket-anslutningar**: WebSocket-tjänster initierades även vid utveckling av andra delar av systemet.
3. **Uvicorn Hot Reload**: Filewatch-processen för hot reload orsakar konstant disk I/O och CPU-användning.

## Användning

Utvecklare kan nu starta FastAPI-servern i olika lägen beroende på vad de arbetar med:

```bash
# Minimal CPU-användning (inga WebSockets eller GlobalNonceManager)
python scripts/development/fastapi_dev.py --mode minimal

# Endast API-endpoints (utan WebSockets)
python scripts/development/fastapi_dev.py --mode api

# WebSocket-utveckling
python scripts/development/fastapi_dev.py --mode websocket

# Fullständigt läge (alla tjänster aktiverade)
python scripts/development/fastapi_dev.py --mode full

# Inaktivera hot reload för ytterligare CPU-besparing
python scripts/development/fastapi_dev.py --mode minimal --no-reload
```

## Testning

Alla ändringar har testats manuellt för att säkerställa:

1. FastAPI-servern startar korrekt i alla lägen
2. API-endpoints fortsätter att fungera i alla lägen
3. WebSockets fungerar i relevanta lägen
4. CPU-användningen är betydligt lägre i optimerade lägen
5. GlobalNonceManager inaktiveras korrekt i utvecklingsläge

## Framtida förbättringar

1. Implementera automatiska tester för olika lägen
2. Skapa en liknande lösning för frontend-utveckling
3. Utöka stödet för mer detaljerad konfiguration av tjänster 