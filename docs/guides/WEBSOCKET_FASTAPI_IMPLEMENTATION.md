# FastAPI WebSocket Implementation Guide

## Översikt

Detta dokument beskriver implementationen av WebSocket-stöd i FastAPI som en del av migrationen från Flask till FastAPI.

## Implementerade funktioner

- WebSocket-endpoints för marknadsdata (ticker, orderbook, trades)
- WebSocket-endpoints för användardata (balances, orders, positions)
- Connection Managers för att hantera klient-anslutningar
- Integration med befintliga WebSocket-services

## WebSocket-endpoints

### Marknadsdata (`/ws/market/{client_id}`)

WebSocket-endpoint för att ta emot realtidsuppdateringar av marknadsdata:

- Ticker-data (priser, volym)
- Orderbook-data (bids/asks)
- Trades-data (utförda affärer)

```typescript
// Exempel på anslutning från frontend
const ws = new WebSocket(`ws://localhost:8001/ws/market/client-123?symbol=BTCUSD`);

// Lyssna på meddelanden
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Received ${data.type} data:`, data);
};

// Prenumerera på orderbook
ws.send(JSON.stringify({
  action: "subscribe",
  channel: "orderbook",
  symbol: "BTCUSD"
}));
```

### Användardata (`/ws/user/{client_id}`)

WebSocket-endpoint för att ta emot realtidsuppdateringar av användarspecifik data:

- Balans-uppdateringar
- Order-uppdateringar
- Positions-uppdateringar

```typescript
// Exempel på anslutning från frontend
const ws = new WebSocket(`ws://localhost:8001/ws/user/client-456`);

// Skicka autentiseringsdata direkt efter anslutning
ws.onopen = () => {
  ws.send(JSON.stringify({
    api_key: "YOUR_API_KEY",
    api_secret: "YOUR_API_SECRET"
  }));
};

// Lyssna på meddelanden
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log(`Received ${data.type} data:`, data);
};
```

## Arkitektur

### Connection Manager

För att hantera aktiva WebSocket-anslutningar använder vi en `ConnectionManager`-klass som ansvarar för att:

- Acceptera nya anslutningar
- Hantera frånkopplingar
- Skicka meddelanden till specifika klienter
- Skicka broadcast-meddelanden till alla klienter
- Hantera prenumerationer

```python
# Exempel på ConnectionManager-användning
market_manager = ConnectionManager("market")
await market_manager.connect(websocket, client_id)
await market_manager.send_personal_message(json.dumps(data), websocket)
```

### Integration med befintliga tjänster

WebSocket-endpointsen använder befintliga WebSocket-tjänster:

- `websocket_market_service.py` för marknadsdata
- `websocket_user_data_service.py` för användardata

Dessa tjänster hanterar den faktiska kommunikationen med Bitfinex WebSocket API.

## Livscykelhantering

WebSocket-tjänsterna startas och stoppas i FastAPI-applikationens livscykelhanterare:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup-kod
    try:
        await start_websocket_service()
        logger.info("WebSocket market service started successfully")
    except Exception as e:
        logger.error(f"Failed to start WebSocket market service: {e}")
    
    yield
    
    # Shutdown-kod
    try:
        await stop_websocket_service()
        logger.info("WebSocket market service stopped successfully")
    except Exception as e:
        logger.error(f"Failed to stop WebSocket market service: {e}")
```

## Användning från frontend

För att använda WebSocket-endpoints från frontend kan React-hooken `useWebSocket` användas:

```typescript
import { useWebSocket } from '@/hooks/useWebSocket';

// För marknadsdata
const { socket, isConnected, sendMessage } = useWebSocket(
  `ws://localhost:8001/ws/market/client-123?symbol=BTCUSD`,
  (data) => {
    // Hantera inkommande meddelanden
    console.log('Received data:', data);
  }
);

// Prenumerera på en kanal
useEffect(() => {
  if (isConnected) {
    sendMessage({
      action: "subscribe",
      channel: "ticker",
      symbol: "BTCUSD"
    });
  }
}, [isConnected, sendMessage]);
```

## Fördelar med FastAPI WebSockets

1. **Asynkron hantering**: FastAPI:s asynkrona modell passar perfekt för WebSockets
2. **Typsäkerhet**: Genom Pydantic-modeller kan vi säkerställa korrekt meddelandeformat
3. **Dependency Injection**: Enkel integration med FastAPI:s dependency injection-system
4. **Dokumentation**: FastAPI genererar automatiskt dokumentation för WebSocket-endpoints
5. **Skalbarhet**: Asynkron kod möjliggör hantering av många samtidiga anslutningar

## Nästa steg

- Implementera fullständig klienthantering med per-klient prenumerationer
- Utöka användardata-anslutningen med fler datapunkter
- Implementera JWT-autentisering för WebSocket-anslutningar
- Skapa enhets- och integrationstester för WebSocket-endpoints
- Lägga till komprimering för stora dataströmmar (t.ex. orderbooks)

## Slutsats

WebSocket-stödet i FastAPI utgör en viktig del av migrationen från Flask och ger en robust grund för realtidskommunikation med klienter. Implementationen använder existerande WebSocket-tjänster men med en modernare och mer skalbar arkitektur. 