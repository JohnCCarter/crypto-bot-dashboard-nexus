# ADR-002: Database Persistence Layer

## Status
✅ **ACCEPTED** – 2024-06-25

## Context
In-memory state in `bot_service` and `risk_manager` causes loss of information on restart.  The project now requires:

1. Thread-safe, durable storage of Bot status (running, cycles, error, uptime)
2. Persistent RiskManager snapshots (PnL, open positions)
3. Unified local-dev & prod setup ⇒ Postgres dialect (Supabase in prod)

## Decision
Implement SQLAlchemy ORM models backed by PostgreSQL.

* **Local development:** `docker-compose.db.yml` spins up Postgres 15.
* **Staging / Production:** Existing Supabase Postgres instance.
* Single env var `DATABASE_URL` controls connection (e.g. `postgresql://user:pass@localhost:5432/tradingbot`).  Falls back to SQLite for unit tests.
* Alembic is used for migrations.

## Consequences
+ Durable state across restarts & containers
+ One dialect across all environments (no vendor lock-in)
− Extra operational surface (Postgres container, migrations)

## Implementation Plan
1. Add **docker-compose.db.yml** service `postgres`.
2. Create `backend/persistence/` with `__init__.py`, `models.py`, `utils.py`.
3. Add SQLAlchemy & psycopg2-binary to `backend/requirements.txt`.
4. Initialise Alembic (`alembic/`, `alembic.ini`) and generate `revision --autogenerate`.
5. Update `bot_service.ThreadSafeBotState` to load/save state via persistence utils.
6. Add mini-tests (`test_persistence.py`) marked `@pytest.mark.persistence`.
7. Extend CI workflow to start Postgres service.
8. Future: add `RiskManagerSnapshot` model & persistence hooks.