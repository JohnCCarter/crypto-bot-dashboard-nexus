#!/bin/bash
# 🛑 Stop Development Servers Script
# Följer Zero-Fault Troubleshooting regler

echo "🛑 Stopping Trading Bot Development Servers..."
echo "═══════════════════════════════════════════════"

# Stop tracked processes first
PID_FILE=".dev-servers.pid"
if [ -f $PID_FILE ]; then
    echo "📋 Stopping tracked processes..."
    while read pid; do
        if kill -0 $pid 2>/dev/null; then
            echo "   Stopping PID $pid"
            kill $pid 2>/dev/null || true
        fi
    done < $PID_FILE
    rm -f $PID_FILE
    echo "✅ Tracked processes stopped"
fi

# Force kill any remaining processes
echo "🔧 Cleaning up remaining processes..."

# Backend processes
echo "   Stopping Flask/Python backend..."
pkill -f "flask" 2>/dev/null || true
pkill -f "python.*backend" 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true

# Frontend processes  
echo "   Stopping Vite/NPM frontend..."
pkill -f "npm run dev" 2>/dev/null || true
pkill -f "vite" 2>/dev/null || true
pkill -f "node.*vite" 2>/dev/null || true

# Wait for processes to terminate
sleep 2

# Verify cleanup
echo "🔍 Verifying cleanup..."
REMAINING_BACKEND=$(ps aux | grep -E "(python.*backend|flask)" | grep -v grep | wc -l)
REMAINING_FRONTEND=$(ps aux | grep -E "(vite|npm run dev)" | grep -v grep | wc -l)

if [ $REMAINING_BACKEND -eq 0 ] && [ $REMAINING_FRONTEND -eq 0 ]; then
    echo "✅ All development servers stopped successfully"
    
    # Clean up temp files
    rm -f .dev-servers.pid 2>/dev/null || true
    
    echo ""
    echo "💡 To restart: ./scripts/start-dev.sh"
    exit 0
else
    echo "⚠️  Some processes may still be running:"
    if [ $REMAINING_BACKEND -gt 0 ]; then
        echo "   Backend processes: $REMAINING_BACKEND"
        ps aux | grep -E "(python.*backend|flask)" | grep -v grep
    fi
    if [ $REMAINING_FRONTEND -gt 0 ]; then
        echo "   Frontend processes: $REMAINING_FRONTEND"  
        ps aux | grep -E "(vite|npm run dev)" | grep -v grep
    fi
    echo ""
    echo "💡 Use 'pkill -9 -f flask' and 'pkill -9 -f vite' for force kill"
    exit 1
fi