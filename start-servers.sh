#!/bin/bash

echo "🚀 Starting Hybrid Trading Bot Servers..."
echo "════════════════════════════════════════════════════════════════"

# Kill any existing processes
echo "🔧 Stopping existing processes..."
pkill -f "npm run dev" 2>/dev/null
pkill -f "vite" 2>/dev/null
pkill -f "flask" 2>/dev/null
sleep 2

# Start backend in background
echo "🔥 Starting Backend (port 5000)..."
cd /workspace
source venv/bin/activate
PYTHONPATH=/workspace FLASK_APP=backend.app python -m flask run --host=0.0.0.0 --port=5000 &
BACKEND_PID=$!

# Start frontend in background  
echo "📱 Starting Frontend (port 8081)..."
npm run dev &
FRONTEND_PID=$!

echo ""
echo "✅ Servers started!"
echo "Frontend: http://localhost:8081"
echo "Backend:  http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop both servers"

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID; echo 'Servers stopped'; exit" INT
wait