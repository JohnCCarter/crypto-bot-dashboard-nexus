# Guide för hemarbete med FastAPI-migrationen

Detta dokument innehåller instruktioner för att fortsätta arbetet med FastAPI-migrationen när du arbetar hemifrån.

## Förberedelser

1. Klona projektet från GitHub om du inte redan har gjort det:
   ```bash
   git clone <repository-url>
   cd crypto-bot-dashboard-nexus
   ```

2. Installera alla beroenden:
   ```bash
   pip install -r backend/requirements.txt
   npm install
   ```

3. Skapa en `.env`-fil baserad på `.env.example` och fyll i nödvändiga miljövariabler.

## Starta projektet

1. Starta FastAPI-servern från projektroten:
   ```bash
   # Windows PowerShell
   python -m backend.fastapi_app
   ```

2. Starta Flask-servern i en annan terminal:
   ```bash
   # Windows PowerShell
   cd backend
   python -m flask run
   ```

3. Starta frontend-utvecklingsservern:
   ```bash
   # Windows PowerShell
   npm run dev
   ```

## Fortsätta med FastAPI-migrationen

### Viktigt: Lösa ImportError först!

Det finns ett kritiskt problem med ImportError för `get_positions_service_async` som måste åtgärdas innan fortsatt migration. Detta problem har nu lösts genom att lägga till projektroten i Python-sökvägen i `backend/fastapi_app.py`.

### Nästa steg i migrationen

1. Migrera bot control-endpoints
   - Implementera asynkrona versioner av bot control-funktionerna
   - Uppdatera API-endpoints i FastAPI

2. Implementera BotManagerAsync
   - Skapa en asynkron version av BotManager
   - Uppdatera beroenden i FastAPI

3. Förbättra testning av asynkrona tjänster
   - Anpassa tester för FastAPI-miljön
   - Skapa nya tester för asynkrona tjänster

### Dokumentation

Följande dokumentation är viktig att läsa för att förstå projektet och migrationen:

- `docs/guides/FASTAPI_MIGRATION_PLAN.md` - Övergripande plan för migrationen
- `docs/guides/FASTAPI_MIGRATION_STATUS.md` - Aktuell status för migrationen
- `docs/reports/FASTAPI_ASYNC_POSITIONS_SERVICE_IMPLEMENTATION.md` - Detaljer om implementationen av asynkron positions-service

## Felsökning

Om du stöter på problem med att starta FastAPI-servern, kontrollera följande:

1. Säkerställ att du startar servern från projektroten:
   ```bash
   cd crypto-bot-dashboard-nexus
   python -m backend.fastapi_app
   ```

2. Kontrollera att alla beroenden är installerade:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Verifiera att Python-sökvägen inkluderar projektroten:
   ```python
   import sys
   print(sys.path)
   ```

4. Om du fortfarande har problem, kan du behöva lägga till projektroten manuellt:
   ```python
   import sys
   sys.path.append('/sökväg/till/crypto-bot-dashboard-nexus')
   ```

## Testning

Kör tester för att verifiera att allt fungerar som det ska:

```bash
# Windows PowerShell
cd backend
python -m pytest tests/test_fastapi_positions.py -v
```