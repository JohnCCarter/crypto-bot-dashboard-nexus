# BACKTEST-API – ARKITEKTUR & INTEGRATION

## Översikt

Projektets backtest-funktionalitet är uppdelad i tre huvuddelar:

- **API-router (`backend/api/backtest.py`)**  
  Exponerar REST-endpoints för att köra backtests via FastAPI.
- **Backtestmotor (`backend/services/backtest.py`)**  
  Innehåller logik för simulering av strategier, kapitalhantering, risk och resultat.
- **Tester (`backend/tests/test_backtest.py`)**  
  Säkerställer att backtestmotorn fungerar korrekt med olika strategier och parametrar.

---

## Flöde

1. **Frontend** skickar POST till `/api/backtest/run` med strategi, data och parametrar.
2. **API-routern** konverterar request till DataFrame, väljer strategi-funktion och anropar backtestmotorn.
3. **Backtestmotorn** kör simuleringen och returnerar ett `BacktestResult`.
4. **API-routern** returnerar resultatet som API-respons till frontend.

---

## Viktiga principer och krav

- **Pydantic-modellen** (`BacktestRequest`) måste ha fälten:  
  `strategy`, `data`, `parameters`, `timeframe`, `start_date`, `end_date`.
- **Strategi-funktioner** måste returnera en instans av `TradeSignal` (eller lista av dessa).
- **API-routern** måste anropa motorn med rätt strategi-signatur och konvertera resultatet till API-format.
- **Backtestmotorn** måste strikt kontrollera typ och signatur på strategi-funktionen.

---

## Vanliga felkällor

- Felaktig användning av attribut på Pydantic-modellen.
- Strategi-funktioner som returnerar dict istället för `TradeSignal`.
- Typinkompatibilitet mellan API, strategi och motor.
- Tester som inte matchar den faktiska signaturen.

---

## Rekommenderad arbetsgång för vidareutveckling

1. **Korrigera Pydantic-modellen** så att alla fält finns och är rätt typade.
2. **Säkerställ att strategi-funktionerna returnerar rätt typ** och kan användas direkt av motorn.
3. **Uppdatera API-routern** så att den anropar motorn med rätt signatur och hanterar fel korrekt.
4. **Verifiera och utöka testerna** så att de täcker både lyckade och felaktiga anrop.

---

## Exempel på korrekt strategi-funktion

```python
from backend.strategies.sample_strategy import TradeSignal

def my_strategy(data: pd.DataFrame, params: dict) -> TradeSignal:
    # ... strategi-logik ...
    return TradeSignal(action="buy", confidence=1.0, position_size=1.0, metadata={})
```

---

Denna dokumentation kan användas som referens för vidare utveckling och felsökning av backtest-API:t. 