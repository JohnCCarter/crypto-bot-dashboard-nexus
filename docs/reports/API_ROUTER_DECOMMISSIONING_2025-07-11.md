# 🗑️ API Router Decommissioning – 2025-07-11

## Syfte
Avlusta och slutgiltigt ta bort de gamla API-filerna `balances.py`, `backtest.py`, `bot_control.py` efter fullständig FastAPI-migration och verifierad borttagning av alla beroenden.

## Åtgärder
- Alla imports och router-registreringar för dessa moduler har tagits bort i applikationskod och tester.
- Testfiler som explicit testade dessa routers har markerats som `skip` för spårbarhet.
- Alla tester passerar, inga ImportError eller regressions.
- Filerna är säkerhetskopierade till `.codex_backups/YYYY-MM-DD/` och därefter borttagna från kodbasen.

## Resultat
- Kodbasen är nu fri från död kod och gamla API-beroenden.
- FastAPI-backend är ren och stabil.
- Allt är dokumenterat och reversibelt via backup.

## Nästa steg
- Fortsätt med övrig kodrensning, förbättringar eller dokumentationsuppdateringar enligt todo-listan. 