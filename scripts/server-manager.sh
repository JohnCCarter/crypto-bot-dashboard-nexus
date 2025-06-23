#!/bin/bash
# 🚀 Robust Server Manager for Trading Bot
# Följer cursor-rules-general-standards.mdc och Zero-Fault Troubleshooting

set -e  # Exit on any error

# Server configuration
BACKEND_PORT=5000
FRONTEND_PORT=8081
BACKEND_DIR="/workspace"
PID_FILE=".server-manager.pid"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function: Check if port is free
check_port_free() {
    local port=$1
    if python3 -c "
import socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
result = sock.connect_ex(('localhost', $port))
sock.close()
exit(0 if result != 0 else 1)
    "; then
        return 0  # Port is free
    else
        return 1  # Port is occupied
    fi
}

# Function: Force kill processes on port
kill_port() {
    local port=$1
    log_info "Freeing port $port..."
    
    # Kill processes by name patterns
    pkill -f "flask.*$port" 2>/dev/null || true
    pkill -f "python.*flask.*$port" 2>/dev/null || true
    pkill -f "vite.*$port" 2>/dev/null || true
    pkill -f "npm.*dev.*$port" 2>/dev/null || true
    
    # Wait a moment
    sleep 2
    
    # Force kill if still occupied
    if ! check_port_free $port; then
        log_warning "Port $port still occupied, using force kill..."
        pkill -9 -f "flask.*$port" 2>/dev/null || true
        pkill -9 -f "python.*flask.*$port" 2>/dev/null || true
        pkill -9 -f "vite" 2>/dev/null || true
        pkill -9 -f "npm.*dev" 2>/dev/null || true
        sleep 3
    fi
    
    if check_port_free $port; then
        log_success "Port $port is now free"
    else
        log_error "Failed to free port $port"
        return 1
    fi
}

# Function: Stop all servers
stop_servers() {
    log_info "🛑 Stopping all trading bot servers..."
    
    # Stop tracked processes if PID file exists
    if [[ -f $PID_FILE ]]; then
        log_info "Stopping tracked processes..."
        while read pid; do
            if kill -0 $pid 2>/dev/null; then
                log_info "Stopping PID $pid"
                kill $pid 2>/dev/null || true
            fi
        done < $PID_FILE
        rm -f $PID_FILE
    fi
    
    # Kill all related processes
    log_info "Killing all Flask and Vite processes..."
    pkill -f flask 2>/dev/null || true
    pkill -f "python.*backend" 2>/dev/null || true
    pkill -f "npm run dev" 2>/dev/null || true
    pkill -f vite 2>/dev/null || true
    
    sleep 3
    
    # Force kill if necessary
    pkill -9 -f flask 2>/dev/null || true
    pkill -9 -f "python.*backend" 2>/dev/null || true
    pkill -9 -f "npm run dev" 2>/dev/null || true
    pkill -9 -f vite 2>/dev/null || true
    
    sleep 2
    
    # Free ports specifically
    kill_port $BACKEND_PORT
    kill_port $FRONTEND_PORT
    
    log_success "All servers stopped"
}

# Function: Start backend
start_backend() {
    log_info "🔥 Starting Backend (Flask) on port $BACKEND_PORT..."
    
    # Verify port is free
    if ! check_port_free $BACKEND_PORT; then
        log_error "Port $BACKEND_PORT is not free"
        return 1
    fi
    
    # Start backend in background
    cd $BACKEND_DIR
    (
        export PYTHONPATH=/workspace
        export FLASK_APP=backend.app
        export FLASK_ENV=development
        python3 -m flask run --host=0.0.0.0 --port=$BACKEND_PORT
    ) &
    
    BACKEND_PID=$!
    echo $BACKEND_PID >> $PID_FILE
    log_success "Backend started (PID: $BACKEND_PID) on port $BACKEND_PORT"
    
    # Wait and verify startup
    sleep 5
    if kill -0 $BACKEND_PID 2>/dev/null; then
        log_success "Backend is running successfully"
    else
        log_error "Backend failed to start"
        return 1
    fi
}

# Function: Start frontend
start_frontend() {
    log_info "📱 Starting Frontend (Vite) on port $FRONTEND_PORT..."
    
    # Verify port is free
    if ! check_port_free $FRONTEND_PORT; then
        log_error "Port $FRONTEND_PORT is not free"
        return 1
    fi
    
    # Start frontend in background
    cd $BACKEND_DIR
    npm run dev &
    
    FRONTEND_PID=$!
    echo $FRONTEND_PID >> $PID_FILE
    log_success "Frontend started (PID: $FRONTEND_PID) on port $FRONTEND_PORT"
    
    # Wait and verify startup
    sleep 5
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        log_success "Frontend is running successfully"
    else
        log_error "Frontend failed to start"
        return 1
    fi
}

# Function: Health check
health_check() {
    log_info "🏥 Running health checks..."
    
    local backend_ok=false
    local frontend_ok=false
    
    # Check backend
    if curl -s --max-time 5 http://localhost:$BACKEND_PORT/api/status > /dev/null 2>&1; then
        log_success "Backend health check: OK"
        backend_ok=true
    else
        log_error "Backend health check: FAILED"
    fi
    
    # Check frontend
    if curl -s --max-time 5 http://localhost:$FRONTEND_PORT > /dev/null 2>&1; then
        log_success "Frontend health check: OK"
        frontend_ok=true
    else
        log_error "Frontend health check: FAILED"
    fi
    
    if $backend_ok && $frontend_ok; then
        log_success "🎉 All systems healthy!"
        echo ""
        echo "🌐 Frontend: http://localhost:$FRONTEND_PORT"
        echo "🔧 Backend:  http://localhost:$BACKEND_PORT"
        echo "📊 API:      http://localhost:$BACKEND_PORT/api/status"
    else
        log_error "🚨 Some systems are unhealthy"
        return 1
    fi
}

# Function: Show status
show_status() {
    log_info "📊 Server Status"
    echo ""
    
    # Port status
    for port in $BACKEND_PORT $FRONTEND_PORT; do
        if check_port_free $port; then
            echo "Port $port: FREE"
        else
            echo "Port $port: OCCUPIED"
        fi
    done
    
    echo ""
    # Process status
    log_info "Running processes:"
    ps aux | grep -E "(flask|python.*backend|vite|npm run dev)" | grep -v grep || echo "No server processes found"
}

# Main script logic
case "$1" in
    "stop")
        stop_servers
        ;;
    "start")
        stop_servers
        echo ""
        start_backend
        echo ""
        start_frontend
        echo ""
        health_check
        ;;
    "restart")
        stop_servers
        echo ""
        start_backend
        echo ""
        start_frontend
        echo ""
        health_check
        ;;
    "status")
        show_status
        ;;
    "health")
        health_check
        ;;
    *)
        echo "🚀 Trading Bot Server Manager"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|health}"
        echo ""
        echo "Commands:"
        echo "  start   - Stop all servers and start fresh"
        echo "  stop    - Stop all servers"
        echo "  restart - Stop and start all servers"
        echo "  status  - Show server and port status"
        echo "  health  - Run health checks"
        echo ""
        echo "Ports:"
        echo "  Backend:  $BACKEND_PORT"
        echo "  Frontend: $FRONTEND_PORT"
        exit 1
        ;;
esac