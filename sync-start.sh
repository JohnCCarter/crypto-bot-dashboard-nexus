#!/bin/bash

echo "🔄 SYNKRONISERINGS-START"
echo "======================="

# Kolla current branch
current_branch=$(git branch --show-current)
echo "📍 Aktuell branch: $current_branch"

# Kolla om det finns osparade ändringar
if [[ -n $(git status --porcelain) ]]; then
    echo "⚠️  VARNING: Du har osparade ändringar!"
    echo "Vill du spara dem först? (y/n)"
    read -r response
    if [[ "$response" =~ ^[Yy]$ ]]; then
        echo "💾 Sparar ändringar..."
        git add .
        echo "📝 Ange commit meddelande:"
        read -r message
        if [ -z "$message" ]; then
            message="Automatisk backup innan pull - $(date '+%Y-%m-%d %H:%M')"
        fi
        git commit -m "$message"
        echo "✅ Ändringar sparade!"
    fi
fi

echo "🌐 Hämtar senaste ändringar från GitHub..."
git fetch

# Kolla om remote har updates
if [[ $(git rev-parse HEAD) != $(git rev-parse @{u}) ]]; then
    echo "📥 Nya ändringar hittade! Hämtar..."
    git pull
    
    if [ $? -eq 0 ]; then
        echo "✅ Senaste ändringar hämtade framgångsrikt!"
        echo "📋 Senaste commits:"
        git log --oneline -3
    else
        echo "❌ Problem med git pull. Kontrollera manuellt."
        exit 1
    fi
else
    echo "✅ Du har redan senaste versionen!"
fi

echo ""
echo "🎯 SYSTEMSTATUS:"
echo "==============="

# Kolla backend dependencies
if [ -f "backend/requirements.txt" ]; then
    if [ -d "venv" ]; then
        echo "✅ Python virtual environment: OK"
    else
        echo "⚠️  Virtual environment saknas. Kör:"
        echo "   python3 -m venv venv && source venv/bin/activate && pip install -r backend/requirements.txt"
    fi
fi

# Kolla frontend dependencies  
if [ -f "package.json" ]; then
    if [ -d "node_modules" ]; then
        echo "✅ Node.js dependencies: OK"
    else
        echo "⚠️  Node modules saknas. Kör: npm install"
    fi
fi

# Kolla om servrar körs
if pgrep -f "flask" > /dev/null; then
    echo "✅ Flask backend: Körs redan"
else
    echo "⚠️  Flask backend: Inte startad"
    echo "   Starta med: python -m flask run --debug --host=0.0.0.0 --port=5000"
fi

if pgrep -f "vite" > /dev/null || pgrep -f "npm.*dev" > /dev/null; then
    echo "✅ Frontend dev server: Körs redan"
else
    echo "⚠️  Frontend dev server: Inte startad"
    echo "   Starta med: npm run dev -- --port 8081 --host 0.0.0.0"
fi

echo ""
echo "🚀 REDO ATT JOBBA!"
echo "=================="
echo "Nästa steg:"
echo "1. Aktivera venv (om nödvändigt): source venv/bin/activate"
echo "2. Starta servrarna (om nödvändiga)"
echo "3. Öppna projektet i din editor"
echo ""
echo "💡 Tips: Kör ./sync-end.sh när du är klar för dagen!"