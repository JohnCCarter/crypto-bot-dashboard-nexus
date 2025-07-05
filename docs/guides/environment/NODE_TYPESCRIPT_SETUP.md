# Node.js och TypeScript-konfiguration

Detta dokument beskriver hur du konfigurerar Node.js och TypeScript för projektet.

## Snabbstart

Vi har skapat två skript för att starta frontend-utvecklingsservern på ett smidigt sätt:

- **Windows (PowerShell)**: `scripts/development/start-frontend.ps1`
- **Linux/macOS (Bash)**: `scripts/development/start-frontend.sh`

Dessa skript:
1. Kontrollerar om `node_modules` finns och installerar beroenden om det behövs
2. Skapar `.vscode/settings.json` för TypeScript-konfiguration om den inte finns
3. Startar utvecklingsservern med `npm run dev`

## Manuell konfiguration

### 1. Installera Node.js

Installera Node.js LTS-versionen (v18.x eller senare):
- Windows: [Ladda ner från nodejs.org](https://nodejs.org/)
- Linux/macOS: Använd nvm (rekommenderas)

```bash
# Installera nvm (Node Version Manager)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.7/install.sh | bash

# Installera och använd Node.js LTS
nvm install --lts
nvm use --lts
```

### 2. Verifiera installationen

```bash
node --version  # Bör visa v18.x eller senare
npm --version   # Bör visa 9.x eller senare
```

### 3. Konfigurera VS Code för TypeScript

För att undvika problem med TypeScript Server och Node.js-sökvägar:

1. Skapa mappen `.vscode` i projektets rot om den inte finns
2. Skapa filen `.vscode/settings.json` med följande innehåll:

```json
{
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true
}
```

### 4. Installera projektets beroenden

```bash
npm install
```

### 5. Starta utvecklingsservern

```bash
npm run dev
```

## Felsökning

### Problem med TypeScript Server

Om du får ett felmeddelande om att TypeScript Server inte kan hitta en giltig Node.js-installation:

#### Lösning 1: Kontrollera VS Code-konfigurationen

1. Verifiera att `.vscode/settings.json` är korrekt konfigurerad
2. Starta om VS Code

#### Lösning 2: Kontrollera TypeScript-installationen

```bash
# Kontrollera att TypeScript är installerat
ls -la node_modules/typescript/lib  # Linux/macOS
dir node_modules\typescript\lib     # Windows
```

Om TypeScript saknas eller är felaktigt installerat:

```bash
npm uninstall typescript
npm install typescript
```

#### Lösning 3: Rensa VS Code-cache

- Windows: Ta bort mappen `%APPDATA%\Code\User\workspaceStorage`
- macOS: Ta bort mappen `~/Library/Application Support/Code/User/workspaceStorage`
- Linux: Ta bort mappen `~/.config/Code/User/workspaceStorage`

### Problem med flera Node.js-versioner

Om du har flera Node.js-versioner installerade:

#### Windows (nvm-windows)

1. Installera [nvm-windows](https://github.com/coreybutler/nvm-windows)
2. Öppna en ny kommandotolk som administratör
3. Kör:

```cmd
nvm install 18
nvm use 18
```

#### Linux/macOS (nvm)

```bash
nvm install 18
nvm use 18
```

## Avancerad konfiguration

### Prettier och ESLint

För att konfigurera Prettier och ESLint för automatisk formatering och linting:

1. Installera VS Code-tillägg:
   - ESLint
   - Prettier - Code formatter

2. Uppdatera `.vscode/settings.json`:

```json
{
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true,
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": "explicit"
  },
  "eslint.validate": ["javascript", "javascriptreact", "typescript", "typescriptreact"],
  "[typescript]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[typescriptreact]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

### Användning av Node.js API i VS Code-tillägg

Om du använder VS Code-tillägg som kräver Node.js API:

1. Kontrollera att Node.js är korrekt installerat och finns i PATH
2. Starta om VS Code
3. Om problemet kvarstår, öppna VS Code-inställningar och lägg till:

```json
"typescript.tsserver.nodePath": "C:\\Program Files\\nodejs\\node.exe"  // Anpassa sökvägen
```

## Rekommenderade VS Code-tillägg

- ESLint
- Prettier - Code formatter
- vscode-styled-components
- Tailwind CSS IntelliSense
- ES7+ React/Redux/React-Native snippets
- Import Cost
- Path Intellisense
- Error Lens 