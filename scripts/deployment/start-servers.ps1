# 🚀 Crypto Trading Bot - Server Start Script (PowerShell)
# ===========================================================
# Detta skript startar både backend (FastAPI) och frontend (Vite) korrekt
# Kör från projektets rot: .\start-servers.ps1

param(
    [Parameter(Position=0)]
    [ValidateSet("backend", "frontend", "both")]
    [string]$Mode = "both"
)

# Aktivera strict mode
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host "🔧 Crypto Trading Bot - Startar servrar..." -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Kontrollera att vi är i projektets rot
if (-not (Test-Path "package.json") -or -not (Test-Path "backend")) {
    Write-Host "❌ FEL: Kör detta skript från projektets rot (crypto-bot-dashboard-nexus-1/)" -ForegroundColor Red
    Write-Host "📁 Nuvarande katalog: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

# Kontrollera Python virtual environment
if (-not (Test-Path "backend/venv")) {
    Write-Host "❌ FEL: Python virtual environment saknas i backend/venv" -ForegroundColor Red
    Write-Host "💡 Kör: cd backend; python -m venv venv; .\venv\Scripts\Activate.ps1; pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Kontrollera npm dependencies
if (-not (Test-Path "node_modules")) {
    Write-Host "❌ FEL: Node.js dependencies saknas" -ForegroundColor Red
    Write-Host "💡 Kör: npm install" -ForegroundColor Yellow
    exit 1
}

Write-Host "✅ Förkunskaper kontrollerade" -ForegroundColor Green

# Starta FastAPI-servern
Write-Host "🔄 Startar FastAPI backend..." -ForegroundColor Green
cd backend
& ../venv/Scripts/Activate.ps1
Write-Host "🌐 FastAPI backend startar på: http://localhost:8001" -ForegroundColor Green
python -m uvicorn fastapi_app:app --host 0.0.0.0 --port 8001 --reload 