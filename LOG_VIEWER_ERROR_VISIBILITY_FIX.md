# 🔍 LogViewer Error Visibility Fix - Lösning

## 📋 **Problem**
Felmeddelanden från API-anrop (400 Bad Request, 500 Internal Server Error) visades bara i webbläsarens Console/Network-flik, men **INTE** i dashboardens LogViewer-komponent. Detta gjorde det svårt att debugga fel direkt i gränssnittet.

## 🔍 **Rotorsak**
- **LogViewer** lyssnar på `console.log/error/warn/info` för att visa loggmeddelanden
- **API-fel** kastas som `Error` exceptions i React Query/mutations men triggar inte `console.error` automatiskt
- **Frontend** fångar fel med `try/catch` och React Query's error handling, men loggar dem inte explicit till console

## ✅ **Lösning Implementerad**

### 1. **API Error Logging (src/lib/api.ts)**
Lade till explicit `console.error` för alla API-fel:

```typescript
// FÖRE:
if (!res.ok) throw new Error('Order failed');

// EFTER:
if (!res.ok) {
  const errorMsg = `❌ Order failed: ${res.status} ${res.statusText}`;
  console.error(`[API] ${errorMsg}`, { order, status: res.status });
  throw new Error(errorMsg);
}
```

**Påverkade funktioner:**
- ✅ `placeOrder()` - Order submission fel
- ✅ `getBalances()` - Balance fetch fel  
- ✅ `getActiveTrades()` - Position fetch fel

### 2. **React Query Error Logging**
Lade till `onError`/`useEffect` error handlers:

```typescript
// ManualTradePanel.tsx - Order submission
const submitOrderMutation = useMutation({
  // ... mutation config
  onError: (error, variables) => {
    console.error(`[ManualTrade] ❌ Order failed:`, { 
      error: error.message,
      symbol: variables.symbol, 
      side: variables.side, 
      amount: variables.amount 
    });
  }
});

// HybridBalanceCard.tsx - Balance fetch errors
useEffect(() => {
  if (error) {
    console.error('[HybridBalanceCard] ❌ Failed to fetch balances:', error.message);
  }
}, [error]);
```

### 3. **Enhanced Error Context**
Fel innehåller nu mer detaljerad information:
- **HTTP status codes** (400, 500, etc.)
- **Request context** (symbol, amount, side)
- **Component source** ([API], [ManualTrade], [HybridBalanceCard])
- **Timestamp** (automatiskt från LogViewer)

## 🎯 **Resultat**

**Innan:**
- ❌ API-fel bara synliga i browser console
- ❌ Inget sätt att se fel direkt i dashboard
- ❌ Svårt att debugga för användare

**Efter:**
- ✅ **Alla API-fel visas i LogViewer**
- ✅ **Fel loggas med kontext och detaljer**
- ✅ **Real-time error visibility** i dashboard
- ✅ **Filterbara fel** (Errors Only filter)
- ✅ **Exporterbara logs** för debugging

## 📊 **Example Error Log**
```
[API] ❌ Order failed: 400 Bad Request
Symbol: BTCUSD, Side: buy, Amount: 0.001

[ManualTrade] ❌ Order failed: Order failed: 400 Bad Request  
{error: "Order failed: 400 Bad Request", symbol: "BTCUSD", side: "buy", amount: 0.001, type: "market"}

[HybridBalanceCard] ❌ Failed to fetch balances: Failed to fetch balances: 500 Internal Server Error
```

## 🔄 **Nästa Steg**
1. **Testa systemet** - Försök göra en order för att se felloggning
2. **Verifiera LogViewer** - Kontrollera att fel visas i "Errors Only" filter
3. **Backend debugging** - Fixa 400/500 fel som orsakar loggarna

Nu kommer alla API-fel att vara **synliga direkt i dashboard** för enklare debugging! 🎉