#!/bin/bash

echo "🔪 Stoppar alla Python-analysverktyg för bättre prestanda..."

# Döda alla Cursor Python-verktyg
pkill -f "ms-python.pylint"
pkill -f "ms-python.black-formatter" 
pkill -f "ms-python.autopep8"
pkill -f "ms-python.flake8"
pkill -f "ms-python.mypy-type-checker"
pkill -f "ms-python.isort"

# Döda alla lsp_server processer
pkill -f "lsp_server.py"

echo "✅ Alla analysverktyg stoppade!"

# Visa aktuell status
echo ""
echo "📊 Kvarvarande Python-processer:"
REMAINING=$(ps aux | grep python | grep cursor-server | wc -l)
echo "Antal: $REMAINING"

if [ $REMAINING -eq 0 ]; then
    echo "🎉 Perfekt! Inga analysverktyg kör längre."
else
    echo "⚠️  Några processer kör fortfarande. Starta om Cursor för bästa resultat."
fi