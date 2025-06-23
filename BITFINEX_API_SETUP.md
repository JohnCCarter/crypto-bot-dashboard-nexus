# 🔐 Säker Bitfinex API Konfiguration

## 📋 Steg för att konfigurera riktiga API-nycklar

### 1. Skapa API-nycklar på Bitfinex
- Logga in på Bitfinex.com
- Gå till Settings → API
- Skapa ny API Key med permissions:
  - ✅ Account History
  - ✅ Orders  
  - ✅ Positions
  - ✅ Wallets
  - ❌ Trading (INTE aktivera för säkerhet)

### 2. Uppdatera .env fil
```bash
# Öppna .env filen
nano .env

# Ersätt dessa rader:
EXCHANGE_API_KEY=your_bitfinex_api_key_here
EXCHANGE_API_SECRET=your_bitfinex_api_secret_here

# Med dina riktiga nycklar:
EXCHANGE_API_KEY=din_riktiga_api_key
EXCHANGE_API_SECRET=din_riktiga_api_secret
```

### 3. Restart servrar
```bash
bot-restart
```

### 4. Verifiera att riktiga data visas
```bash
curl -s http://localhost:5000/api/balances
```

## 🛡️ Säkerhetsaspekter

- ✅ .env är i .gitignore (commitas ALDRIG)
- ✅ API-nycklar har bara READ permissions
- ✅ Backup skapas automatiskt
- ⚠️ Dela ALDRIG API-nycklar med någon
- ⚠️ Om nycklarna komprometteras - radera dem på Bitfinex

## 🧪 Test med Mock Data

Om du vill behålla mock-data:
```bash
# Sätt tillbaka placeholder-värden i .env
EXCHANGE_API_KEY=your_bitfinex_api_key_here
EXCHANGE_API_SECRET=your_bitfinex_api_secret_here
```

Systemet växlar automatiskt till demo-data.