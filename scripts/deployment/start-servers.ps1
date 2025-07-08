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

# Funktion för att starta backend
function Start-Backend {
    Write-Host "🐍 Startar backend (FastAPI)..." -ForegroundColor Blue
    
    # Säkerställ att vi är i projektets rot
    $originalLocation = Get-Location
    
    try {
        # Sätt miljövariabler
        $env:FLASK_APP = "backend/app.py"
        $env:FLASK_ENV = "development" 
        $env:FLASK_DEBUG = "true"
        
        Write-Host "📂 Working directory: $(Get-Location)" -ForegroundColor Gray
        Write-Host "🔗 Flask app: $env:FLASK_APP" -ForegroundColor Gray
        Write-Host "🌐 Backend startar på: http://localhost:8001" -ForegroundColor Green
        Write-Host ""
        
        # Aktivera virtual environment och starta Flask
        & "backend\venv\Scripts\Activate.ps1"
        python -m uvicorn backend.fastapi_app:app --host=0.0.0.0 --port=8001
    }
    finally {
        Set-Location $originalLocation
    }
}

# Funktion för att starta frontend
function Start-Frontend {
    Write-Host "⚛️ Startar frontend (Vite)..." -ForegroundColor Magenta
    Write-Host "🌐 Frontend startar på: http://localhost:8081" -ForegroundColor Green
    Write-Host ""
    npm run dev
}

# Funktion för att kontrollera om backend svarar
function Test-Backend {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:5000/api/status" -UseBasicParsing -TimeoutSec 5
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

# Huvudlogik baserat på mode
switch ($Mode) {
    "backend" {
        Start-Backend
    }
    "frontend" {
        Start-Frontend  
    }
    "both" {
        Write-Host "🚀 Startar båda servrarna..." -ForegroundColor Cyan
        Write-Host "🛑 Tryck Ctrl+C för att stoppa båda" -ForegroundColor Yellow
        Write-Host ""
        
        # Starta backend i bakgrunden
        $backendJob = Start-Job -ScriptBlock {
            Set-Location $using:PWD
            $env:FLASK_APP = "backend/app.py"
            $env:FLASK_ENV = "development"
            $env:FLASK_DEBUG = "true"
            
            & "backend\venv\Scripts\Activate.ps1"
            python -m uvicorn backend.fastapi_app:app --host=0.0.0.0 --port=8001
        }
        
        # Vänta lite för backend att starta
        Start-Sleep -Seconds 5
        
        # Kontrollera att backend startade
        if (Test-Backend) {
            Write-Host "✅ Backend igång på port 8001" -ForegroundColor Green
        } else {
            Write-Host "⚠️ Backend kanske inte startade korrekt" -ForegroundColor Yellow
        }
        
        try {
            # Starta frontend (blockerar här)
            Start-Frontend
        }
        finally {
            # Cleanup när skriptet avslutas
            Write-Host "🛑 Stoppar servrar..." -ForegroundColor Yellow
            Stop-Job $backendJob -ErrorAction SilentlyContinue
            Remove-Job $backendJob -ErrorAction SilentlyContinue
        }
    }
}

Write-Host "✅ Servrar stoppade" -ForegroundColor Green 