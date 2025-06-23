#!/bin/bash
# 🏥 Development Servers Health Check
# Följer Zero-Fault Troubleshooting regler

echo "🏥 Health Check - Trading Bot Servers"
echo "═══════════════════════════════════════"

# Exit codes
BACKEND_OK=0
FRONTEND_OK=0

# Test Backend
echo "🔧 Testing Backend (Flask)..."
if curl -s --max-time 5 http://localhost:5000/api/status > /dev/null 2>&1; then
    echo "✅ Backend: Healthy (http://localhost:5000)"
    BACKEND_OK=1
else
    echo "❌ Backend: Not responding (http://localhost:5000)"
    echo "   - Check if Flask is running"
    echo "   - Check backend logs"
fi

# Test Frontend  
echo "📱 Testing Frontend (Vite)..."
if curl -s --max-time 5 http://localhost:8081 > /dev/null 2>&1; then
    echo "✅ Frontend: Healthy (http://localhost:8081)"
    FRONTEND_OK=1
else
    echo "❌ Frontend: Not responding (http://localhost:8081)"
    echo "   - Check if Vite is running"
    echo "   - Check frontend logs"
fi

# Check processes
echo "📊 Process Status:"
echo "Backend processes:"
ps aux | grep -E "(python.*backend|flask)" | grep -v grep || echo "   No backend processes found"

echo "Frontend processes:"
ps aux | grep -E "(vite|npm run dev)" | grep -v grep || echo "   No frontend processes found"

# Summary
echo ""
echo "📋 Summary:"
if [ $BACKEND_OK -eq 1 ] && [ $FRONTEND_OK -eq 1 ]; then
    echo "🎉 All systems healthy!"
    exit 0
elif [ $BACKEND_OK -eq 1 ]; then
    echo "⚠️  Frontend issues detected"
    exit 1
elif [ $FRONTEND_OK -eq 1 ]; then
    echo "⚠️  Backend issues detected"
    exit 1
else
    echo "❌ Both servers have issues"
    echo "💡 Try: ./scripts/stop-dev.sh && ./scripts/start-dev.sh"
    exit 2
fi