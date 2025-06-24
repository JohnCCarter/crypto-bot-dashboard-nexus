# 🗄️ Supabase Database Setup Guide

## ✅ Steg 1: Skapa tabeller i Supabase Dashboard

1. **Öppna Supabase Dashboard**
   - Gå till https://supabase.com/dashboard  
   - Välj ditt projekt

2. **Öppna SQL Editor**
   - Klicka på "SQL Editor" i vänstermenyn
   - Klicka på "New query"

3. **Kör SQL Schema**
   - Kopiera **hela innehållet** från `backend/supabase_schema.sql`
   - Klistra in i SQL Editor
   - Klicka "Run" (eller Ctrl+Enter)

4. **Verifiera tabeller**
   - Gå till "Table Editor" 
   - Du ska se 7 nya tabeller:
     - `trades` 📊 
     - `positions` 🎯
     - `orders` 📈
     - `risk_metrics` ⚠️ (KRITISK!)
     - `alerts` 🚨
     - `balance_snapshots` 💰
     - `strategy_performance` 🎲

## ✅ Steg 2: Uppdatera .env-filen

Kontrollera att din `.env` fil innehåller:

```bash
SUPABASE_URL=https://din-projekt-ref.supabase.co
SUPABASE_SERVICE_KEY=eyJ...din_service_role_key
```

⚠️ **Viktigt**: Använd **service_role** key (inte anon key) för full databasåtkomst.

## ✅ Steg 3: Testa anslutningen

Kör detta kommando för att verifiera:

```bash
cd /workspace
source venv/bin/activate
python -c "
from backend.services.database_service import db_service
print('🔍 Testing database connection...')
health = db_service.health_check()
print(f'✅ Database health: {health}')

if health:
    stats = db_service.get_trading_stats()
    print(f'📊 Trading stats: {stats}')
else:
    print('❌ Database not ready - please create tables first')
"
```

## ✅ Steg 4: Testa funktionalitet

När tabellerna är skapade, testa grundläggande operationer:

```bash
python -c "
from backend.services.database_service import db_service
from backend.models.trading_models import AlertModel
from decimal import Decimal

# Test alert creation
alert = AlertModel(
    type='system',
    severity='low', 
    title='Database Setup Complete',
    message='Supabase integration is working!'
)

try:
    created = db_service.create_alert(alert)
    print(f'✅ Alert created: {created.title}')
    
    # Test alert retrieval
    alerts = db_service.get_unacknowledged_alerts()
    print(f'📨 Unacknowledged alerts: {len(alerts)}')
    
except Exception as e:
    print(f'❌ Error: {e}')
"
```

## 🔄 Steg 5: Uppdatera befintliga services

Nästa steg är att uppdatera `risk_manager.py` och andra services för att använda databaslagring istället för in-memory state.

## 🚨 Kritiska fördelar efter setup:

✅ **Inga mer dataförluster** vid server-restart  
✅ **Persistent daily P&L tracking** - förhindrar överhandel  
✅ **Complete audit trail** av alla trades  
✅ **Real-time risk management** med databas-backed metrics  
✅ **Production-ready** persistens

## ❗ Troubleshooting

### Problem: "relation does not exist"
**Lösning**: Tabellerna är inte skapade än. Kör SQL-schemat i Supabase Dashboard.

### Problem: "Authentication failed"  
**Lösning**: Kontrollera att du använder service_role key (inte anon key).

### Problem: "Permission denied"
**Lösning**: Service_role key krävs för tabellskapande. Anon key räcker inte.

---

🎯 **När denna setup är klar har vi löst det kritiska in-memory state problemet!**