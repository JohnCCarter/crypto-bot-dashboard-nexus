# Hemdator Synkronisering Guide
*Baserat på jobbdatorns konfiguration från 2025-07-07*

## 🚀 Snabbstart

### 1. Förberedelser
```bash
# Klona projektet (om inte redan gjort)
git clone <repository-url> crypto-bot-dashboard-nexus
cd crypto-bot-dashboard-nexus

# Kontrollera att du är på rätt branch
git status
```

### 2. Python Miljö Setup
```bash
# Kontrollera Python version (ska vara 3.11.9)
python --version

# Skapa virtual environment
python -m venv venv

# Aktivera venv
# På Linux/Mac:
source venv/bin/activate
# På Windows:
# venv\Scripts\activate

# Installera alla paket från jobbdatorn
pip install -r environment_requirements.txt

# Verifiera installation
pip list | grep -E "(fastapi|flask|ccxt|bitfinex|pytest)"
```

### 3. Node.js Miljö Setup
```bash
# Kontrollera Node version (ska vara v24.0.2)
node --version

# Kontrollera npm version (ska vara 11.4.2)
npm --version

# Installera paket
npm install

# Fixa saknade paket
npm install @types/uuid@^10.0.0 uuid@^11.1.0

# Verifiera installation
npm list --depth=0
```

### 4. Miljövariabler
```bash
# Kopiera .env.example till .env (om den inte finns)
cp env.example .env

# Redigera .env med dina lokala inställningar
# Särskilt viktigt: API-nycklar, databas-anslutningar
```

## 🔍 Verifiering

### Python Verifiering
```bash
# Aktivera venv först
source venv/bin/activate

# Testa Python
python --version  # Ska visa 3.11.9

# Testa viktiga paket
python -c "import fastapi; print('FastAPI OK')"
python -c "import flask; print('Flask OK')"
python -c "import ccxt; print('CCXT OK')"
python -c "import bitfinex; print('Bitfinex OK')"
```

### Node.js Verifiering
```bash
# Testa Node.js
node --version  # Ska visa v24.0.2

# Testa npm
npm --version  # Ska visa 11.4.2

# Testa viktiga paket
npm list react  # Ska visa 18.3.1
npm list vite   # Ska visa 5.4.19
```

### Projekt Verifiering
```bash
# Testa backend
cd backend
python -m pytest tests/ -v --tb=short

# Testa frontend
cd ..
npm run test

# Testa byggprocess
npm run build
```

## 🚨 Vanliga Problem och Lösningar

### Problem: Python version fel
```bash
# Lösning: Installera Python 3.11.9
# På Ubuntu/Debian:
sudo apt update
sudo apt install python3.11 python3.11-venv python3.11-pip

# På macOS med Homebrew:
brew install python@3.11

# På Windows: Ladda ner från python.org
```

### Problem: Virtual environment aktiveras inte
```bash
# Kontrollera att venv finns
ls -la venv/

# Skapa nytt venv om det saknas
rm -rf venv
python -m venv venv
source venv/bin/activate
```

### Problem: Paket installation misslyckas
```bash
# Uppdatera pip först
pip install --upgrade pip

# Installera paket en i taget för att identifiera problem
pip install fastapi
pip install flask
pip install ccxt
# ... osv
```

### Problem: Node.js version fel
```bash
# Använd nvm för att hantera Node.js versioner
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install 24.0.2
nvm use 24.0.2
```

### Problem: NPM paket saknas
```bash
# Rensa npm cache
npm cache clean --force

# Ta bort node_modules och installera om
rm -rf node_modules package-lock.json
npm install
```

## 📋 Checklista

### Före Synkronisering
- [ ] Git repository är uppdaterat
- [ ] Python 3.11.9 är installerat
- [ ] Node.js v24.0.2 är installerat
- [ ] npm 11.4.2 är installerat

### Efter Synkronisering
- [ ] Virtual environment är aktivt
- [ ] `pip list` matchar jobbdatorn
- [ ] `npm list --depth=0` visar samma paket
- [ ] Backend tester passerar
- [ ] Frontend tester passerar
- [ ] Projekt bygger utan fel

### Verifiering av Funktion
- [ ] Backend startar: `python -m backend.app`
- [ ] FastAPI startar: `python -m backend.fastapi_app`
- [ ] Frontend startar: `npm run dev`
- [ ] Alla endpoints svarar korrekt

## 📞 Support

Om synkroniseringen misslyckas:

1. **Kontrollera versioner först** - Python, Node.js, npm
2. **Verifiera virtual environment** - måste vara aktivt
3. **Jämför med jobbdatorn** - se `docs/reports/JOBDATOR_KONFIGURATION_SNAPSHOT.md`
4. **Kontrollera nätverksanslutning** - för paketinstallation
5. **Kontrollera diskutrymme** - för installationer

### Loggning för Felsökning
```bash
# Spara output för analys
python --version > sync_log.txt 2>&1
pip list >> sync_log.txt 2>&1
node --version >> sync_log.txt 2>&1
npm list --depth=0 >> sync_log.txt 2>&1
``` 