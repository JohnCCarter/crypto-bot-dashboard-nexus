#!/bin/bash

# Skript för att starta frontend-utvecklingsservern på ett smidigt sätt

# Gå till projektets rotmapp
cd "$(dirname "$0")/../.." || exit

# Kontrollera om node_modules finns, om inte installera beroenden
if [ ! -d "node_modules" ]; then
    echo "node_modules hittades inte. Installerar beroenden..."
    npm install
fi

# Skapa .vscode/settings.json om den inte finns
if [ ! -d ".vscode" ]; then
    mkdir -p .vscode
fi

if [ ! -f ".vscode/settings.json" ]; then
    echo '{
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true
}' > .vscode/settings.json
    echo "Skapade .vscode/settings.json för TypeScript-konfiguration"
fi

# Starta utvecklingsservern
echo "Startar frontend-utvecklingsservern..."
npm run dev 