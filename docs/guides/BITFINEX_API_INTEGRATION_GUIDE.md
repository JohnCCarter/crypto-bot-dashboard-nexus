# 🔌 Bitfinex API Integration Guide

Detta dokument beskriver hur man använder den nya `BitfinexClientWrapper`-klassen för att interagera med Bitfinex API på ett mer robust och effektivt sätt.

## 📋 Översikt

`BitfinexClientWrapper` är en wrapper runt det officiella Bitfinex API Python-biblioteket som ger följande fördelar:

- Enklare hantering av både REST och WebSocket API
- Bättre felhantering och återanslutningslogik
- Konsekvent gränssnitt för alla API-anrop
- Stöd för både synkrona och asynkrona anrop

## 🛠️ Installation

Biblioteket installeras automatiskt när du installerar projektets beroenden:

```bash
pip install -r backend/requirements.txt
```

## 🚀 Användning

### Grundläggande användning

```python
from backend.services.bitfinex_client_wrapper import BitfinexClientWrapper

# Skapa en klient
client = BitfinexClientWrapper(
    api_key="din_api_nyckel",
    api_secret="din_api_hemlighet",
    use_rest_auth=True  # Sätt till False för att endast använda publika API:er
)

# Hämta ticker-information
ticker_result = client.get_ticker("tBTCUSD")
if ticker_result["status"] == "success":
    ticker = ticker_result["ticker"]
    print(f"BTC/USD: Bid: {ticker[0]}, Ask: {ticker[2]}, Last: {ticker[6]}")
```

### REST API-anrop

Följande REST API-funktioner finns tillgängliga:

#### Marknadsdata

```python
# Hämta ticker
ticker_result = client.get_ticker("tBTCUSD")

# Hämta orderbok
book_result = client.get_order_book("tBTCUSD", precision="P0", length=25)
```

#### Orderhantering

```python
# Skapa en order (köp 0.01 BTC till pris 30000 USD)
order_result = client.place_order(
    symbol="tBTCUSD",
    amount=0.01,  # Positivt för köp, negativt för sälj
    price=30000,
    order_type="LIMIT"  # "LIMIT" eller "MARKET"
)

# Hämta orderstatus
status_result = client.get_order_status(order_id=123456)

# Avbryt en order
cancel_result = client.cancel_order(order_id=123456)

# Hämta aktiva order
orders_result = client.get_active_orders()
```

#### Konto och positioner

```python
# Hämta plånbokssaldon
balances_result = client.get_wallet_balances()

# Hämta aktiva positioner
positions_result = client.get_positions()
```

### WebSocket API

WebSocket API:et ger realtidsuppdateringar för marknadsdata och kontoaktivitet:

```python
# Anslut till WebSocket
client.connect_websocket()

# Registrera en callback för ticker-uppdateringar
def handle_ticker(ticker_data):
    print(f"Ticker-uppdatering: {ticker_data}")

client.register_ws_callback("ticker", handle_ticker)

# Prenumerera på ticker-kanalen för BTC/USD
client.subscribe_to_channel("ticker", "tBTCUSD")

# När du är klar, koppla från
client.disconnect_websocket()
```

## 🔄 Integration med befintlig kod

`BitfinexClientWrapper` är integrerad med `ExchangeService` och `BitfinexUserDataClient` för att ge en sömlös övergång från den tidigare implementationen:

### ExchangeService

`ExchangeService` använder nu `BitfinexClientWrapper` för Bitfinex-specifika anrop, men behåller CCXT som fallback för kompatibilitet:

```python
from backend.services.exchange import ExchangeService

# Skapa en exchange service
exchange = ExchangeService(
    exchange_id="bitfinex",
    api_key="din_api_nyckel",
    api_secret="din_api_hemlighet"
)

# Använder automatiskt BitfinexClientWrapper för Bitfinex
order = exchange.create_order(
    symbol="BTC/USD",
    order_type="limit",
    side="buy",
    amount=0.01,
    price=30000
)
```

### BitfinexUserDataClient

`BitfinexUserDataClient` använder nu `BitfinexClientWrapper` för WebSocket-hantering:

```python
from backend.services.websocket_user_data_service import BitfinexUserDataClient

# Skapa en klient
client = BitfinexUserDataClient(
    api_key="din_api_nyckel",
    api_secret="din_api_hemlighet"
)

# Anslut till WebSocket (använder BitfinexClientWrapper internt)
await client.connect()

# Registrera callbacks
await client.subscribe_orders(handle_order_update)
await client.subscribe_balances(handle_balance_update)
```

## 🧪 Testning

För att testa integrationen finns följande verktyg:

1. **Enhetstester**: `python -m pytest backend/tests/test_bitfinex_client_wrapper.py`
2. **Manuellt testskript**: `python scripts/testing/test_bitfinex_integration.py`

## 🔍 Felsökning

### Vanliga problem

1. **API-nycklar saknas eller är ogiltiga**
   - Kontrollera att API-nycklar är korrekt konfigurerade
   - Verifiera att API-nycklar har rätt behörigheter

2. **WebSocket-anslutningsproblem**
   - Kontrollera nätverksanslutning
   - Verifiera att WebSocket-protokollet inte blockeras av brandvägg

3. **Nonce-fel**
   - Wrapper-klassen hanterar nonce automatiskt, men om du får nonce-fel, kontakta utvecklarna

### Loggning

För att aktivera detaljerad loggning:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📝 Anteckningar

- Denna implementation är bakåtkompatibel med den tidigare koden
- Prestandan bör vara bättre, särskilt för WebSocket-anslutningar
- Felhanteringen är mer robust med automatisk återanslutning 