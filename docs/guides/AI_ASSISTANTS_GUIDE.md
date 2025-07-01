# AI-assistenter för utvecklingsarbete

Denna guide beskriver hur du kan använda olika AI-assistenter effektivt i utvecklingen av crypto-bot-dashboard-nexus projektet.

## GitHub Copilot

GitHub Copilot är en AI-kodassistent som hjälper dig skriva kod snabbare och med bättre kvalitet direkt i din editor.

### Installation och konfiguration

1. Installera GitHub Copilot i din kodredigerare:
   - **VS Code**: Installera från Extensions Marketplace
   - **JetBrains IDEs**: Installera via Plugins/Marketplace 
   - **Vim/Neovim**: Använd plugin-hanteraren

2. Logga in med ett GitHub-konto som har Copilot-prenumeration

3. Projektkonfigurationen finns i:
   - `.github/copilot/dictionary.json` - Projektspecifika termer
   - `.github/copilot/ignore.yml` - Filer att ignorera/fokusera på

### Projektspecifika verktyg

Vi har skapat verktyg för att förbättra Copilot-integrationen:

```bash
# Uppdatera Copilot-kontext baserad på aktuell kodstruktur
python scripts/development/copilot_helper.py --update-context
```

Detta skapar JSON-filer med kontext om strategier, tjänster och komponenter som förbättrar Copilots förståelse av kodbasen.

### Effektiv användning med Copilot

- **För Python-backend**:
  - Skriv kommentarer som beskriver vad strategin/servicen ska göra
  - Använd docstrings för att beskriva funktioner
  - Definiera typer med hjälp av typannotationer

- **För React/TypeScript-frontend**:
  - Skapa prop-typedefinitioner först
  - Använd JSDoc-kommentarer för att beskriva komponenten
  - Skapa hook-funktioner med tydliga namn

### Tips för bättre förslag

1. Uppdatera regelbundet kontext med `copilot_helper.py`
2. Inkludera beskrivande kommentarer innan implementation
3. Använd en tydlig namngivningskonvention
4. Dela upp komplexa funktioner i mindre bitar

## Inbyggd kodgranskning med Cursor

Cursor har en inbyggd AI som kan användas för kodgranskning direkt i editorn.

### Användning av Cursor AI

1. Markera en kodfil eller ett kodblock
2. Tryck `Ctrl+K` eller högerklicka och välj "Ask Cursor"
3. Ställ en fråga som:
   - "Granska denna kod för förbättringsmöjligheter"
   - "Hur kan jag förbättra prestandan i denna funktion?"
   - "Finns det några säkerhetsproblem i denna kod?"

### Tips för bättre granskning

- Var specifik i dina frågor
- Fokusera på ett problem i taget
- Ge kontext om vad koden ska göra

## Kommande implementationer

I framtida faser planerar vi att lägga till:
- Pre-commit hooks för automatisk kodformatering
- CI/CD-integration för kodkvalitetskontroller
- Integrering av statiska kodanalysverktyg

## Exempel på användning

### Skapa en ny handelsstrategi

```python
# En strategi som kombinerar RSI och bollinger bands
# för att identifiera överköpta/översålda tillstånd

def run_strategy(data: pd.DataFrame) -> TradeSignal:
    # Låt Copilot föreslå implementation baserat på denna kommentar
```

### Skapa en React-komponent

```tsx
/**
 * ProfitChart - Visar vinst/förlust över tid med filtreringsmöjligheter
 * @param {Object} props - Komponentegenskaper
 * @param {Trade[]} props.trades - Genomförda affärer
 * @param {string} props.timeFrame - Tidram för visning
 */
``` 