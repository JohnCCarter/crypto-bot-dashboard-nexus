# Bitfinex API Integration Update Guide

Detta dokument beskriver hur man uppdaterar BitfinexClientWrapper för att fungera med den nya versionen av Bitfinex API-biblioteket (version 3.x).

## Bakgrund

Vi har tidigare implementerat en BitfinexClientWrapper-klass som integrerar med Bitfinex API-biblioteket. Denna wrapper använder GlobalNonceManager för att hantera nonce-värden och förhindra race conditions.

När vi uppgraderade till den nya versionen av Bitfinex API-biblioteket (version 3.x) upptäckte vi att API:et har ändrats betydligt. Detta dokument beskriver de ändringar som krävs för att uppdatera vår wrapper.

## Ändringar i Bitfinex API-biblioteket

### REST API

- Metoder har flyttats från `client.rest` till `client.rest.public`, `client.rest.auth` och `client.rest.merchant`
- Metodnamn har ändrats, t.ex. `get_public_ticker` → `get_t_ticker`
- Metoder är inte längre asynkrona i samma utsträckning
- Returtyper är nu dataklasser istället för dictionaries

### WebSocket API

- Händelsenamn har ändrats
- Endast ett fåtal händelser är tillgängliga som standard (`error`)
- WebSocket-klienten använder nu `open()` istället för `connect()`
- Autentisering hanteras annorlunda

## Uppdatering av BitfinexClientWrapper

### 1. Importera rätt moduler

```python
from bfxapi import Client
```

### 2. Uppdatera REST API-metoder

Gamla metoder:
```python
result = await self.client.rest.get_public_ticker(symbol=symbol)
```

Nya metoder:
```python
result = self.client.rest.public.get_t_ticker(symbol=symbol)
```

### 3. Uppdatera WebSocket-händelser

Gamla händelser:
```python
self.client.wss.on('connected', self._handle_ws_connected)
self.client.wss.on('disconnected', self._handle_ws_disconnected)
self.client.wss.on('error', self._handle_ws_error)
self.client.wss.on('authenticated', self._handle_ws_authenticated)
self.client.wss.on('auth_failed', self._handle_ws_auth_failed)
```

Nya händelser:
```python
self.client.wss.on('open', self._handle_ws_connected)
# 'close' är inte tillgänglig som standard
self.client.wss.on('error', self._handle_ws_error)
# 'auth' och 'auth_error' måste registreras efter prenumeration
```

### 4. Uppdatera WebSocket-anslutning

Gamla metoder:
```python
await self.client.wss.connect()
await self.client.wss.authenticate()
```

Nya metoder:
```python
await self.client.wss.open()
await self.client.wss.auth()
```

### 5. Uppdatera WebSocket-prenumerationer

Gamla metoder:
```python
await self.client.wss.subscribe(channel=channel, symbol=symbol)
```

Nya metoder:
```python
await self.client.wss.subscribe(channel=channel, symbol=symbol)
# Samma metod, men hanteringen av svaret är annorlunda
```

## Exempel på uppdaterad BitfinexClientWrapper

Se `scripts/testing/test_bitfinex_wrapper_updated.py` för en uppdaterad version av BitfinexClientWrapper som fungerar med den nya versionen av Bitfinex API-biblioteket.

## Testning

För att testa den uppdaterade wrappern, kör:

```bash
python scripts/testing/test_bitfinex_simple.py
```

Detta kommer att testa både REST API och GlobalNonceManager.

## Slutsats

Den nya versionen av Bitfinex API-biblioteket kräver betydande ändringar i vår BitfinexClientWrapper. Genom att följa denna guide kan du uppdatera wrappern för att fungera med den nya versionen av biblioteket.

Notera att WebSocket-funktionaliteten i den nya versionen är mer begränsad än i den tidigare versionen, och kan kräva ytterligare anpassningar. 