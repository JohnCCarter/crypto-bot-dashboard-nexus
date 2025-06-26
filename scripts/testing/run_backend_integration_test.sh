#!/bin/bash

# 🔗 Backend WebSocket Integration Test Script
# Testar integration mellan Bitfinex WebSocket och trading bot backend

echo "🔗 BACKEND WEBSOCKET INTEGRATION TEST"
echo "====================================="
echo "Testar backend integration med live WebSocket data..."
echo ""

# Kontrollera att vi är i rätt katalog
if [ ! -d "backend" ]; then
    echo "❌ Denna skript måste köras från projektets root-katalog"
    echo "   Kontrollera att du är i rätt mapp och att 'backend' mappen finns"
    exit 1
fi

# Kontrollera Python och dependencies
echo "📦 Kontrollerar backend dependencies..."
cd backend

# Kontrollera kritiska imports
python3 -c "
import sys
sys.path.insert(0, '..')
try:
    from backend.services.live_data_service import LiveDataService
    from backend.services.websocket_market_service import BitfinexWebSocketClient
    from backend.strategies.ema_crossover_strategy import run_strategy
    from backend.services.risk_manager import RiskManager
    print('✅ Backend imports OK')
except ImportError as e:
    print(f'❌ Backend import error: {e}')
    sys.exit(1)
" || {
    echo "❌ Backend dependencies eller imports saknas"
    echo "   Kör: pip install -r requirements.txt"
    exit 1
}

# Gå tillbaka till root
cd ..

# Kontrollera .env filen
if [ ! -f ".env" ]; then
    echo "⚠️ .env fil saknas - skapar template..."
    cat > .env << 'EOF'
# Bitfinex API Credentials (valfritt för paper trading)
BITFINEX_API_KEY=your_api_key_here
BITFINEX_API_SECRET=your_api_secret_here

# Email notifications (valfritt)
EMAIL_ADDRESS=your_email@example.com
SMTP_PASSWORD=your_password_here
EOF
    echo "📝 .env template skapad - uppdatera med dina värden"
fi

# Ladda .env om den finns
if [ -f ".env" ]; then
    echo "📄 Laddar environment variables från .env..."
    export $(grep -v '^#' .env | xargs)
fi

echo "✅ Backend miljö konfigurerad"
echo ""

# Kontrollera internetanslutning till Bitfinex
echo "🌐 Testar anslutning till Bitfinex..."
if ! curl -s --max-time 5 https://api-pub.bitfinex.com/v2/platform/status > /dev/null; then
    echo "❌ Kan inte nå Bitfinex API"
    exit 1
fi
echo "✅ Bitfinex API tillgängligt"
echo ""

# Kör backend integration test
echo "🚀 Startar backend integration test..."
echo "   (Detta kan ta 1-2 minuter - tryck Ctrl+C för att avbryta)"
echo ""

# Kör test med error handling
python3 scripts/testing/test_backend_websocket_integration.py 2>&1

# Kontrollera exit status
exit_code=$?
echo ""

if [ $exit_code -eq 0 ]; then
    echo "🎉 BACKEND INTEGRATION TEST SLUTFÖRD!"
    echo "✅ Trading bot backend fungerar korrekt med WebSocket data"
    echo ""
    echo "📊 NÄSTA STEG:"
    echo "   • Backend är redo för live trading"
    echo "   • Starta backend server: python3 backend/app.py"
    echo "   • Starta frontend: npm run dev"
    echo "   • Övervaka trading bot: python3 backend/services/main_bot.py"
else
    echo "⚠️ BACKEND INTEGRATION TEST AVSLUTAD MED PROBLEM"
    echo "❌ Backend integration behöver åtgärdas innan live trading"
    echo ""
    echo "🔧 VANLIGA LÖSNINGAR:"
    echo "   • Kontrollera .env konfiguration"
    echo "   • Installera saknade Python dependencies: pip install -r backend/requirements.txt"
    echo "   • Verifiera backend/config.json inställningar"
    echo "   • Kontrollera internetanslutning och API åtkomst"
fi

echo ""
echo "📋 För detaljerad felsökning, se loggar ovan."