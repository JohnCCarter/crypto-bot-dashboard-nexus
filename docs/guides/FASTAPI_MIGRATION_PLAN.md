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

### Fas 3: Stegvis migration av endpoints (KLAR)

- [x] Migrera balances-endpoints (`/api/balances` och `/api/balances/{currency}`)
- [x] Migrera orders-endpoints (`/api/orders`, `/api/orders/{order_id}`)
- [x] Migrera backtest-endpoints (`/api/backtest/strategies`, `/api/backtest/run`, `/api/backtest/{id}`)
- [x] Migrera config-endpoints (`/api/config`, `/api/config/strategies`, etc.)
- [x] Migrera positions-endpoints (`/api/positions`)
- [x] Migrera bot-control-endpoints (`/api/bot-status`, `/api/bot/start`, `/api/bot/stop`)
- [x] Migrera market-data-endpoints (`/api/market-data`)
- [x] Migrera orderbook-endpoints (`/api/orderbook`)
- [x] Migrera monitoring-endpoints (`/api/monitoring`)

### Fas 4: Servicelager och asynkron konvertering (PÅGÅENDE)

- [x] Skapa asynkrona versioner av service-funktioner
- [x] Implementera dependency injection för servicelager (grundläggande struktur klar)
- [x] Utöka dependency injection-systemet med monitoring-komponenter
- [x] Implementera asynkron order_service med dependency injection
- [x] Implementera asynkron risk_manager med avancerade riskhanteringsfunktioner
- [x] Implementera asynkron portfolio_manager med strategi-integration
- [x] Integrera risk_manager och portfolio_manager i dependency injection-systemet
- [ ] Optimera dataflöde för asynkrona operationer
- [ ] Konvertera återstående service-funktioner till asynkrona

### Fas 5: Integration och testning

- [ ] Skapa omfattande tester för FastAPI-endpoints
- [ ] Implementera tester för asynkrona service-klasser
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
2. **Fas 3**: Sprint 2-3 (KLAR)
3. **Fas 4 & 5**: Sprint 4-5 (PÅGÅENDE)
4. **Fas 6**: Sprint 6

## Uppföljning och dokumentation

Framstegen i migrationen kommer att spåras i `docs/guides/FASTAPI_MIGRATION_STATUS.md`. Alla API-ändringar dokumenteras också där.

## Övriga överväganden

- **Bakåtkompatibilitet**: Alla endpoints kommer att behålla samma URL-struktur och svarsformat för att säkerställa bakåtkompatibilitet.
- **Prestanda**: Prestandamätningar kommer att göras för att säkerställa att FastAPI-implementationen är minst lika snabb som Flask-implementationen.
- **Testning**: Omfattande tester kommer att skrivas för alla nya endpoints för att säkerställa korrekt funktionalitet.
- **Dokumentation**: All API-dokumentation kommer att uppdateras för att reflektera de nya endpoints och funktionaliteten.

## Nuvarande status

- Fas 1 och 2 är helt slutförda.
- Fas 3 är helt slutförd med migreringar av alla planerade endpoints.
- Fas 4 är i full gång med betydande framsteg:
  - Vi har implementerat en fullständig asynkron version av order_service med dependency injection
  - Vi har integrerat asynkron order_service med FastAPI orders API
  - Vi har implementerat helt nya asynkrona risk_manager_async och portfolio_manager_async moduler
  - Vi har utökat dependency injection-systemet med stöd för risk- och portföljhantering
  - Vi använder singleton-mönster för kritiska serviceklasser för att optimera resursanvändning
- FastAPI-servern körs på port 8001 parallellt med Flask-servern på port 5000.
- Pydantic-modeller finns på plats för alla resurser som har migrerats hittills.
- Dokumentation för asynkrona implementationer har skapats i form av rapporter.

## Nästa steg

1. Skapa endpoints som använder de nya asynkrona risk- och portföljhanteringsklasserna
2. Fortsätta med Fas 4 genom att konvertera återstående service-funktioner till asynkrona
3. Optimera asynkron datahantering och implementera caching där lämpligt
4. Påbörja Fas 5 genom att skriva tester för de nya FastAPI-endpoints och asynkrona serviceklasserna

## Uppföljning

Framstegen och statusen för migrationen kommer att uppdateras kontinuerligt i `docs/guides/FASTAPI_MIGRATION_STATUS.md`. 