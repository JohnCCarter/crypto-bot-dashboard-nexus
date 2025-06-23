#!/bin/bash
# 🚀 Development Server Startup Script
# Följer cursor-rules-general-standards.mdc och etablerad konfiguration

set -e  # Exit on any error

echo "🚀 Starting Trading Bot Development Servers..."
echo "════════════════════════════════════════════════"

# 1. Kontrollera att setup har körts  
# Check if dependencies are available
if ! python3 -c "import flask" 2>/dev/null; then
    echo "❌ Flask not found. Run './scripts/setup-dev.sh' first"
    exit 1
fi

if [ ! -d "node_modules" ]; then
    echo "❌ Node modules not found. Run './scripts/setup-dev.sh' first"
    exit 1
fi

# 2. Stoppa befintliga processer för clean start
echo "🔧 Stopping existing processes..."
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "flask" 2>/dev/null || true
pkill -f "python.*backend" 2>/dev/null || true
sleep 2

# 3. Skapa process tracking
PID_FILE=".dev-servers.pid"
rm -f $PID_FILE

# 4. Starta Backend (enligt fungerande konfiguration)
echo "🔥 Starting Backend (Flask) on port 5000..."
(
    # Use venv if available, otherwise system python
    if [ -d "venv" ] && [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
    fi
    export PYTHONPATH=/workspace
    export FLASK_APP=backend.app
    export FLASK_ENV=development
    python3 -m flask run --host=0.0.0.0 --port=5000
) &
BACKEND_PID=$!
echo $BACKEND_PID >> $PID_FILE
echo "✅ Backend started (PID: $BACKEND_PID)"

# 5. Vänta lite för backend att starta
sleep 3

# 6. Starta Frontend (Vite)
echo "📱 Starting Frontend (Vite) on port 8081..."
npm run dev &
FRONTEND_PID=$!
echo $FRONTEND_PID >> $PID_FILE
echo "✅ Frontend started (PID: $FRONTEND_PID)"

# 7. Vänta på att servrarna startar
echo "⏳ Waiting for servers to initialize..."
sleep 5

# 8. Health check
echo "🏥 Running health checks..."
./scripts/health-check.sh

echo ""
echo "🎉 Development servers are running!"
echo "────────────────────────────────────"
echo "🌐 Frontend: http://localhost:8081"
echo "🔧 Backend:  http://localhost:5000"
echo "📊 API:      http://localhost:5000/api/status"
echo ""
echo "📋 Commands:"
echo "  - Stop servers: ./scripts/stop-dev.sh"
echo "  - Health check: ./scripts/health-check.sh"
echo "  - View logs:    ./scripts/logs-dev.sh"
echo ""
echo "Press Ctrl+C to stop all servers..."

# 9. Cleanup function
cleanup() {
    echo ""
    echo "🛑 Stopping development servers..."
    if [ -f $PID_FILE ]; then
        while read pid; do
            kill $pid 2>/dev/null || true
        done < $PID_FILE
        rm -f $PID_FILE
    fi
    pkill -f "npm run dev" 2>/dev/null || true
    pkill -f "vite" 2>/dev/null || true
    pkill -f "flask" 2>/dev/null || true
    echo "✅ All servers stopped"
    exit 0
}

# 10. Set up signal handlers
trap cleanup INT TERM

# 11. Keep script running
wait