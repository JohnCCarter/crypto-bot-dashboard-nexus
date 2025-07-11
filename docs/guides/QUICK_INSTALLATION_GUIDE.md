# 🚀 SNABBSTART - HEMDATOR INSTALLATION

## 📋 KRITISKA VERSIONER (MÅSTE MATCHA)

| Komponent | Version | Källa |
|-----------|---------|-------|
| Python | 3.11.9 | python.org |
| Node.js | 24.0.2 | nodejs.org |
| NPM | 11.4.2 | Kommer med Node.js |

---

## ⚡ STEG-FÖR-STEG INSTALLATION

### 1. Rensa Existerande Miljö
```bash
# Ta bort alla Python-installationer från "Lägg till/ta bort program"
# Ta bort alla Node.js-installationer
# Rensa PATH-variabler (ta bort Python/Node.js-sökvägar)
```

### 2. Installera Python 3.11.9
```bash
# 1. Ladda ner från: https://www.python.org/downloads/release/python-3119/
# 2. Välj: "Windows installer (64-bit)"
# 3. Kör installer med "Add Python to PATH" ✅
# 4. Verifiera: python --version
```

### 3. Installera Node.js 24.0.2
```bash
# 1. Ladda ner från: https://nodejs.org/dist/v24.0.2/
# 2. Välj: "node-v24.0.2-x64.msi"
# 3. Kör installer (npm kommer automatiskt)
# 4. Verifiera: node --version && npm --version
```

### 4. Klona Projekt
```bash
git clone https://github.com/JohnCCarter/crypto-bot-dashboard-nexus.git
cd crypto-bot-dashboard-nexus
```

### 5. Installera Python-beroenden
```bash
# Använd den kompletta miljösnapshoten
pip install -r environment_requirements.txt
```

### 6. Installera Node.js-beroenden
```bash
npm install
```

### 7. Verifiera Installation
```bash
# Testa Python
python -c "import fastapi, ccxt, supabase; print('✅ Python OK')"

# Testa Node.js
npm run test
```

---

## 🔍 VERIFIERINGSKOMMANDON

### Python-verifiering
```bash
python --version                   # Ska visa: Python 3.11.9
pip --version                      # Ska visa: pip 25.1.1
pip list | findstr fastapi         # Ska finnas
pip list | findstr ccxt            # Ska finnas
pip list | findstr supabase        # Ska finnas
```

### Node.js-verifiering
```bash
node --version                      # Ska visa: v24.0.2
npm --version                       # Ska visa: 11.4.2
npm list react                      # Ska visa: 18.3.1
npm list typescript                 # Ska visa: 5.6.3
```

### Projekt-verifiering
```bash
cd crypto-bot-dashboard-nexus
python -m pytest backend/tests/    # Alla 62+ tester ska passera
npm run test                       # Alla frontend-tester ska passera
```

---

## 🚨 VANLIGA PROBLEM & LÖSNINGAR

### Problem: Python version fel
```bash
# Lösning: Avinstallera alla Python-versioner och installera 3.11.9
# Kontrollera PATH-variabler
```

### Problem: Node.js version fel
```bash
# Lösning: Avinstallera alla Node.js-versioner och installera 24.0.2
```

### Problem: pip install misslyckas
```bash
# Lösning: Uppdatera pip först
python -m pip install --upgrade pip
pip install -r environment_requirements.txt
```

### Problem: npm install misslyckas
```bash
# Lösning: Rensa cache och installera om
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

---

## 📞 HJÄLP

Om du stöter på problem:

1. **Kontrollera versioner** - Använd verifieringskommandona ovan
2. **Jämför med snapshot** - Se `docs/guides/ENVIRONMENT_SNAPSHOT_2025_01_10.md`
3. **Rensa och installera om** - Följ steg 1-7 igen
4. **Kontrollera PATH** - Säkerställ att Python/Node.js finns i PATH

---

**Skapad:** 2025-07-11  
**Baserat på:** Jobbdator-snapshot med användare fa06662
**Syfte:** Snabb installation på hemdator 