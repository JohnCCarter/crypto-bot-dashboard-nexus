#!/bin/bash

# 🎯 Kod-formatering i optimal ordning för Python backend
# Kör detta script för att formatera all kod enligt projektstandarder

echo "🧹 Formaterar Python kod i optimal ordning..."
echo ""

# Steg 1: Import organisation
echo "1️⃣ FÖRSTA STEGET: isort (Import organisation)"
echo "----------------------------------------"
isort backend/ --profile black
echo "✅ Import organisation klar"
echo ""

# Steg 2: Kod formatering
echo "2️⃣ ANDRA STEGET: black (Kod formatering)"
echo "----------------------------------------"
black backend/
echo "✅ Kod formatering klar"
echo ""

# Steg 3: Linting och kvalitetskontroll
echo "3️⃣ TREDJE STEGET: flake8 (Linting & kvalitet)"
echo "----------------------------------------------"
echo "Kontrollerar kodkvalitet (exkluderar venv)..."

# Kör flake8 och capture output
flake8_output=$(flake8 backend/ --max-line-length=88 --extend-ignore=E203,W503 --exclude=backend/venv 2>&1)
flake8_exit_code=$?

if [ $flake8_exit_code -eq 0 ]; then
    echo "✅ Inga linting-problem hittades!"
else
    echo "⚠️  Linting-problem hittades:"
    echo "$flake8_output"
    echo ""
    echo "💡 Tips för att fixa vanliga problem:"
    echo "   • E501 (line too long): Dela upp långa rader"
    echo "   • E402 (import not at top): Flytta imports till toppen"
    echo "   • F401 (imported but unused): Ta bort oanvända imports"
    echo "   • F841 (variable assigned but unused): Ta bort oanvända variabler"
fi
echo ""

# Sammanfattning
echo "📊 SAMMANFATTNING"
echo "=================="
echo "✅ isort: Import organisation klar"
echo "✅ black: Kod formatering klar"
if [ $flake8_exit_code -eq 0 ]; then
    echo "✅ flake8: Inga kvalitetsproblem"
    echo ""
    echo "🎉 All kod är korrekt formaterad och lintad!"
else
    echo "⚠️  flake8: Kvalitetsproblem hittades (se ovan)"
    echo ""
    echo "🔧 Fixa problemen ovan och kör scriptet igen."
fi

exit $flake8_exit_code 