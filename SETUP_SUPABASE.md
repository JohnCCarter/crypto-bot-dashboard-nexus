# 🗄️ Supabase Setup Guide (Fresh Start)

## ✅ Steg 1: Kör SQL-schema i Supabase

1. **Öppna Supabase Dashboard**
   - Gå till https://supabase.com/dashboard
   - Välj ditt projekt

2. **Öppna SQL Editor**
   - Klicka på "SQL Editor" i vänstermenyn
   - Klicka på "New query"

3. **Kör SQL-schemat**
   - Kopiera **hela innehållet** från `backend/supabase_simple_schema.sql`
   - Klistra in i SQL Editor
   - Klicka "Run" (eller Ctrl+Enter)

4. **Verifiera resultat**
   - Du ska se: `"All tables created successfully!"`
   - Gå till "Table Editor" - du ska se 5 tabeller:
     - `trades` 📊
     - `positions` 🎯  
     - `risk_metrics` ⚠️
     - `alerts` 🚨
     - `orders` 📈

## ✅ Steg 2: Testa integration

Efter att tabellerna skapats, kör:

```bash
source venv/bin/activate
python backend/simple_database_test.py
```

**Du ska se:**
```
🎉 ALL TESTS PASSED!
✅ Supabase integration working perfectly!
```

## ✅ Steg 3: Integrera med befintlig kod

Efter att testerna går igenom kan du:

1. **Uppdatera befintliga services** att använda den nya databasen
2. **Migrera från in-memory** till persistent storage
3. **Köra live trading** med data-persistens

## 🚨 Troubleshooting

**Om du får fel:**
- ✅ Kontrollera att .env innehåller rätt SUPABASE_URL och SUPABASE_SERVICE_KEY
- ✅ Kontrollera att alla SQL-kommandon kördes framgångsrikt
- ✅ Kör `python backend/simple_database_test.py` för att debugga

## 📊 Schema Summary

**Minimal men kraftfull struktur:**
- **trades**: All trading history med P&L
- **positions**: Aktiva positioner
- **risk_metrics**: Daglig risk tracking (KRITISK!)
- **alerts**: System notifications  
- **orders**: Order history

**💡 Denna setup löser problemet med in-memory state permanent!**