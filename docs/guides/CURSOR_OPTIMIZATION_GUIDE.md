# Guide för Cursor/AI-assistent Optimering

Detta dokument beskriver hur du kan optimera indexeringen och resursanvändningen för Cursor/AI-assistenten, särskilt på hemdatorn.

## Optimera Indexeringen

### 1. Skapa en .cursorignore-fil

Lägg till en `.cursorignore`-fil i projektroten för att undvika indexering av onödiga filer:

```bash
# Skapa filen
touch .cursorignore  # Linux/Mac
# eller
New-Item -Path .cursorignore -ItemType File  # Windows PowerShell
```

### 2. Rekommenderat innehåll för .cursorignore

```
# Python artifacts
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/

# Virtual environments
venv/
*.egg-info/
build/
dist/

# Node modules and NPM/Yarn cache
node_modules/
.npm/
.yarn/
.pnp.*

# Local environment
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE specific files
.vscode/
.idea/
*.swp
*.swo
.DS_Store

# Build outputs
*.min.js
*.min.css
frontend/dist/
frontend/build/

# Large databases and logs
*.log
local.db
```

### 3. Genom Cursor-inställningarna

Om du föredrar att använda UI istället för filen:

1. Öppna Cursor-inställningar
2. Gå till "Indexing & Docs"
3. Klistra in samma mönster som ovan i relevanta fält

## Hantera PowerShell-processer

Cursor kan lämna flera PowerShell-processer öppna med `-noexit`-flaggan, vilket binder onödigt minne.

### Kontrollera aktiva processer

```powershell
# Visa alla PowerShell-processer
Get-Process -Name powershell

# Visa enbart de som kan vara relaterade till Cursor
Get-Process -Name powershell | Where-Object { $_.CommandLine -like "*-noexit*" -or $_.CommandLine -like "*Cursor*" }
```

### Avsluta onödiga processer

```powershell
# Avsluta alla PowerShell-processer med -noexit i kommandoraden
Get-Process -Name powershell | Where-Object { $_.CommandLine -like "*-noexit*" } | Stop-Process -Force

# Eller avsluta specifika processer med ID (ersätt med dina process-ID:er)
Stop-Process -Id 1234, 5678 -Force
```

## Ytterligare Optimeringar

### 1. Aktivera utvecklingsläge för FastAPI

För att minska CPU-användningen, använd utvecklingsläget via `fastapi_dev.py`:

```bash
python scripts/development/fastapi_dev.py --mode minimal --no-reload
```

### 2. Stäng av hot-reload när det inte behövs

Hot-reload är användbart vid aktiv utveckling men ökar CPU-användningen.

### 3. Arbeta i mindre sessioner

Dela upp arbetet i mindre konversationer med AI-assistenten för att reducera kontextfönstrets storlek:

1. Starta nya chattar när du byter fokusområde
2. Fokusera varje konversation på en specifik del av kodbasen

### 4. Rensa caches periodiskt

För att frigöra diskutrymme och potentiellt förbättra prestandan:

```bash
# Rensa Python-caches
find . -type d -name "__pycache__" -exec rm -rf {} +  # Linux/Mac
# eller
Get-ChildItem -Path . -Filter "__pycache__" -Recurse | Remove-Item -Force -Recurse  # Windows PowerShell
```

## Använda denna guide

1. Implementera .cursorignore-filen först
2. Starta om Cursor för att tillämpa indexeringsändringarna
3. Kontrollera och avsluta eventuella onödiga PowerShell-processer
4. Använd utvecklingsläget för FastAPI när du arbetar med backend

Dessa optimeringar bör göra AI-assistenten betydligt mer responsiv och minska resursanvändningen avsevärt. 