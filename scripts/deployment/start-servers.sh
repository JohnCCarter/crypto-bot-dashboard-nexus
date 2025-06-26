#!/bin/bash

# 🚀 Crypto Trading Bot - Server Start Script
# ===========================================
# Detta skript startar både backend (Flask) och frontend (Vite) korrekt
# Kör från projektets rot: ./start-servers.sh

set -e  # Avsluta vid fel

echo "🔧 Crypto Trading Bot - Startar servrar..."
echo "============================================"

# Kontrollera att vi är i projektets rot
if [ ! -f "package.json" ] || [ ! -d "backend" ]; then
    echo "❌ FEL: Kör detta skript från projektets rot (crypto-bot-dashboard-nexus-1/)"
    echo "📁 Nuvarande katalog: $(pwd)"
    exit 1
fi

# Kontrollera Python virtual environment
if [ ! -d "backend/venv" ]; then
    echo "❌ FEL: Python virtual environment saknas i backend/venv"
    echo "💡 Kör: cd backend && python -m venv venv && source venv/Scripts/activate && pip install -r requirements.txt"
    exit 1
fi

# Kontrollera npm dependencies
if [ ! -d "node_modules" ]; then
    echo "❌ FEL: Node.js dependencies saknas"
    echo "💡 Kör: npm install"
    exit 1
fi

echo "✅ Förkunskaper kontrollerade"

# Funktion för att starta backend
start_backend() {
    echo "🐍 Startar backend (Flask)..."
    cd "$(dirname "$0")"  # Säkerställ att vi är i projektets rot
    
    # Aktivera virtual environment och starta Flask
    export FLASK_APP=backend/app.py
    export FLASK_ENV=development
    export FLASK_DEBUG=true
    
    echo "📂 Working directory: $(pwd)"
    echo "🔗 Flask app: $FLASK_APP"
    echo "🌐 Backend startar på: http://localhost:5000"
    echo ""
    
    # Starta Flask från projektets rot (viktigt för SQLite-sökvägen)
    source backend/venv/Scripts/activate
    python -m flask run --host=0.0.0.0 --port=5000
}

# Funktion för att starta frontend
start_frontend() {
    echo "⚛️ Startar frontend (Vite)..."
    echo "🌐 Frontend startar på: http://localhost:8081"
    echo ""
    npm run dev
}

# Hantera kommandoradsargument
case "${1:-both}" in
    "backend")
        start_backend
        ;;
    "frontend")
        start_frontend
        ;;
    "both"|"")
        echo "🚀 Startar båda servrarna..."
        echo "🛑 Tryck Ctrl+C för att stoppa båda"
        echo ""
        
        # Starta backend i bakgrunden
        start_backend &
        BACKEND_PID=$!
        
        # Vänta lite för backend att starta
        sleep 3
        
        # Kontrollera att backend startade
        if curl -s http://localhost:5000/api/status > /dev/null 2>&1; then
            echo "✅ Backend igång på port 5000"
        else
            echo "⚠️ Backend kanske inte startade korrekt"
        fi
        
        # Starta frontend
        start_frontend
        
        # Cleanup när skriptet avslutas
        trap "echo '🛑 Stoppar servrar...'; kill $BACKEND_PID 2>/dev/null; exit" INT TERM
        ;;
    *)
        echo "❓ Användning: $0 [backend|frontend|both]"
        echo ""
        echo "Exempel:"
        echo "  $0           # Startar båda (standard)"
        echo "  $0 backend   # Startar endast backend" 
        echo "  $0 frontend  # Startar endast frontend"
        exit 1
        ;;
esac