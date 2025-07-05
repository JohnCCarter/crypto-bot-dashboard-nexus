# Guide för migrering från backend/venv till ./venv

Detta dokument beskriver processen för att migrera från den tidigare strukturen med virtuell miljö i backend-mappen (`backend/venv`) till den nya standardiserade strukturen med virtuell miljö i rotmappen (`./venv`).

## Bakgrund

Tidigare användes en virtuell miljö i `backend/venv`, särskilt på jobbdatorn. För att standardisera utvecklingsmiljön mellan jobb- och hemdatorn har vi beslutat att använda en virtuell miljö i projektets rotmapp (`./venv`) istället.

## Fördelar med ./venv

1. **Absoluta importsökvägar fungerar korrekt** - Koden använder konsekvent absoluta imports som `from backend.routes import x` vilket kräver att Python körs från rotmappen.
2. **SQLite-databasfiler** - Databashanteringen använder absoluta sökvägar till SQLite-databasen baserat på projektets rot.
3. **Moderna Python-konventioner** - Det är praxis i moderna Python-projekt att ha den virtuella miljön i rotmappen.
4. **Konsekvent med start-dev.py** - Vårt utvecklingsskript är konfigurerat för att använda `./venv`.
5. **Importproblem löses** - Många importfel undviks när Python körs från rotmappen.
6. **Bättre testintegrering** - Pytest och andra verktyg fungerar bättre när de körs från rotmappen.

## Migreringssteg

### 1. Skapa backup av nuvarande virtuell miljö

```bash
# För PowerShell
mv backend/venv backend/venv_backup

# För Bash
mv backend/venv backend/venv_backup
```

### 2. Skapa ny virtuell miljö i rotmappen

```bash
# För PowerShell
python -m venv venv

# För Bash
python -m venv venv
```

### 3. Aktivera den nya miljön

**PowerShell:**
```powershell
.\venv\Scripts\Activate.ps1
```

**Bash:**
```bash
source venv/Scripts/activate
```

### 4. Installera alla paket

```bash
pip install -r backend/requirements.txt
```

### 5. Uppdatera pip till senaste version

```bash
pip install --upgrade pip
```

### 6. Installera eventuella saknade paket

```bash
pip install psycopg2-binary
```

### 7. Verifiera installationen

**PowerShell:**
```powershell
pip list | findstr "bitfinex ccxt fastapi"
```

**Bash:**
```bash
pip list | grep "bitfinex\|ccxt\|fastapi"
```

## Uppdatera skript

Följande skript behöver uppdateras för att använda den nya virtuella miljön:

1. `scripts/deployment/start-servers.sh`
2. `scripts/deployment/start-dev.sh`
3. `scripts/testing/run_backend_integration_test.sh`

### Exempel på uppdatering

Ändra från:
```bash
source backend/venv/Scripts/activate
```

Till:
```bash
source venv/Scripts/activate
```

## Felsökning

Om du stöter på problem efter migreringen, kontrollera följande:

1. **Python-sökväg**: Kör `python -c "import sys; print(sys.executable)"` för att verifiera att du använder Python från den virtuella miljön.
2. **Importfel**: Om du får importfel som `ModuleNotFoundError: No module named 'backend'`, säkerställ att du kör Python från projektets rotmappen.
3. **Databasfel**: Om du får databasfel, kontrollera att SQLite-databasfilerna använder absoluta sökvägar baserat på projektets rot.

## Återställning

Om du behöver återställa till den tidigare strukturen:

```bash
# Ta bort den nya virtuella miljön
rm -rf venv

# Återställ från backup
mv backend/venv_backup backend/venv
```

## Kodexempel för att detektera och hantera virtuell miljö

Här är ett exempel på hur man kan detektera och hantera virtuell miljö i ett Python-skript:

```python
import os
import sys
from pathlib import Path

def is_venv_active():
    """Kontrollerar om en virtuell miljö är aktiverad."""
    return hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)

def get_venv_path():
    """Returnerar sökvägen till den virtuella miljön."""
    if is_venv_active():
        return sys.prefix
    return None

def activate_venv(project_root):
    """Aktiverar rätt virtuell miljö baserat på tillgänglighet."""
    # Kontrollera om ./venv finns
    root_venv = Path(project_root) / "venv"
    # Kontrollera om backend/venv finns
    backend_venv = Path(project_root) / "backend" / "venv"
    
    if root_venv.exists():
        print(f"Använder virtuell miljö i rotmappen: {root_venv}")
        # Returnera aktiveringskommandot
        if os.name == 'nt':  # Windows
            return str(root_venv / "Scripts" / "activate")
        return f"source {root_venv}/bin/activate"
    elif backend_venv.exists():
        print(f"Använder virtuell miljö i backend-mappen: {backend_venv}")
        # Returnera aktiveringskommandot
        if os.name == 'nt':  # Windows
            return str(backend_venv / "Scripts" / "activate")
        return f"source {backend_venv}/bin/activate"
    else:
        print("Ingen virtuell miljö hittades. Skapar en ny i rotmappen.")
        # Skapa ny virtuell miljö i rotmappen
        import subprocess
        subprocess.run([sys.executable, "-m", "venv", str(root_venv)])
        # Returnera aktiveringskommandot
        if os.name == 'nt':  # Windows
            return str(root_venv / "Scripts" / "activate")
        return f"source {root_venv}/bin/activate"

# Exempel på användning
if __name__ == "__main__":
    project_root = os.path.abspath(os.path.dirname(__file__))
    
    if is_venv_active():
        print(f"Virtuell miljö är redan aktiverad: {get_venv_path()}")
    else:
        activate_cmd = activate_venv(project_root)
        print(f"Aktivera virtuell miljö med: {activate_cmd}")
```

## Vanliga problem och lösningar

### Problem: Importfel för backend-moduler

**Problem**: `ModuleNotFoundError: No module named 'backend'`

**Lösning**: Säkerställ att Python körs från projektets rotmapp:

```bash
cd /sökväg/till/crypto-bot-dashboard-nexus-1
python -m backend.app  # Korrekt sätt att köra
```

### Problem: SQLite-databasfel

**Problem**: `sqlite3.OperationalError: unable to open database file`

**Lösning**: Säkerställ att Python körs från projektets rotmapp så att SQLite-databasen kan hittas med absoluta sökvägar.

### Problem: Aktivering av virtuell miljö misslyckas i PowerShell

**Problem**: `File cannot be loaded because running scripts is disabled on this system`

**Lösning**:

1. Öppna PowerShell som administratör
2. Kör: `Set-ExecutionPolicy RemoteSigned`
3. Svara "Y" för att bekräfta
4. Försök aktivera miljön igen: `.\venv\Scripts\Activate.ps1`

## Sammanfattning

Genom att migrera från `backend/venv` till `./venv` i rotmappen följer vi moderna Python-konventioner och löser många importproblem. Detta ger en mer konsekvent utvecklingsupplevelse på alla datorer och gör det enklare att köra tester och utvecklingsservrar.

För mer information om miljökonfiguration, se [ENVIRONMENT_SETUP_GUIDE.md](./ENVIRONMENT_SETUP_GUIDE.md).
