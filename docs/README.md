# Documentation

This directory contains all project documentation.

## Directory Structure

- `decisions/` - Architecture Decision Records (ADRs) and major design decisions
- `development/` - Development roadmap and planning documents
- `guides/` - Step-by-step guides for various tasks
  - `environment/` - Environment setup guides
    - `NODE_TYPESCRIPT_SETUP.md` - Guide for Node.js and TypeScript configuration
    - `VENV_MIGRATION_GUIDE.md` - Guide for migrating from backend/venv to ./venv
  - `ENVIRONMENT_SETUP_GUIDE.md` - Overall environment setup guide
  - `BITFINEX_API_INTEGRATION_GUIDE.md` - Guide for Bitfinex API integration
  - `WEBSOCKET_IMPLEMENTATION_GUIDE.md` - Guide for WebSocket implementation
  - `DEBUG_GUIDE.md` - Debugging guide
  - `QUICK_DEPLOYMENT_GUIDE.md` - Quick deployment guide
  - `SERVER_MANAGEMENT_GUIDE.md` - Server management guide
- `reports/` - Status reports and implementation summaries
- `solutions/` - Solution documents for specific problems

## Key Documents

### Environment Setup

- [Environment Setup Guide](./guides/ENVIRONMENT_SETUP_GUIDE.md) - Main guide for setting up the development environment
- [Node.js and TypeScript Setup](./guides/environment/NODE_TYPESCRIPT_SETUP.md) - Detailed guide for Node.js and TypeScript configuration
- [Virtual Environment Migration Guide](./guides/environment/VENV_MIGRATION_GUIDE.md) - Guide for migrating from backend/venv to ./venv

### Development

- [Development Roadmap](./development/DEVELOPMENT_ROADMAP.md) - Overall project roadmap and milestones
- [Debugging Guide](./guides/DEBUG_GUIDE.md) - Guide for debugging common issues

### API Integration

- [Bitfinex API Integration Guide](./guides/BITFINEX_API_INTEGRATION_GUIDE.md) - Guide for Bitfinex API integration
- [WebSocket Implementation Guide](./guides/WEBSOCKET_IMPLEMENTATION_GUIDE.md) - Guide for WebSocket implementation

### Deployment

- [Quick Deployment Guide](./guides/QUICK_DEPLOYMENT_GUIDE.md) - Quick guide for deploying the application
- [Server Management Guide](./guides/SERVER_MANAGEMENT_GUIDE.md) - Guide for managing the server

## Architecture Decisions

- [ADR-001: Database Choice](./decisions/ADR-001-database-choice.md) - Decision record for database choice
- [ADR-002: DB Persistence](./decisions/ADR-002-db-persistence.md) - Decision record for database persistence strategy

## Key Guides

### Environment and Configuration
- [Environment Setup Guide](guides/ENVIRONMENT_SETUP_GUIDE.md) - Main guide for setting up the development environment
- [Node.js and TypeScript Setup](guides/environment/NODE_TYPESCRIPT_SETUP.md) - Detailed guide for Node.js and TypeScript configuration
- [Virtual Environment Migration Guide](guides/environment/VENV_MIGRATION_GUIDE.md) - Guide for migrating from backend/venv to ./venv
- [Felsökningsguide](guides/DEBUG_GUIDE.md) - Felsökningsguide
- [Snabb deploymentguide](guides/QUICK_DEPLOYMENT_GUIDE.md) - Snabbguide för driftsättning

### API and Integration
- [Bitfinex API-integrationsguide](guides/BITFINEX_API_INTEGRATION_GUIDE.md) - Guide för Bitfinex API-integration
- [Bitfinex API-uppdateringsplan](guides/BITFINEX_API_INTEGRATION_UPDATE.md)
- [Bitfinex API-uppdateringschecklista](guides/BITFINEX_API_UPDATE_CHECKLIST.md)
- [Bitfinex API-uppdateringsstatus](guides/BITFINEX_API_UPDATE_CI_STATUS.md)

### WebSocket
- [WebSocket-funktioner översikt](guides/WEBSOCKET_FUNKTIONER_OVERSIKT.md) - Översikt över WebSocket-funktioner
- [WebSocket vs REST-analys](guides/WEBSOCKET_VS_REST_ANALYSIS.md) - Jämförelse mellan WebSocket och REST
- [WebSocket-användardata implementationsplan](guides/WEBSOCKET_USER_DATA_IMPLEMENTATION_PLAN.md) - Plan för implementering av användardata via WebSocket

### Serverhantering
- [Serverhanteringsguide](guides/SERVER_MANAGEMENT_GUIDE.md) - Guide för serverhantering

## Key Reports

- [Bitfinex API-biblioteksintegration slutförd](reports/BITFINEX_API_LIBRARY_INTEGRATION_COMPLETE.md)
- [Bitfinex WebSocket-förbättringar slutförda](reports/BITFINEX_WEBSOCKET_ENHANCEMENT_COMPLETE.md)
- [Användardata-strömmar implementation slutförd](reports/USER_DATA_STREAMS_IMPLEMENTATION_COMPLETE.md)
- [Förbättrad loggning sammanfattning](reports/ENHANCED_LOGGING_SUMMARY.md)
- [Hybridimplementation slutförd](reports/HYBRID_IMPLEMENTATION_COMPLETE.md)

## Key Decisions

- [ADR-001-database-choice.md](decisions/ADR-001-database-choice.md) - Beslut om val av databas
- [ADR-002-db-persistence.md](decisions/ADR-002-db-persistence.md) - Beslut om databaslagring

## Key Solutions

- [Logganalys lösning](solutions/LOG_ANALYSIS_SOLUTION.md)
- [Pappershandel lösning sammanfattning](solutions/PAPER_TRADING_SOLUTION_SUMMARY.md)
- [Serverstartlösning](solutions/SERVER_START_SOLUTION.md)
- [Logg 7 lösning sammanfattning](solutions/LOG_7_SOLUTION_SUMMARY.md) 