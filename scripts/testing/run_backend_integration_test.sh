#!/bin/bash

# 🧪 Crypto Trading Bot - Backend Integration Test Runner
# =====================================================
# Detta skript kör integrationstester för backend med virtuell miljö i rotmappen
# Kör från projektets rot: ./scripts/testing/run_backend_integration_test.sh

set -e  # Avsluta vid fel

echo "🧪 Crypto Trading Bot - Kör integrationstester..."
echo "==============================================="

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

echo "✅ Förkunskaper kontrollerade"

# Kör integrationstester
echo "🔄 Kör backend integrationstester..."
python -m pytest backend/tests/integration/ -v

# Kör specifika tester om de finns
if [ -f "backend/tests/test_real_api_integration.py" ]; then
    echo "🔄 Kör tester för real API integration..."
    python -m pytest backend/tests/test_real_api_integration.py -v
fi

if [ -f "backend/tests/test_websocket_user_data_handlers.py" ]; then
    echo "🔄 Kör tester för WebSocket user data handlers..."
    python -m pytest backend/tests/test_websocket_user_data_handlers.py -v
fi

echo "✅ Alla integrationstester klara!"