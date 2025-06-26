#!/bin/bash

# 🚀 Development Server Start Script
# ==================================
# Snabb start för utveckling - kör från projektets rot

echo "🔧 Starting development servers..."

# Kontrollera working directory
if [ ! -f "package.json" ] || [ ! -d "backend" ]; then
    echo "❌ FEL: Kör från projektets rot (crypto-bot-dashboard-nexus-1/)"
    exit 1
fi

# Aktivera virtual environment och starta backend i bakgrunden
echo "🐍 Starting backend..."
export FLASK_APP=backend/app.py
export FLASK_ENV=development

# Starta Flask från projektets rot (viktigt för SQLite!)
source backend/venv/Scripts/activate
python -m flask run --host=0.0.0.0 --port=5000 &
BACKEND_PID=$!

# Vänta lite för backend
sleep 3

# Starta frontend
echo "⚛️ Starting frontend..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Servers started!"
echo "Frontend: http://localhost:8081"
echo "Backend:  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Cleanup vid exit
trap "echo '🛑 Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM

# Vänta på interrupt
wait
