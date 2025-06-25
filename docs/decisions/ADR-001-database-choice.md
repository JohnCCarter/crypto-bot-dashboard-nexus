# ADR-001: Database Architecture Decision

## Status
✅ **ACCEPTED** - 2024-06-25

## Context
Critical production fixes require persistent state management for:
- RiskManager daily PnL tracking
- Bot service state persistence  
- Order history and position tracking

Current system uses in-memory state which causes data loss on restart.

## Decision
**PostgreSQL via SQLAlchemy ORM + Alembic migrations**

**Rationale:**
- Supabase production instance IS PostgreSQL
- Local development uses PostgreSQL for consistency
- SQLAlchemy provides ORM abstraction
- Alembic handles schema migrations safely

## Consequences
**Positive:**
- State persists across service restarts
- Transaction safety and ACID compliance
- Scalable for multi-instance deployment
- Industry standard tooling

**Negative:**
- Additional complexity vs in-memory
- Database setup required for development
- Migration management overhead

## Implementation Plan
1. Setup local PostgreSQL container
2. Create SQLAlchemy models for critical entities
3. Migrate RiskManager to persistent storage
4. Update bot_service for database state
5. Create Alembic migration scripts