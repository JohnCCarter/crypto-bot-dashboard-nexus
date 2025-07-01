# FastAPI Migration Plan

Detta dokument beskriver planen för att migrera API:et från Flask till FastAPI.

## Målsättning

Målet är att migrera hela backend-API:et från Flask till FastAPI för att dra nytta av:

1. **Förbättrad prestanda**: FastAPI är en av de snabbaste Python-webbramverken och kan hantera fler förfrågningar per sekund än Flask.
2. **Asynkron kod**: FastAPI stöder `async`/`await` syntax, vilket möjliggör icke-blockerande IO-operationer.
3. **Automatisk dokumentation**: FastAPI genererar automatiskt OpenAPI-dokumentation och Swagger UI.
4. **Robustare validering**: FastAPI använder Pydantic för datavalidering och konvertering.
5. **Dependency Injection**: FastAPI har ett inbyggt system för dependency injection.

## Stegvis migrationsplan

För att minimera risken och säkerställa kontinuerlig funktionalitet kommer migreringen att ske stegvis:

### Fas 1: Förberedelse (KLAR)

- [x] Skapa en ny FastAPI-applikation parallellt med den befintliga Flask-applikationen
- [x] Konfigurera CORS, felhantering och grundläggande middleware
- [x] Skapa en struktur för API-endpointsen med separata filer för varje resursaktion

### Fas 2: Grundläggande implementation (KLAR)

- [x] Skapa Pydantic-modeller för alla resurser
- [x] Implementera status-endpoints (hälsokontroll och systeminformation)
- [x] Testa den grundläggande implementationen

### Fas 3: Stegvis migration av endpoints (DELVIS KLAR)

- [x] Migrera balances-endpoints (`/api/balances` och `/api/balances/{currency}`)
- [x] Migrera orders-endpoints (`/api/orders`, `/api/orders/{order_id}`)
- [x] Migrera backtest-endpoints (`/api/backtest/strategies`, `/api/backtest/run`, `/api/backtest/{id}`)
- [x] Migrera config-endpoints (`/api/config`, `/api/config/strategies`, etc.)
- [x] Migrera positions-endpoints (`/api/positions`)
- [x] Migrera bot-control-endpoints (`/api/bot-status`, `/api/bot/start`, `/api/bot/stop`)
- [ ] Migrera market-data-endpoints (`/api/market-data`)
- [ ] Migrera orderbook-endpoints (`/api/orderbook`)
- [ ] Migrera monitoring-endpoints (`/api/monitoring`)

### Fas 4: Servicelager och asynkron konvertering (PÅBÖRJAD)

- [x] Skapa asynkrona versioner av service-funktioner
- [x] Implementera dependency injection för servicelager (grundläggande struktur klar)
- [ ] Optimera dataflöde för asynkrona operationer
- [ ] Konvertera fler service-funktioner till asynkrona

### Fas 5: Integration och testning

- [ ] Skapa omfattande tester för FastAPI-endpoints
- [ ] Verifiera att alla endpoints fungerar korrekt
- [ ] Testa prestanda och skalbarhet
- [ ] Implementera lösning för databasanslutningar med asynkrona sessioner

### Fas 6: Slutlig övergång

- [ ] Uppdatera frontend för att använda nya API-endpoints
- [ ] Genomför komplett testning end-to-end
- [ ] Växla över till FastAPI som primärt API
- [ ] Avveckla Flask-applikationen

## Parallell drift

Under migrationen kommer både Flask och FastAPI att köras parallellt:

- Flask API: Port 5000 (befintlig)
- FastAPI API: Port 8001 (ny)

Detta möjliggör stegvis testning och övergång.

## Tidslinje

Migreringen kommer att ske stegvis under kommande sprints:

1. **Fas 1 & 2**: Sprint 1 (KLAR)
2. **Fas 3**: Sprint 2-3 (PÅGÅENDE)
3. **Fas 4 & 5**: Sprint 4
4. **Fas 6**: Sprint 5

## Uppföljning och dokumentation

Framstegen i migrationen kommer att spåras i `docs/guides/FASTAPI_MIGRATION_STATUS.md`. Alla API-ändringar dokumenteras också där.

## Övriga överväganden

- **Bakåtkompatibilitet**: Alla endpoints kommer att behålla samma URL-struktur och svarsformat för att säkerställa bakåtkompatibilitet.
- **Prestanda**: Prestandamätningar kommer att göras för att säkerställa att FastAPI-implementationen är minst lika snabb som Flask-implementationen.
- **Testning**: Omfattande tester kommer att skrivas för alla nya endpoints för att säkerställa korrekt funktionalitet.
- **Dokumentation**: All API-dokumentation kommer att uppdateras för att reflektera de nya endpoints och funktionaliteten.

## Nuvarande status

- Fas 1 och 2 är helt slutförda.
- Fas 3 är delvis slutförd med migreringar av balances, orders, backtest, config, positions, och bot-control-endpoints.
- Fas 4 är påbörjad med implementation av grundläggande dependency injection struktur.
- FastAPI-servern körs på port 8001.
- Pydantic-modeller finns på plats för alla resurser som har migrerats hittills.

## Nästa steg

1. Fortsätt med Fas 3 genom att migrera återstående endpoints
2. Utveckla dependency injection-strukturen vidare
3. Konvertera fler service-funktioner till asynkrona
4. Börja skriva tester för de nya FastAPI-endpoints

## Uppföljning

Framstegen och statusen för migrationen kommer att uppdateras kontinuerligt i `docs/guides/FASTAPI_MIGRATION_STATUS.md`. 