#!/bin/bash
# 🚀 Convenient aliases för Trading Bot Server Management
# Lägg till i din .bashrc eller kör: source scripts/aliases.sh

# Core server commands
alias bot-start="./scripts/server-manager.sh start"
alias bot-stop="./scripts/server-manager.sh stop"
alias bot-restart="./scripts/server-manager.sh restart"
alias bot-status="./scripts/server-manager.sh status"
alias bot-health="./scripts/server-manager.sh health"

# Quick development shortcuts
alias bot-logs="tail -f backend/*.log 2>/dev/null || echo 'No log files found'"
alias bot-test="npm test && cd backend && python -m pytest tests/"
alias bot-lint="npm run lint && cd backend && python -m flake8 ."

# Quick navigation
alias bot-cd="cd /workspace"
alias bot-backend="cd /workspace/backend"
alias bot-frontend="cd /workspace"

echo "✅ Trading Bot aliases loaded!"
echo "📚 Available commands:"
echo "  🚀 bot-start    - Start both servers"
echo "  🛑 bot-stop     - Stop both servers"
echo "  🔄 bot-restart  - Restart both servers"
echo "  📊 bot-status   - Show server status"
echo "  🏥 bot-health   - Run health checks"
echo "  📝 bot-logs     - Show live logs"
echo "  🧪 bot-test     - Run all tests"
echo "  🔍 bot-lint     - Run all linters"