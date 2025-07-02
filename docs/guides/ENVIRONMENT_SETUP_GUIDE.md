# Miljöuppsättningsguide

Detta dokument beskriver hur du sätter upp en konsekvent utvecklingsmiljö för projektet på olika datorer (jobb och hemma).

## Viktigt om miljöskillnader

**OBS! Miljöskillnader mellan datorerna:**
- **Jobbdator**: 
  - Python 3.11.9
  - PowerShell
  - Windows
- **Hemdator**: 
  - Python 3.13.3 (planerar att nedgradera till 3.11.9)
  - Bash
  - Windows

Dessa skillnader kräver olika kommandon och aktiveringsmetoder. Denna guide innehåller instruktioner för båda miljöerna.

## Nuvarande miljö (jobbdator)

### Systemdetaljer
- **Python-version**: 3.11.9
- **Skal**: PowerShell
- **Virtuell miljö**: `venv` i projektets rotmapp
- **Operativsystem**: Windows

### Viktiga paket
- bitfinex-api-py 3.0.4
- ccxt 4.4.91
- fastapi 0.115.14
- uvicorn 0.35.0
- pytest 8.4.1
- pytest-asyncio 1.0.0

## Nuvarande miljö (hemdator)

### Systemdetaljer
- **Python-version**: 3.13.3 (planerar att nedgradera till 3.11.9)
- **Skal**: Bash
- **Virtuell miljö**: `venv` i projektets rotmapp
- **Operativsystem**: Windows

## Steg för att konfigurera miljön

### 1. Installera rätt Python-version
- **För jobbdatorn**: Python 3.11.9 - [Ladda ner](https://www.python.org/downloads/release/python-3119/)
- **För hemdatorn**: Nedgradera till Python 3.11.9 - [Ladda ner](https://www.python.org/downloads/release/python-3119/)
- Se till att markera "Add to PATH" under installationen

### 2. Klona projektet (om det inte redan är gjort)
```bash
git clone <repository-url>
cd crypto-bot-dashboard-nexus
```

### 3. Skapa en virtuell miljö

**Jobbdator (PowerShell):**
```powershell
python -m venv venv
```

**Hemdator (Bash):**
```bash
python -m venv venv
```

### 4. Aktivera den virtuella miljön

**Jobbdator (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
```

**Hemdator (Bash):**
```bash
source venv/Scripts/activate
```

### 5. Installera alla paket från requirements-filen

**Jobbdator (PowerShell):**
```powershell
pip install -r environment_requirements.txt
```

**Hemdator (Bash):**
```bash
pip install -r environment_requirements.txt
```

### 6. Verifiera installationen

**Jobbdator (PowerShell):**
```powershell
pip list | findstr "bitfinex ccxt fastapi"
```

**Hemdator (Bash):**
```bash
pip list | grep "bitfinex\|ccxt\|fastapi"
```

### 7. Testa att du kan importera nyckelpaket
```bash
python -c "import bfxapi; import ccxt; import fastapi; print('Alla paket laddades framgångsrikt!')"
```

## Skapa hjälpskript för enklare utveckling

För att underlätta utvecklingen mellan olika miljöer, skapa följande hjälpskript:

### start-dev.py (fungerar på båda miljöerna)
```python
#!/usr/bin/env python
import os
import sys
import subprocess
import platform

print("🚀 Startar utvecklingsmiljön...")

# Detektera om vi använder PowerShell eller Bash
is_powershell = "powershell" in os.environ.get("SHELL", "").lower() or platform.system() == "Windows"

# Aktivera virtuell miljö och starta servern
if is_powershell:
    print("📌 Använder PowerShell")
    subprocess.run("cd backend; python -m uvicorn fastapi_app:app --reload --port 8001", shell=True)
else:
    print("📌 Använder Bash")
    subprocess.run("cd backend && python -m uvicorn fastapi_app:app --reload --port 8001", shell=True)

print("✅ Server startad på port 8001")
```

Spara detta skript i projektets rot och kör det med:
```bash
python start-dev.py
```

## Felsökning

### Problem med bfxapi
Om du får fel vid import av bfxapi, prova att installera direkt från GitHub:

```bash
pip install git+https://github.com/bitfinexcom/bitfinex-api-py.git
```

### Aktivera virtuell miljö i PowerShell
Om du får fel när du försöker aktivera den virtuella miljön i PowerShell:

1. Öppna PowerShell som administratör
2. Kör: `Set-ExecutionPolicy RemoteSigned`
3. Svara "Y" för att bekräfta
4. Försök aktivera miljön igen: `.\venv\Scripts\Activate.ps1`

### Kontrollera Python-sökväg
För att verifiera vilken Python-installation som används:

```bash
python -c "import sys; print(sys.executable)"
```

Detta bör visa sökvägen till Python i den virtuella miljön.

## Köra tester

När miljön är korrekt konfigurerad kan du köra testerna:

**Jobbdator (PowerShell):**
```powershell
cd backend
python -m pytest tests/test_fastapi_websocket.py -v
```

**Hemdator (Bash):**
```bash
cd backend
python -m pytest tests/test_fastapi_websocket.py -v
```

## Uppdatera miljön

Om du gör ändringar i miljön på en dator och vill synkronisera med den andra:

1. Generera en ny requirements-fil:
   ```bash
   pip freeze > environment_requirements.txt
   ```

2. Kopiera filen till den andra datorn och installera:
   ```bash
   pip install -r environment_requirements.txt
   ```

## Snabbkommandon för daglig användning

### Jobbdator (PowerShell)

```powershell
# Aktivera miljö
function activate-env { .\venv\Scripts\Activate.ps1 }

# Starta utvecklingsserver
function start-dev { cd backend; python -m uvicorn fastapi_app:app --reload --port 8001 }

# Kör tester
function run-tests { cd backend; python -m pytest tests/ }
```

Lägg till dessa i din PowerShell-profil:
```powershell
notepad $PROFILE
```

### Hemdator (Bash)

Lägg till följande i din `.bashrc` eller `.bash_profile`:

```bash
# Aktivera miljö
alias activate-env='source venv/Scripts/activate'

# Starta utvecklingsserver
alias start-dev='cd backend && python -m uvicorn fastapi_app:app --reload --port 8001'

# Kör tester
alias run-tests='cd backend && python -m pytest tests/'
``` 