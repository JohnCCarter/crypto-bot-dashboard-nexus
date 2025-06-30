# 🖥️ Server Management Guide - Crypto Trading Bot

**Syfte:** Denna guide hjälper dig att hantera server-processer på ett kontrollerat sätt för att undvika att många processer startas i bakgrunden.

---

## 🚀 Starta Servrar

### Rekommenderad metod (PowerShell)

```powershell
# Starta backend-server
cd backend
python -m flask run --host=0.0.0.0 --port=5000

# I ett nytt terminalfönster, starta frontend-server
cd <projektrot>
npm run dev
```

### Alternativ för utveckling (med script)

Använd de fördefinierade skripten i `scripts/deployment/`:

```powershell
# Windows
.\scripts\deployment\start-servers.ps1

# Linux/Mac
./scripts/deployment/start-servers.sh
```

---

## 🛑 Stoppa Servrar

### Manuell metod (PowerShell)

```powershell
# Hitta och stoppa Python-processer (backend)
Get-Process | Where-Object { $_.ProcessName -like '*python*' } | Stop-Process -Force

# Hitta och stoppa Node-processer (frontend)
Get-Process | Where-Object { $_.ProcessName -like '*node*' } | Stop-Process -Force
```

### Kontrollera aktiva processer

```powershell
# Visa alla relevanta processer
Get-Process | Where-Object { $_.ProcessName -like '*python*' -or $_.ProcessName -like '*node*' } | Select-Object ProcessName, Id, CPU, WorkingSet
```

---

## ⚠️ Vanliga Problem

### Problem: Många processer i bakgrunden

**Symptom:** Systemet blir långsamt, många Python/Node/PowerShell-processer körs.

**Lösning:**
1. Stoppa alla processer med kommandot ovan
2. Starta om servrarna manuellt i separata terminalfönster
3. Undvik att starta servrar i bakgrunden med `&` eller liknande

### Problem: Port redan upptagen

**Symptom:** Felmeddelande om att port 5000 eller 8081 redan används.

**Lösning:**
```powershell
# Hitta process som använder port 5000 (backend)
netstat -ano | findstr :5000

# Hitta process som använder port 8081 (frontend)
netstat -ano | findstr :8081

# Stoppa process med specifikt PID
Stop-Process -Id <PID> -Force
```

### Problem: Servern svarar inte

**Symptom:** API-anrop misslyckas med "Failed to fetch" eller timeout.

**Lösning:**
1. Kontrollera att servrarna körs:
   ```powershell
   # Testa backend
   Invoke-RestMethod -Uri "http://localhost:5000/api/status" -Method Get
   
   # Testa frontend
   Invoke-WebRequest -Uri "http://localhost:8081" -Method Get
   ```
2. Om servrarna inte svarar, starta om dem enligt instruktionerna ovan

---

## 🔄 Utvecklingsflöde

För att undvika problem med processer, följ detta arbetsflöde:

1. **Starta servrar separat** i olika terminalfönster
2. **Övervaka loggarna** i varje fönster för att upptäcka fel
3. **Stoppa servrar ordentligt** när du är klar (Ctrl+C i respektive fönster)
4. **Kontrollera regelbundet** för kvarvarande processer

---

## 📋 Checklista för Serverhantering

- [ ] Starta backend-server i ett dedikerat terminalfönster
- [ ] Starta frontend-server i ett annat terminalfönster
- [ ] Kontrollera att båda servrarna svarar på förfrågningar
- [ ] Avsluta servrarna ordentligt med Ctrl+C när du är klar
- [ ] Kontrollera för kvarvarande processer och stoppa dem vid behov

---

**💡 Tips:** Använd alltid separata terminalfönster för backend och frontend för bästa överblick och kontroll. 