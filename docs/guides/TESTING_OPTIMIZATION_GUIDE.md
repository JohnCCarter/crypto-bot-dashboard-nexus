# 🚀 TESTING & OPTIMIZATION GUIDE

## 1. Teststruktur och kategorier

Projektet har 220+ tester uppdelade i:

- **Unit tests**: Isolerade funktions-/klass-tester (snabbast)
- **Mock tests**: API och tjänster testas med mockade beroenden
- **API tests**: Testar FastAPI-endpoints med TestClient
- **Integration tests**: Testar hela flöden och integration mot riktiga API:er
- **WebSocket tests**: Realtids- och anslutningstester
- **Performance/Edge/Negative tests**: Prestanda och felhantering
- **Snabba tester**: Märkta med `@pytest.mark.fast` (körs på sekunder)
- **Långsamma tester**: Märkta med `@pytest.mark.slow` (integration, e2e, prestanda)

## 2. Nya testkommandon och skript

### Nya scripts för enkel testkörning

- **Snabba tester:**
  ```bash
  python scripts/testing/run_fast_tests.py
  ```
- **Integrationstester:**
  ```bash
  python scripts/testing/run_integration_tests.py
  ```
- **Alla tester:**
  ```bash
  python scripts/testing/run_integration_tests.py all
  ```
- **Långsamma tester:**
  ```bash
  python scripts/testing/run_integration_tests.py slow
  ```

### Manuella kommandon med pytest-markeringar

- **Kör bara snabba tester:**
  ```bash
  pytest -n auto -m "fast"
  ```
- **Kör bara integrationstester:**
  ```bash
  pytest -n auto -m "integration"
  ```
- **Kombinera markeringar:**
  ```bash
  pytest -n auto -m "fast and not integration"
  ```
- **Kör senaste failade tester:**
  ```bash
  pytest --last-failed
  ```

### Exempel på pytest-markeringar i kod

```python
import pytest

@pytest.mark.fast
@pytest.mark.api
def test_get_orders_success(...):
    ...

@pytest.mark.integration
def test_real_api_integration(...):
    ...
```

## 3. Prestandaoptimeringar

- **Parallellisering:** Alla scripts använder `-n auto` och kör tester på alla CPU-kärnor.
- **Miljövariabler** för snabbare testning:
  - `FASTAPI_DISABLE_WEBSOCKETS=true`
  - `FASTAPI_DISABLE_GLOBAL_NONCE_MANAGER=true`
  - `FASTAPI_DEV_MODE=true`
- **Fixtures** i `conftest.py` mockar tunga tjänster och återanvänder app-instans
- **pytest.ini** har nya markers: `unit`, `mock`, `api`, `integration`, `e2e`, `fast`, `slow`
- **Test-runner-skript** kör tester i optimal ordning och minimerar flaskhalsar

## 4. Rekommenderad arbetsordning

1. **Snabba tester först** (unit, indicators, strategies)
2. **Mock-tester** (config, positions, portfolio)
3. **API-tester** (bot control, risk management)
4. **Långsamma tester sist** (integration, websocket)

## 5. Återställning och säkerhet

- Alla optimeringar är bakåtkompatibla
- Inga produktionsberoenden påverkas
- Alla ändringar är versionshanterade och återställningsbara

## 6. CI/CD och automatiska tester

- **Alla tester körs automatiskt i CI/CD** (t.ex. GitHub Actions) vid varje push/PR.
- **Parallellisering** används även i CI för snabbare feedback.
- **Felrapportering:** Misslyckade tester och varningar syns direkt i PR/commit.
- **Rekommendation:** Kör alltid snabba tester lokalt innan push, och kontrollera CI-status efter varje push.

## 7. Felsökning och tolkning av pytest-resultat

- **Kör alltid unit- och mock-tester först** för snabb feedback.
- **Om fel:**
  - Isolera till enskild testfil och kör igen:
    ```bash
    pytest backend/tests/test_fastapi_orders.py
    ```
  - Kör med `-s` för att se print/logg:
    ```bash
    pytest -s backend/tests/test_fastapi_orders.py
    ```
  - Använd `--maxfail=1` för att stoppa vid första fel:
    ```bash
    pytest --maxfail=1
    ```
- **Vanliga feltyper:**
  - `AssertionError`: Förväntat värde matchar inte
  - `TypeError`, `KeyError`: Fel i mock eller API-respons
  - `ConnectionError`: Backend-servern kör inte (integrationstester)
- **Tips:**
  - Kontrollera miljövariabler och mock-fixtures
  - Dokumentera alla kända problem och TODOs i testkoden
  - Använd pytest-markers (`skip`, `xfail`) för att tydliggöra status

## 8. Senaste teststatus (2024-07-07)

### ✅ Gröna tester
- Unit-tester (indicators, strategies): 100% passerar
- Mockade API-tester (config, positions): 100% passerar (2 skipped, kända begränsningar)

### ⚠️ Delvis gröna tester
- API-tester (bot control): 2 fail (status: 'running' istället för 'stopped')
- WebSocket-tester: 11/14 passerar, 1 xfail (förväntat), 1 error (NameError), 1 fail (TypeError)

### ❌ Kända problem
- NameError i test_websocket_routes_exist (import av app i fel scope)
- TypeError i test_user_data_callbacks (callback är None)
- Bot-status-fel i API-tester (status: 'running' istället för 'stopped')
- 2 positions-tester skipped (mock-begränsning)
- 1 WebSocket-test xfail (förväntat, TODO)

## 9. Rekommenderad åtgärdslista

1. Fixa NameError i test_websocket_routes_exist (importera app i rätt scope)
2. Fixa TypeError i test_user_data_callbacks (mocka callback korrekt)
3. Felsök och åtgärda bot-status-fel i API-tester (mocka/ställ in bot-status rätt)
4. Dokumentera kvarvarande skipped/xfail-tester med tydliga TODO-kommentarer
5. Fortsätt köra snabba tester först, långsamma sist

---

*Senast uppdaterad: 2025-07-09 av AI-partnern Codex* 