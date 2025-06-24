#!/bin/bash

echo "🔍 Miljö-kontroll för Trading Bot"
echo "================================"

# Kontrollera virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual Environment: AKTIVERAD ($VIRTUAL_ENV)"
else
    echo "❌ Virtual Environment: INTE AKTIVERAD"
    echo "   Kör: source venv/bin/activate"
fi

# Kontrollera Python-path
PYTHON_PATH=$(which python)
if [[ "$PYTHON_PATH" == *"venv"* ]]; then
    echo "✅ Python Path: $PYTHON_PATH"
else
    echo "❌ Python Path: $PYTHON_PATH (borde vara i venv/)"
fi

# Kontrollera kritiska paket
echo ""
echo "📦 Kritiska paket:"
PACKAGES=("flask" "supabase" "ccxt" "requests" "pandas")
for package in "${PACKAGES[@]}"; do
    if pip list | grep -q "^$package "; then
        VERSION=$(pip list | grep "^$package " | awk '{print $2}')
        echo "✅ $package: $VERSION"
    else
        echo "❌ $package: SAKNAS"
    fi
done

echo ""
echo "🚀 Flask App Status:"
if pgrep -f "app_integrated" > /dev/null; then
    echo "✅ Trading Bot: IGÅNG"
else
    echo "❌ Trading Bot: STOPPAD"
fi