#!/bin/bash

# 🔍 Bitfinex WebSocket Verification Script
# Kör verifieringstest för att säkerställa korrekt WebSocket-data

echo "🔍 BITFINEX WEBSOCKET VERIFICATION"
echo "=================================="
echo "Testar WebSocket-anslutning och datakvalitet för trading bot..."
echo ""

# Kontrollera att python3 finns
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 krävs men hittades inte"
    exit 1
fi

# Kontrollera att pip dependencies finns
echo "📦 Kontrollerar dependencies..."
python3 -c "import asyncio, websockets, json, logging" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Saknade dependencies. Installerar..."
    pip3 install websockets asyncio-compat || {
        echo "❌ Kunde inte installera dependencies"
        exit 1
    }
fi

echo "✅ Dependencies OK"
echo ""

# Kontrollera internetanslutning
echo "🌐 Testar internetanslutning..."
if ! ping -c 1 api-pub.bitfinex.com &> /dev/null; then
    echo "❌ Kan inte nå Bitfinex API. Kontrollera internetanslutning."
    exit 1
fi
echo "✅ Internetanslutning OK"
echo ""

# Kör WebSocket verifieringstest
echo "🚀 Startar WebSocket verifieringstest..."
echo "   (Detta tar ca 60 sekunder - tryck Ctrl+C för att avbryta)"
echo ""

# Kör verifieringsverktyget
python3 scripts/testing/websocket_verification_tool.py

# Kontrollera resultat
exit_code=$?
echo ""

if [ $exit_code -eq 0 ]; then
    echo "🎉 VERIFIERING SLUTFÖRD!"
    echo "✅ WebSocket-anslutning fungerar korrekt"
    echo "✅ Trading bot bör få utmärkt data från Bitfinex"
    echo ""
    echo "📊 NÄSTA STEG:"
    echo "   • Kör backend integration test: ./scripts/testing/run_backend_integration_test.sh"
    echo "   • Starta trading bot för live trading"
else
    echo "⚠️ VERIFIERING AVSLUTAD MED PROBLEM"
    echo "❌ WebSocket-anslutning eller datakvalitet behöver åtgärdas"
    echo ""
    echo "🔧 FELSÖKNING:"
    echo "   • Kontrollera internetanslutning"
    echo "   • Verifiera att Bitfinex API är tillgängligt"
    echo "   • Kontrollera eventuella brandväggar eller proxy-inställningar"
fi

echo ""
echo "📋 För mer detaljerad information, se loggar ovan."