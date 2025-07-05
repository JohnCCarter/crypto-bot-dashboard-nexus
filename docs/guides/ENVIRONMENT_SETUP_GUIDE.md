# Miljökonfigurationsguide

Detta dokument beskriver hur du konfigurerar utvecklingsmiljön för både backend och frontend.

## Backend-miljö

Se [VENV_MIGRATION_GUIDE.md](./environment/VENV_MIGRATION_GUIDE.md) för instruktioner om hur du migrerar från backend/venv till ./venv.

## Frontend-miljö

### Node.js och npm

1. Installera Node.js LTS-versionen (rekommenderas v18.x eller senare)
2. Verifiera installationen:
   ```bash
   node --version
   npm --version
   ```

### Snabb installation av frontend-beroenden

Kör följande kommando i projektets rotmapp:

```bash
npm install
```

### VS Code-konfiguration för TypeScript

För att undvika problem med TypeScript Server och Node.js-sökvägar, skapa en `.vscode/settings.json`-fil med följande innehåll:

```json
{
  "typescript.tsdk": "node_modules/typescript/lib",
  "typescript.enablePromptUseWorkspaceTsdk": true
}
```

Detta konfigurerar VS Code att använda den lokala TypeScript-versionen i projektet istället för den globala installationen.

### Starta utvecklingsservern

Kör följande kommando för att starta frontend-utvecklingsservern:

```bash
npm run dev
```

## Felsökning

### TypeScript Server-problem

Om du får ett felmeddelande om att TypeScript Server inte kan hitta en giltig Node.js-installation:

1. Kontrollera att `.vscode/settings.json` är korrekt konfigurerad
2. Starta om VS Code
3. Kontrollera att TypeScript är korrekt installerat i projektet:
   ```bash
   ls -la node_modules/typescript/lib
   ```

Om problemet kvarstår, prova följande:

1. Avinstallera och installera om TypeScript:
   ```bash
   npm uninstall typescript
   npm install typescript
   ```
2. Rensa VS Code-cache:
   - Windows: Ta bort mappen `%APPDATA%\Code\User\workspaceStorage`
   - macOS: Ta bort mappen `~/Library/Application Support/Code/User/workspaceStorage`
   - Linux: Ta bort mappen `~/.config/Code/User/workspaceStorage`

### Node.js-versionskonflikt

Om du har flera Node.js-versioner installerade, använd en versionshanterare som nvm (Node Version Manager):

- Windows: [nvm-windows](https://github.com/coreybutler/nvm-windows)
- macOS/Linux: [nvm](https://github.com/nvm-sh/nvm)

Installera och använd rätt version:

```bash
nvm install 18  # Installera Node.js v18
nvm use 18      # Använd Node.js v18
```
