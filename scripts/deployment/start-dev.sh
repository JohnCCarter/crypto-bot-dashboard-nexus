#!/bin/bash

# 🚀 Crypto Trading Bot - Development Start Script
# ===============================================
# Detta skript startar utvecklingsmiljön med virtuell miljö i rotmappen
# Kör från projektets rot: ./scripts/deployment/start-dev.sh

set -e  # Avsluta vid fel

echo "🔧 Crypto Trading Bot - Startar utvecklingsmiljö..."
echo "=================================================="

# Kontrollera att vi är i projektets rot
if [ ! -f "package.json" ] || [ ! -d "backend" ]; then
    echo "❌ FEL: Kör detta skript från projektets rot (crypto-bot-dashboard-nexus-1/)"
    echo "📁 Nuvarande katalog: $(pwd)"
    exit 1
fi

# Kontrollera om virtuell miljö finns
if [ -d "venv" ]; then
    echo "✅ Använder virtuell miljö i rotmappen"
    source venv/Scripts/activate
elif [ -d "backend/venv" ]; then
    echo "⚠️ Använder virtuell miljö i backend-mappen (legacy)"
    echo "⚠️ Rekommendation: Migrera till virtuell miljö i rotmappen enligt docs/guides/environment/VENV_MIGRATION_GUIDE.md"
    source backend/venv/Scripts/activate
else
    echo "❌ Ingen virtuell miljö hittades. Skapar en ny i rotmappen..."
    python -m venv venv
    source venv/Scripts/activate
    pip install -r backend/requirements.txt
fi

# Kontrollera Python-version
PYTHON_VERSION=$(python -V 2>&1)
echo "🐍 Python-version: $PYTHON_VERSION"
if [[ ! "$PYTHON_VERSION" == *"3.11"* ]]; then
    echo "⚠️ Varning: Rekommenderad Python-version är 3.11.9. Du använder $PYTHON_VERSION"
    echo "💡 Se docs/guides/ENVIRONMENT_SETUP_GUIDE.md för instruktioner om hur du installerar rätt version."
fi

# Kontrollera npm dependencies
if [ ! -d "node_modules" ]; then
    echo "❌ FEL: Node.js dependencies saknas"
    echo "💡 Kör: npm install"
    exit 1
fi

echo "✅ Förkunskaper kontrollerade"

# Funktion för att starta FastAPI
start_fastapi() {
  echo "🔄 Startar FastAPI backend..."
  cd backend
  source ../venv/Scripts/activate
  echo "🌐 FastAPI backend startar på: http://localhost:8001"
  python -m uvicorn fastapi_app:app --host 0.0.0.0 --port 8001 --reload
}

# Funktion för att starta frontend
start_frontend() {
    echo "🔄 Startar frontend..."
    cd "$(pwd)" || exit
    npm run dev
}

# Starta FastAPI/Uvicorn
python3 -m uvicorn backend.fastapi_app:app --host=0.0.0.0 --port=8001 &
FASTAPI_PID=$!

# Vänta lite för att låta FastAPI starta
sleep 2

start_frontend &
FRONTEND_PID=$!

echo "✅ Alla servrar startade!"
echo "- Backend (FastAPI): http://localhost:8001"
echo "- Frontend: http://localhost:5173"

# Funktion för att städa upp processer vid avslut
cleanup() {
    echo "🛑 Avslutar processer..."
    kill $FASTAPI_PID $FRONTEND_PID 2>/dev/null
    exit 0
}

# Registrera cleanup-funktionen för att köras vid avslut
trap cleanup SIGINT SIGTERM

# Håll skriptet igång
echo "⚠️ Tryck Ctrl+C för att avsluta alla processer."
wait
