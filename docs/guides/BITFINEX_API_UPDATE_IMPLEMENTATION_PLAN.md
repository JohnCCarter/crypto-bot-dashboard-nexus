# Bitfinex API Uppdatering - Implementationsplan

Detta dokument beskriver den detaljerade implementationsplanen för att uppdatera BitfinexClientWrapper för att fungera med den nya versionen av Bitfinex API-biblioteket (version 3.x).

## 1. Förberedelser och backup

- [ ] Skapa backups av alla filer som ska ändras i `.codex_backups/YYYY-MM-DD/`
  - `backend/services/bitfinex_client_wrapper.py`
  - `backend/services/exchange.py` (om den använder BitfinexClientWrapper)
  - `backend/services/websocket_user_data_service.py` (om den använder BitfinexClientWrapper)
  - Andra filer som använder BitfinexClientWrapper

- [ ] Kör baseline-tester för att dokumentera nuvarande funktionalitet
  - `python -m pytest backend/tests/test_bitfinex_client_wrapper.py -v`
  - `python scripts/testing/test_nonce_simple.py`

## 2. Uppdatera BitfinexClientWrapper

### 2.1 Uppdatera importer

```python
# Gamla importer
from bfxapi import Client
from bfxapi.websockets.GenericWSClient import GenericWSClient

# Nya importer
from bfxapi import Client
# Ta bort import av GenericWSClient om den inte används direkt
```

### 2.2 Uppdatera REST API-metoder

- [ ] Uppdatera `get_ticker` metoden
```python
# Gammal implementation
ticker = await self.client.rest.get_public_ticker(symbol=symbol)

# Ny implementation
ticker = self.client.rest.public.get_t_ticker(symbol=symbol)
```

- [ ] Uppdatera `get_order_book` metoden
```python
# Gammal implementation
result = await self.client.rest.get_public_books(symbol=symbol, precision=precision, length=length)

# Ny implementation
result = self.client.rest.public.get_book(symbol=symbol, precision=precision, len=length)
```

- [ ] Uppdatera `get_wallet_balances` metoden
```python
# Gammal implementation
result = await self.client.rest.get_wallets()

# Ny implementation
result = await self.client.rest.auth.get_wallets()
```

- [ ] Uppdatera `get_positions` metoden
```python
# Gammal implementation
result = await self.client.rest.get_active_positions()

# Ny implementation
result = await self.client.rest.auth.get_active_positions()
```

- [ ] Uppdatera övriga REST API-metoder på liknande sätt

### 2.3 Uppdatera WebSocket-händelser

- [ ] Uppdatera händelseregistrering
```python
# Gammal implementation
self.client.wss.on('connected', self._handle_ws_connected)
self.client.wss.on('disconnected', self._handle_ws_disconnected)
self.client.wss.on('error', self._handle_ws_error)
self.client.wss.on('authenticated', self._handle_ws_authenticated)
self.client.wss.on('auth_failed', self._handle_ws_auth_failed)

# Ny implementation
self.client.wss.on('open', self._handle_ws_connected)
# 'close' är inte tillgänglig som standard, hantera på annat sätt
self.client.wss.on('error', self._handle_ws_error)
# Registrera auth-händelser efter anslutning
```

### 2.4 Uppdatera WebSocket-anslutning

- [ ] Uppdatera anslutningsmetoder
```python
# Gammal implementation
await self.client.wss.connect()
await self.client.wss.authenticate()

# Ny implementation
await self.client.wss.open()
await self.client.wss.auth()
```

### 2.5 Uppdatera WebSocket-prenumerationer

- [ ] Uppdatera prenumerationsmetoder
```python
# Gammal implementation
await self.client.wss.subscribe(**params)

# Ny implementation
await self.client.wss.subscribe(**params)
# Samma metod, men hanteringen av svaret kan behöva uppdateras
```

## 3. Uppdatera beroende moduler

- [ ] Identifiera alla moduler som använder BitfinexClientWrapper
  - `backend/services/exchange.py`
  - `backend/services/websocket_user_data_service.py`
  - Andra moduler som importerar BitfinexClientWrapper

- [ ] Uppdatera anrop till ändrade metoder i dessa moduler

## 4. Testa implementationen

- [ ] Kör våra testskript för att verifiera att uppdateringen fungerar
  - `python scripts/testing/test_bitfinex_simple.py`
  - `python -m pytest backend/tests/test_bitfinex_client_wrapper.py -v`

- [ ] Testa både REST API och WebSocket-funktionalitet
  - Verifiera att ticker-data kan hämtas
  - Verifiera att orderbok-data kan hämtas
  - Verifiera att WebSocket-anslutning fungerar

## 5. Köra CI-kontroller

- [ ] Kör linting med `black` och `isort`
  - `python -m black backend/services/bitfinex_client_wrapper.py`
  - `python -m isort backend/services/bitfinex_client_wrapper.py`

- [ ] Kör enhetstester
  - `python -m pytest backend/tests/`

- [ ] Åtgärda eventuella linting-problem eller testfel

## 6. Git-commit

- [ ] Skapa en beskrivande commit-meddelande
  - Förklara uppdateringen av BitfinexClientWrapper
  - Inkludera referens till dokumentationen

- [ ] Commit-format:
  ```
  [API] Uppdatera BitfinexClientWrapper för att stödja Bitfinex API v3
  
  - Uppdaterade importer från bfxapi.websockets till bfxapi.websocket
  - Uppdaterade REST API-metoder för att använda nya strukturen
  - Uppdaterade WebSocket-händelser och anslutningsmetoder
  - Lade till dokumentation för uppdateringen
  ```

## 7. Dokumentation

- [ ] Uppdatera eventuell ytterligare dokumentation
  - README.md om den innehåller information om Bitfinex API
  - Utvecklardokumentation
  - API-dokumentation

## 8. Efterkontroll och verifiering

- [ ] Verifiera att alla tester passerar efter implementationen
- [ ] Verifiera att alla CI-kontroller passerar
- [ ] Verifiera att dokumentationen är uppdaterad och korrekt

## Tidsuppskattning

- Förberedelser och backup: 30 minuter
- Uppdatera BitfinexClientWrapper: 2-3 timmar
- Uppdatera beroende moduler: 1-2 timmar
- Testa implementationen: 1-2 timmar
- Köra CI-kontroller och åtgärda problem: 1 timme
- Git-commit och dokumentation: 30 minuter

Total uppskattad tid: 6-9 timmar 