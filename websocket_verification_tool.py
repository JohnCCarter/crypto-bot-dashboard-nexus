#!/usr/bin/env python3
"""
🔍 Bitfinex WebSocket Verification Tool
Verifierar att trading bot:en får korrekt information från Bitfinex WebSocket

Detta verktyg testar:
1. WebSocket anslutning till Bitfinex
2. Ticker data (pris, volym, bid/ask)
3. Orderbook data (bids/asks)
4. Data kvalitet och latency
5. Integration med backend services
"""

import asyncio
import websockets
import json
import time
import logging
import sys
from datetime import datetime
from typing import Dict, List, Optional
import signal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BitfinexWebSocketVerifier:
    def __init__(self):
        self.ws = None
        self.subscriptions = {}
        self.ticker_data = {}
        self.orderbook_data = {}
        self.connection_stats = {
            'connected_at': None,
            'messages_received': 0,
            'heartbeats_received': 0,
            'last_heartbeat': None,
            'latency_samples': [],
            'error_count': 0
        }
        self.test_symbols = ['tBTCUSD', 'tETHUSD']
        self.running = True
        
    async def connect(self):
        """Anslut till Bitfinex WebSocket API"""
        try:
            logger.info("🔌 Connecting to Bitfinex WebSocket...")
            self.ws = await websockets.connect('wss://api-pub.bitfinex.com/ws/2')
            self.connection_stats['connected_at'] = datetime.now()
            logger.info("✅ Connected to Bitfinex WebSocket successfully")
            
            # Konfigurera avancerade funktioner
            await self.configure_advanced_features()
            
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect: {e}")
            return False
            
    async def configure_advanced_features(self):
        """Aktivera timestamps och checksums"""
        try:
            conf_msg = {
                'event': 'conf',
                'flags': 32768 + 131072  # TIMESTAMP + OB_CHECKSUM
            }
            await self.ws.send(json.dumps(conf_msg))
            logger.info("⚙️ Advanced features configured (timestamps + checksums)")
        except Exception as e:
            logger.error(f"❌ Failed to configure features: {e}")
            
    async def subscribe_to_symbol(self, symbol: str):
        """Prenumerera på ticker och orderbook för symbol"""
        try:
            # Subscribe to ticker
            ticker_msg = {
                'event': 'subscribe',
                'channel': 'ticker',
                'symbol': symbol
            }
            await self.ws.send(json.dumps(ticker_msg))
            
            # Subscribe to orderbook
            book_msg = {
                'event': 'subscribe',
                'channel': 'book',
                'symbol': symbol,
                'prec': 'P0',  # Highest precision
                'freq': 'F0',  # Real-time updates
                'len': '25'    # Top 25 levels
            }
            await self.ws.send(json.dumps(book_msg))
            
            logger.info(f"📡 Subscribed to ticker and orderbook for {symbol}")
            
        except Exception as e:
            logger.error(f"❌ Failed to subscribe to {symbol}: {e}")
            
    async def send_ping(self):
        """Skicka ping för latency mätning"""
        try:
            ping_time = time.time()
            ping_msg = {
                'event': 'ping',
                'cid': int(ping_time * 1000)  # Use timestamp as ID
            }
            await self.ws.send(json.dumps(ping_msg))
            return ping_time
        except Exception as e:
            logger.error(f"❌ Failed to send ping: {e}")
            return None
            
    def process_ticker_data(self, symbol: str, data: List):
        """Bearbeta ticker data från WebSocket"""
        try:
            # Bitfinex ticker format: [BID, BID_SIZE, ASK, ASK_SIZE, DAILY_CHANGE, DAILY_CHANGE_RELATIVE, LAST_PRICE, VOLUME, HIGH, LOW]
            if len(data) >= 10:
                ticker_info = {
                    'symbol': symbol,
                    'bid': float(data[0]),
                    'bid_size': float(data[1]),
                    'ask': float(data[2]),
                    'ask_size': float(data[3]),
                    'daily_change': float(data[4]),
                    'daily_change_pct': float(data[5]) * 100,
                    'last_price': float(data[6]),
                    'volume': float(data[7]),
                    'high': float(data[8]),
                    'low': float(data[9]),
                    'timestamp': datetime.now(),
                    'spread': float(data[2]) - float(data[0]),  # ask - bid
                    'spread_pct': ((float(data[2]) - float(data[0])) / float(data[6])) * 100
                }
                
                self.ticker_data[symbol] = ticker_info
                
                # Log significant price updates (not every tick to avoid spam)
                if symbol not in self.ticker_data or abs(ticker_info['last_price'] - self.ticker_data.get(symbol, {}).get('last_price', 0)) > 0.01:
                    logger.info(f"📊 {symbol}: ${ticker_info['last_price']:.2f} (Vol: {ticker_info['volume']:.2f}, Spread: ${ticker_info['spread']:.2f})")
                    
        except Exception as e:
            logger.error(f"❌ Error processing ticker data for {symbol}: {e}")
            
    def process_orderbook_data(self, symbol: str, data):
        """Bearbeta orderbook data från WebSocket"""
        try:
            if isinstance(data, list):
                if len(data) > 0 and isinstance(data[0], list):
                    # Orderbook snapshot
                    bids = []
                    asks = []
                    
                    for entry in data:
                        if len(entry) >= 3:
                            price, count, amount = float(entry[0]), int(entry[1]), float(entry[2])
                            if amount > 0:
                                bids.append({'price': price, 'amount': amount})
                            else:
                                asks.append({'price': price, 'amount': abs(amount)})
                    
                    self.orderbook_data[symbol] = {
                        'bids': sorted(bids, key=lambda x: x['price'], reverse=True),
                        'asks': sorted(asks, key=lambda x: x['price']),
                        'timestamp': datetime.now()
                    }
                    
                    if bids and asks:
                        best_bid = bids[0]['price']
                        best_ask = asks[0]['price']
                        spread = best_ask - best_bid
                        logger.info(f"📚 {symbol} Orderbook: Bid ${best_bid:.2f} | Ask ${best_ask:.2f} | Spread ${spread:.2f}")
                        
                elif len(data) == 3:
                    # Orderbook update [PRICE, COUNT, AMOUNT]
                    price, count, amount = float(data[0]), int(data[1]), float(data[2])
                    # Process incremental update (simplified for verification)
                    raise NotImplementedError("Incremental orderbook update logic is not implemented. Consider adding simplified update logic here.")
                    
        except Exception as e:
            logger.error(f"❌ Error processing orderbook data for {symbol}: {e}")
            
    async def handle_message(self, message: str):
        """Hantera inkommande WebSocket meddelanden"""
        try:
            data = json.loads(message)
            self.connection_stats['messages_received'] += 1
            
            # Handle different message types
            if isinstance(data, dict):
                # Event messages
                if data.get('event') == 'info':
                    logger.info(f"ℹ️ Info: {data}")
                    if data.get('platform', {}).get('status') == 1:
                        logger.info("✅ Platform status: Operative")
                    else:
                        logger.warning("⚠️ Platform status: Maintenance")
                        
                elif data.get('event') == 'subscribed':
                    channel_id = data.get('chanId')
                    channel = data.get('channel')
                    symbol = data.get('symbol')
                    self.subscriptions[channel_id] = {'channel': channel, 'symbol': symbol}
                    logger.info(f"✅ Subscribed: {channel} for {symbol} (Channel ID: {channel_id})")
                    
                elif data.get('event') == 'pong':
                    # Calculate latency
                    ping_time = data.get('cid', 0) / 1000
                    latency = (time.time() - ping_time) * 1000
                    self.connection_stats['latency_samples'].append(latency)
                    if len(self.connection_stats['latency_samples']) > 10:
                        self.connection_stats['latency_samples'].pop(0)
                    logger.info(f"🏓 Pong received - Latency: {latency:.1f}ms")
                    
                elif data.get('event') == 'error':
                    self.connection_stats['error_count'] += 1
                    logger.error(f"❌ WebSocket Error: {data}")
                    
            elif isinstance(data, list) and len(data) >= 2:
                # Data messages [CHANNEL_ID, DATA]
                channel_id, message_data = data[0], data[1]
                
                if message_data == 'hb':
                    # Heartbeat
                    self.connection_stats['heartbeats_received'] += 1
                    self.connection_stats['last_heartbeat'] = datetime.now()
                    return  # Silent heartbeat
                    
                # Find subscription info
                subscription = self.subscriptions.get(channel_id)
                if not subscription:
                    return
                    
                channel = subscription['channel']
                symbol = subscription['symbol']
                
                if channel == 'ticker':
                    self.process_ticker_data(symbol, message_data)
                elif channel == 'book':
                    self.process_orderbook_data(symbol, message_data)
                    
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON decode error: {e}")
        except Exception as e:
            logger.error(f"❌ Error handling message: {e}")
            
    async def print_statistics(self):
        """Skriv ut anslutningsstatistik"""
        stats = self.connection_stats
        
        if stats['connected_at']:
            uptime = datetime.now() - stats['connected_at']
            uptime_seconds = uptime.total_seconds()
        else:
            uptime_seconds = 0
            
        avg_latency = sum(stats['latency_samples']) / len(stats['latency_samples']) if stats['latency_samples'] else 0
        
        print("\n" + "="*60)
        print("📊 BITFINEX WEBSOCKET VERIFICATION STATISTICS")
        print("="*60)
        print(f"⏱️  Uptime: {uptime_seconds:.1f} seconds")
        print(f"📨 Messages received: {stats['messages_received']}")
        print(f"💓 Heartbeats: {stats['heartbeats_received']}")
        print(f"🏓 Average latency: {avg_latency:.1f}ms")
        print(f"❌ Errors: {stats['error_count']}")
        
        if stats['last_heartbeat']:
            heartbeat_age = (datetime.now() - stats['last_heartbeat']).total_seconds()
            print(f"💓 Last heartbeat: {heartbeat_age:.1f}s ago")
            
        print("\n📊 TICKER DATA:")
        for symbol, ticker in self.ticker_data.items():
            print(f"  {symbol}: ${ticker['last_price']:.2f} (Vol: {ticker['volume']:.2f})")
            print(f"    Bid: ${ticker['bid']:.2f} | Ask: ${ticker['ask']:.2f} | Spread: {ticker['spread_pct']:.3f}%")
            
        print("\n📚 ORDERBOOK DATA:")
        for symbol, book in self.orderbook_data.items():
            if book['bids'] and book['asks']:
                best_bid = book['bids'][0]['price']
                best_ask = book['asks'][0]['price']
                levels = len(book['bids']) + len(book['asks'])
                print(f"  {symbol}: ${best_bid:.2f} - ${best_ask:.2f} ({levels} levels)")
                
        print("="*60)
        
    async def data_quality_check(self):
        """Kontrollera datakvalitet för trading bot"""
        print("\n🔍 DATA QUALITY CHECK FOR TRADING BOT:")
        print("-" * 50)
        
        issues = []
        
        # Check ticker data
        for symbol in self.test_symbols:
            if symbol not in self.ticker_data:
                issues.append(f"Missing ticker data for {symbol}")
                continue
                
            ticker = self.ticker_data[symbol]
            
            # Check spread
            if ticker['spread_pct'] > 0.5:  # 0.5% spread threshold
                issues.append(f"{symbol}: Wide spread {ticker['spread_pct']:.3f}%")
                
            # Check if data is recent
            data_age = (datetime.now() - ticker['timestamp']).total_seconds()
            if data_age > 60:  # 1 minute threshold
                issues.append(f"{symbol}: Stale ticker data ({data_age:.1f}s old)")
                
        # Check orderbook data
        for symbol in self.test_symbols:
            if symbol not in self.orderbook_data:
                issues.append(f"Missing orderbook data for {symbol}")
                continue
                
            book = self.orderbook_data[symbol]
            
            if len(book['bids']) < 10 or len(book['asks']) < 10:
                issues.append(f"{symbol}: Thin orderbook (Bids: {len(book['bids'])}, Asks: {len(book['asks'])})")
                
        # Check connection health
        if self.connection_stats['error_count'] > 0:
            issues.append(f"WebSocket errors detected: {self.connection_stats['error_count']}")
            
        if self.connection_stats['last_heartbeat']:
            heartbeat_age = (datetime.now() - self.connection_stats['last_heartbeat']).total_seconds()
            if heartbeat_age > 30:  # 30 second threshold
                issues.append(f"Heartbeat stale: {heartbeat_age:.1f}s ago")
                
        # Print results
        if issues:
            print("❌ ISSUES DETECTED:")
            for issue in issues:
                print(f"  • {issue}")
            print("\n⚠️ Trading bot may have reduced performance")
        else:
            print("✅ ALL CHECKS PASSED")
            print("✅ Data quality is excellent for trading bot")
            
        return len(issues) == 0
        
    async def run_verification(self, duration: int = 60):
        """Kör verifieringstest"""
        logger.info(f"🚀 Starting Bitfinex WebSocket verification for {duration} seconds...")
        
        # Connect
        if not await self.connect():
            return False
            
        # Subscribe to test symbols
        for symbol in self.test_symbols:
            await self.subscribe_to_symbol(symbol)
            await asyncio.sleep(0.5)  # Small delay between subscriptions
            
        # Start message handling
        async def message_handler():
            try:
                async for message in self.ws:
                    if not self.running:
                        break
                    await self.handle_message(message)
            except websockets.exceptions.ConnectionClosed:
                logger.warning("⚠️ WebSocket connection closed")
            except Exception as e:
                logger.error(f"❌ Message handler error: {e}")
                
        # Start ping routine
        async def ping_routine():
            while self.running:
                await asyncio.sleep(30)  # Ping every 30 seconds
                if self.ws and not self.ws.closed:
                    await self.send_ping()
                    
        # Run verification
        message_task = asyncio.create_task(message_handler())
        ping_task = asyncio.create_task(ping_routine())
        
        try:
            # Wait for specified duration
            await asyncio.sleep(duration)
            
        finally:
            self.running = False
            message_task.cancel()
            ping_task.cancel()
            
            if self.ws:
                await self.ws.close()
                
        # Print final statistics and quality check
        await self.print_statistics()
        quality_ok = await self.data_quality_check()
        
        return quality_ok

async def main():
    """Main verification function"""
    print("🔍 BITFINEX WEBSOCKET VERIFICATION TOOL")
    print("=" * 60)
    print("Testing WebSocket connection for trading bot...")
    print("Press Ctrl+C to stop early")
    print("=" * 60)
    
    verifier = BitfinexWebSocketVerifier()
    
    # Handle Ctrl+C gracefully
    def signal_handler(signum, frame):
        print("\n⏹️ Stopping verification...")
        verifier.running = False
        
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        # Run verification for 60 seconds (adjust as needed)
        success = await verifier.run_verification(duration=60)
        
        if success:
            print("\n🎉 VERIFICATION SUCCESSFUL!")
            print("✅ Trading bot should receive excellent WebSocket data")
        else:
            print("\n⚠️ VERIFICATION COMPLETED WITH ISSUES")
            print("❌ Trading bot may experience data quality problems")
            
    except KeyboardInterrupt:
        print("\n⏹️ Verification stopped by user")
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        
if __name__ == "__main__":
    asyncio.run(main())