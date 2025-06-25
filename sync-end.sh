#!/bin/bash

echo "💾 SYNKRONISERINGS-SLUT"
echo "======================"

# Kolla current branch
current_branch=$(git branch --show-current)
echo "📍 Aktuell branch: $current_branch"

# Kolla om det finns ändringar att spara
if [[ -z $(git status --porcelain) ]]; then
    echo "✅ Inga ändringar att spara!"
    echo "🎯 Verifierar att du har senaste versionen..."
    git fetch
    
    if [[ $(git rev-parse HEAD) == $(git rev-parse @{u}) ]]; then
        echo "✅ Du är uppdaterad med remote repository!"
    else
        echo "⚠️  Remote har uppdateringar. Kör git pull för att hämta dem."
    fi
    
    echo ""
    echo "🎉 Session avslutad - inget att synka!"
    exit 0
fi

echo "📊 ÄNDRINGAR SOM KOMMER SPARAS:"
echo "==============================="
git status --short

echo ""
echo "📝 COMMIT MEDDELANDE:"
echo "Ange kort beskrivning av vad du har arbetat med"
echo "(eller tryck Enter för automatiskt meddelande):"
read -r message

if [ -z "$message" ]; then
    # Automatiskt meddelande baserat på ändrade filer
    changed_files=$(git diff --name-only | head -3)
    if [ -n "$changed_files" ]; then
        message="Arbetssession $(date '+%Y-%m-%d %H:%M') - Uppdateringar i: $(echo $changed_files | tr '\n' ' ')"
    else
        message="Arbetssession slutförd - $(date '+%Y-%m-%d %H:%M')"
    fi
    echo "📋 Använder automatiskt meddelande: $message"
fi

echo ""
echo "💾 SPARAR ÄNDRINGAR..."
echo "====================="

# Lägg till alla ändringar
echo "📁 Lägger till filer..."
git add .

# Kolla att vi har något att committa
if [[ -z $(git diff --cached --name-only) ]]; then
    echo "⚠️  Inga ändringar att committa efter git add."
    exit 1
fi

# Commita ändringar
echo "💾 Committar ändringar..."
git commit -m "$message"

if [ $? -ne 0 ]; then
    echo "❌ Problem med git commit. Kontrollera manuellt."
    exit 1
fi

echo "✅ Ändringar committade!"

echo ""
echo "🚀 SKICKAR TILL GITHUB..."
echo "========================"

# Pusha till remote
git push

if [ $? -eq 0 ]; then
    echo "✅ Framgångsrikt skickat till GitHub!"
    
    # Visa commit info
    echo ""
    echo "📋 SENASTE COMMITS:"
    echo "=================="
    git log --oneline -3
    
    echo ""
    echo "🔗 REPOSITORY STATUS:"
    echo "===================="
    git remote -v | head -1
    echo "Branch: $current_branch"
    echo "Synkad med remote: ✅"
    
else
    echo "❌ Problem med git push!"
    echo "Dina ändringar är sparade lokalt men inte skickade till GitHub."
    echo "Kontrollera internetanslutning och försök igen med: git push"
    exit 1
fi

echo ""
echo "🎉 SESSION AVSLUTAD FRAMGÅNGSRIKT!"
echo "=================================="
echo "✅ Alla ändringar sparade och synkroniserade"
echo "✅ Redo för nästa arbetstillfälle"
echo ""
echo "💡 Nästa gång du börjar arbeta:"
echo "   1. På samma dator: Fortsätt direkt"
echo "   2. På annan dator: Kör ./sync-start.sh först"
echo ""
echo "🔄 Ha en bra dag! Ditt arbete är säkert!"