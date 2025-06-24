# 📊 Bitfinex Margin Info WebSocket Implementation

## 📋 Översikt

Denna implementation baseras på officiella [Bitfinex WebSocket Margin Info dokumentation](https://docs.bitfinex.com/reference/ws-auth-margin-info) och utökar vår `WebSocketAccountProvider` med real-time margin trading information.

## ✅ Implementerade Margin Features

### 📊 Margin Info Updates (`miu`)
- **`miu`** - Margin info update (margininfo-uppdatering)
- Automatisk prenumeration via autentiserad WebSocket-anslutning
- Real-time updates för margin balance, requirements och trading power

### 💰 Base Margin Data
Grundläggande margin-information för hela kontot:

| Fält | Beskrivning | Format |
|------|-------------|--------|
| `userPL` | User profit and loss | Float |
| `userSwaps` | Amount of swaps a user has | Float |
| `marginBalance` | Balance in margin funding account | Float |
| `marginNet` | Balance after P&L accounted | Float |
| `marginRequired` | Minimum required margin | Float |

### 📈 Symbol-specific Margin Data
Per-symbol margin-information:

| Fält | Beskrivning | Format |
|------|-------------|--------|
| `tradableBalance` | Your buying power | Float |
| `grossBalance` | Buying power incl. reserved funds | Float |
| `buy` | Max amount you can buy at best ASK | Float/null |
| `sell` | Max amount you can sell at best BID | Float/null |

## 🛠️ Teknisk Implementation

### Interface Definitions
```typescript
interface BitfinexMarginBase {
  userPL: number;         // User profit and loss
  userSwaps: number;      // Amount of swaps a user has
  marginBalance: number;  // Balance in your margin funding account
  marginNet: number;      // Balance after P&L is accounted for
  marginRequired: number; // Minimum required margin to keep positions open
}

interface BitfinexMarginSym {
  symbol: string;
  tradableBalance: number; // Your buying power
  grossBalance: number;    // Your buying power including reserved funds
  buy: number | null;      // Maximum amount you can buy at current best ASK
  sell: number | null;     // Maximum amount you can sell at current best BID
}

interface MarginInfo {
  base: BitfinexMarginBase | null;
  symbols: { [symbol: string]: BitfinexMarginSym };
  lastUpdated: number;
}
```

### Message Handler Implementation
```typescript
const handleMarginInfoUpdate = useCallback((updateData: any[]) => {
  const [updateType, ...rest] = updateData;
  
  if (updateType === 'base') {
    // Base margin info update
    const [userPL, userSwaps, marginBalance, marginNet, marginRequired] = rest[0];
    console.log('[WebSocketAccount] 📊 Margin base update - Required:', marginRequired);
    
    setMarginInfo(prev => ({
      ...prev,
      base: {
        userPL: userPL || 0,
        userSwaps: userSwaps || 0,
        marginBalance: marginBalance || 0,
        marginNet: marginNet || 0,
        marginRequired: marginRequired || 0
      },
      lastUpdated: Date.now()
    }));
    
  } else if (updateType === 'sym') {
    // Symbol-specific margin info update
    const [symbol, symData] = rest;
    const [tradableBalance, grossBalance, buy, sell] = symData;
    
    setMarginInfo(prev => ({
      ...prev,
      symbols: {
        ...prev.symbols,
        [symbol]: {
          symbol,
          tradableBalance: tradableBalance || 0,
          grossBalance: grossBalance || 0,
          buy: buy,
          sell: sell
        }
      },
      lastUpdated: Date.now()
    }));
  }
}, []);
```

### WebSocket Message Routing
```typescript
case 'miu': // Margin info update
  if (Array.isArray(messageData)) {
    handleMarginInfoUpdate(messageData);
  }
  break;
```

## 📊 Data Getters

### Margin Requirement
```typescript
const getMarginRequirement = useCallback((): number => {
  return marginInfo.base?.marginRequired || 0;
}, [marginInfo]);
```

### Tradable Balance
```typescript
const getTradableBalance = useCallback((symbol?: string): number => {
  if (symbol && marginInfo.symbols[symbol]) {
    return marginInfo.symbols[symbol].tradableBalance;
  }
  // Return total tradable balance across all symbols if no specific symbol
  return Object.values(marginInfo.symbols).reduce((total, sym) => total + sym.tradableBalance, 0);
}, [marginInfo]);
```

## 🎨 UI Integration

### AccountStatus Component Updates
Margin info visas i `AccountStatus` komponenten:

```tsx
{/* Margin Info Summary */}
{marginInfo.base && (
  <div className="grid grid-cols-2 gap-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
    <div className="space-y-1">
      <Label className="text-xs text-blue-600 font-medium">Margin Required</Label>
      <div className="text-lg font-bold text-blue-800">
        ${getMarginRequirement().toFixed(2)}
      </div>
      <div className="text-xs text-blue-600">
        Net: ${marginInfo.base.marginNet.toFixed(2)}
      </div>
    </div>
    <div className="space-y-1">
      <Label className="text-xs text-blue-600 font-medium">P&L</Label>
      <div className={`text-lg font-bold ${marginInfo.base.userPL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
        ${marginInfo.base.userPL.toFixed(2)}
      </div>
      <div className="text-xs text-blue-600">
        Tradable: ${getTradableBalance().toFixed(2)}
      </div>
    </div>
  </div>
)}
```

## 🔧 Användning

```typescript
const { 
  marginInfo,
  getMarginRequirement,
  getTradableBalance 
} = useWebSocketAccount();

// Kontrollera margin requirement
const marginRequired = getMarginRequirement();
console.log('Minimum margin required:', marginRequired);

// Få tradable balance för specifik symbol
const ethTradable = getTradableBalance('tETHUSD');
console.log('ETH tradable balance:', ethTradable);

// Få total tradable balance
const totalTradable = getTradableBalance();
console.log('Total tradable balance:', totalTradable);

// Kontrollera profit/loss
if (marginInfo.base) {
  console.log('Current P&L:', marginInfo.base.userPL);
  console.log('Margin balance:', marginInfo.base.marginBalance);
  console.log('Net balance:', marginInfo.base.marginNet);
}
```

## 🚨 Viktiga Anteckningar

### Null Values
Enligt Bitfinex dokumentation kan vissa värden vara `null`:
> These messages have gained the ability to send the calculation values equal to "null" meaning that the new calculated value is not yet available. In order to receive those values the user have to actively request for it with a "calc" message.

### Calc Input Support
För att få `null` värden beräknade behöver du skicka `calc` meddelanden:
```typescript
// Send calc request för att få uppdaterade värden
const calcMessage = {
  event: 'calc',
  // calc parameters
};
ws.send(JSON.stringify(calcMessage));
```

## 📈 Real-time Margin Monitoring

### Risk Management
- **Margin Call Warning:** När `marginRequired` närmar sig `marginNet`
- **P&L Tracking:** Real-time profit/loss monitoring
- **Position Sizing:** Använd `tradableBalance` för position sizing

### Trading Power Optimization
- **Buy Power:** `buy` värde för specifika symboler
- **Sell Power:** `sell` värde för specifika symboler
- **Cross-margin:** Total tradable balance över alla symboler

## 🎯 Framtida Förbättringar

1. **Calc Integration:** Implementera automatisk `calc` requests för null värden
2. **Risk Alerts:** Warnings när margin levels blir kritiska
3. **Historical Tracking:** Spara margin history för analys
4. **Chart Integration:** Visuell representation av margin utilization

## 📚 Referenser

- [Bitfinex WebSocket Margin Info](https://docs.bitfinex.com/reference/ws-auth-margin-info)
- [Bitfinex WebSocket Calc Input](https://docs.bitfinex.com/reference/ws-auth-calc)
- [Bitfinex Margin Trading Guide](https://docs.bitfinex.com/docs/margin-trading)

Denna implementation ger fullständig real-time margin information för professionell trading med Bitfinex WebSocket API.