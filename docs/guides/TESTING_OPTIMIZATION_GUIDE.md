# 🚀 TESTING & OPTIMIZATION GUIDE

## 1. Teststruktur och kategorier

Projektet har 220+ tester uppdelade i:

- **Unit tests**: Isolerade funktions-/klass-tester (snabbast)
- **Mock tests**: API och tjänster testas med mockade beroenden
- **API tests**: Testar FastAPI-endpoints med TestClient
- **Integration tests**: Testar hela flöden och integration mot riktiga API:er
- **WebSocket tests**: Realtids- och anslutningstester
- **Performance/Edge/Negative tests**: Prestanda och felhantering

## 2. Nya testkommandon och skript

### Snabb testkörning
```bash
python scripts/testing/run_tests_fast.py --fast-only      # Endast snabba tester
python scripts/testing/run_tests_fast.py --mock-only      # Endast mock-tester
python scripts/testing/run_tests_fast.py --api-only       # Endast API-tester
python scripts/testing/run_tests_fast.py --slow-only      # Endast långsamma tester
```

### CI-optimerad körning
```bash
python scripts/testing/run_tests_ci.py --all              # Kör alla tester i optimal ordning
python scripts/testing/run_tests_ci.py --unit-only        # Endast unit-tester
python scripts/testing/run_tests_ci.py --coverage         # Coverage-rapport
```

### Manuella kommandon
```bash
python -m pytest backend/tests/test_indicators.py backend/tests/test_strategies.py -v
python -m pytest backend/tests/test_fastapi_config.py backend/tests/test_fastapi_positions.py -v
python -m pytest backend/tests/test_fastapi_websocket.py -v
```

## 3. Prestandaoptimeringar

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

## 6. Vidare förbättringar

- Parallell testning kan införas med pytest-xdist
- Ytterligare optimering möjlig genom att isolera fler tunga beroenden

## 7. Senaste teststatus (2024-07-07)

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

## 8. Rekommenderad åtgärdslista

1. Fixa NameError i test_websocket_routes_exist (importera app i rätt scope)
2. Fixa TypeError i test_user_data_callbacks (mocka callback korrekt)
3. Felsök och åtgärda bot-status-fel i API-tester (mocka/ställ in bot-status rätt)
4. Dokumentera kvarvarande skipped/xfail-tester med tydliga TODO-kommentarer
5. Fortsätt köra snabba tester först, långsamma sist

## 9. Felsökningsrutin

- Kör alltid unit- och mock-tester först
- Om fel: isolera till enskild testfil och kör igen
- Kontrollera miljövariabler och mock-fixtures
- Dokumentera alla kända problem och TODOs i testkoden
- Använd pytest-markers (skip, xfail) för att tydliggöra status

---

*Senast uppdaterad: 2024-07-07 av AI-partnern Codex* 