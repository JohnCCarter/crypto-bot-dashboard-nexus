# 🚀 Pålitlig Server Management Guide

## 📋 **Översikt**

Detta system säkerställer att backend och frontend alltid startar konsekvent utan port-konflikter eller zombie-processer.

## 🔧 **Huvudkomponenter**

### 1. Robust Server Manager
**Fil**: `scripts/server-manager.sh`

**Funktioner**:
- ✅ Automatisk port-rensning (5000, 8081)
- ✅ Process-spårning med PID-filer
- ✅ Hälsokontroller med timeout
- ✅ Färgad loggning för tydlighet
- ✅ Fehantering enligt Zero-Fault Troubleshooting

### 2. Bekväma Alias
**Fil**: `scripts/aliases.sh`

Ladda med: `source scripts/aliases.sh`

### 3. Port-konfiguration
- **Backend**: Port 5000 (Flask)
- **Frontend**: Port 8081 (Vite)
- **API Proxy**: /api → http://127.0.0.1:5000

## 🚀 **Användning**

### Grundkommandon
```bash
# Starta alla servrar (stoppar först automatiskt)
./scripts/server-manager.sh start

# Stoppa alla servrar
./scripts/server-manager.sh stop

# Restart alla servrar
./scripts/server-manager.sh restart

# Visa status och processer
./scripts/server-manager.sh status

# Hälsokontroller
./scripts/server-manager.sh health
```

### Med Alias (rekommenderat)
```bash
# Ladda alias först
source scripts/aliases.sh

# Använd enkla kommandon
bot-start     # Starta allt
bot-stop      # Stoppa allt
bot-restart   # Restart allt
bot-status    # Visa status
bot-health    # Hälsokontroller
```

## 🛠️ **Utvecklingsworkflow**

### Daglig användning
```bash
# 1. Ladda alias (en gång per session)
source scripts/aliases.sh

# 2. Starta utvecklingsmiljön
bot-start

# 3. Arbeta med koden...

# 4. Vid problem - restart
bot-restart

# 5. Slut av dagen
bot-stop
```

### Felsökning
```bash
# Visa vilka portar som är upptagna
bot-status

# Kontrollera hälsa
bot-health

# Visa live logs
bot-logs

# Force restart vid problem
bot-stop && sleep 5 && bot-start
```

## 🔧 **Teknisk Information**

### Process Management
- **PID-tracking**: `.server-manager.pid`
- **Auto-cleanup**: Zombie processer rensas automatiskt
- **Force-kill**: SIGKILL används vid behov

### Port Management
```python
# Port-kontroll (Python)
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('localhost', port))
sock.close()
# result == 0 betyder porten är upptagen
```

### Process Patterns
Server managern känner igen och hanterar:
- `flask.*port`
- `python.*flask.*port`
- `vite.*port`
- `npm.*dev.*port`

## 🏥 **Health Checks**

Automatiska kontroller av:
1. **Backend**: `GET http://localhost:5000/api/status`
2. **Frontend**: `GET http://localhost:8081`
3. **Timeout**: 5 sekunder per check

## 🔄 **Backup & Safety**

Följer projektets backup-regler:
- ✅ Backup före ändringar: `.codex_backups/YYYY-MM-DD/`
- ✅ Verifiering av backup-integritet
- ✅ Säker process-hantering

## 🚨 **Troubleshooting**

### Problem: Port 5000 fortfarande upptagen
```bash
# Visa vad som använder porten
lsof -i :5000

# Force kill specifikt
pkill -9 -f flask

# Eller använda server managern
bot-stop
```

### Problem: Frontend startar på fel port
```bash
# Kontrollera vite.config.ts
grep -n "port.*8081" vite.config.ts

# Om port saknas, lägg till:
# server: { port: 8081 }
```

### Problem: Zombie processer
```bash
# Server managern hanterar automatiskt
bot-stop  # Rensar allt

# Manuell kontroll
ps aux | grep -E "(flask|vite|npm)" | grep defunct
```

### Problem: API-anslutning
```bash
# Kontrollera proxy-inställning
grep -A5 "proxy" vite.config.ts

# Ska visa:
# proxy: {
#   '/api': 'http://127.0.0.1:5000'
# }
```

## 📊 **Systemarkitektur**

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │
│   (Vite)        │    │   (Flask)       │
│   Port: 8081    │◄───┤   Port: 5000    │
└─────────────────┘    └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   Dev Browser   │    │   Bitfinex API  │
│   localhost:8081│    │   WebSocket     │
└─────────────────┘    └─────────────────┘
```

## ✅ **Best Practices**

1. **Använd alltid server managern** - inte manuella kommandon
2. **Kör `bot-health`** efter ändringar
3. **Stoppa innan shutdown** - `bot-stop`
4. **Använd alias** för snabbare workflow
5. **Backup automatiskt** - följer projektets regler

## 📚 **Relaterade Filer**

- `scripts/server-manager.sh` - Huvudscript
- `scripts/aliases.sh` - Bekväma kommandon  
- `vite.config.ts` - Frontend port-konfiguration
- `backend/app.py` - Backend konfiguration
- `.env` - Miljövariabler (API nycklar)