#!/usr/bin/env python3
"""
Test script för Bitfinex Authenticated WebSocket Service
Baserat på din Go-kod och Bitfinex dokumentation
"""

import asyncio
import os
import logging
from backend.services.authenticated_websocket_service import BitfinexAuthenticatedWebSocket

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_authenticated_websocket():
    """Test authenticated WebSocket connection och data retrieval."""
    
    api_key = os.getenv("BITFINEX_API_KEY")
    api_secret = os.getenv("BITFINEX_API_SECRET")
    
    if not api_key or not api_secret:
        logger.error("❌ BITFINEX_API_KEY och BITFINEX_API_SECRET måste sättas som environment variables")
        return False
    
    if "placeholder" in api_key or "your_" in api_key:
        logger.error("❌ Placeholder API keys detected. Sätt riktiga Bitfinex API keys.")
        return False
    
    logger.info("🔐 Testing Bitfinex Authenticated WebSocket...")
    logger.info(f"API Key: {api_key[:8]}...")
    
    try:
        # Skapa authenticated WebSocket client
        client = BitfinexAuthenticatedWebSocket(api_key, api_secret)
        
        # Setup callbacks för account data
        def wallet_callback(wallets):
            logger.info(f"💰 WALLET UPDATE: {len(wallets)} wallets received")
            for wallet_key, wallet in wallets.items():
                if wallet['balance'] > 0:
                    logger.info(f"  - {wallet['type']} {wallet['currency']}: {wallet['balance']} (available: {wallet['available']})")
        
        def position_callback(positions):
            logger.info(f"📊 POSITION UPDATE: {len(positions)} positions received")
            for pos in positions:
                if pos['amount'] != 0:
                    logger.info(f"  - {pos['symbol']}: {pos['amount']} @ {pos['base_price']} (PnL: {pos['pl']})")
        
        def order_callback(orders):
            logger.info(f"📋 ORDER UPDATE: {len(orders)} orders received")
            for order in orders:
                logger.info(f"  - {order['symbol']}: {order['type']} {order['amount']} @ {order['price']} ({order['status']})")
        
        def trade_callback(trades):
            logger.info(f"💱 TRADE UPDATE: {len(trades)} trades received")
            for trade in trades[-3:]:  # Visa senaste 3 trades
                logger.info(f"  - {trade['symbol']}: {trade['exec_amount']} @ {trade['exec_price']} (fee: {trade['fee']})")
        
        # Sätt callbacks
        client.set_wallet_callback(wallet_callback)
        client.set_position_callback(position_callback)
        client.set_order_callback(order_callback)
        client.set_trade_callback(trade_callback)
        
        # Anslut till WebSocket
        await client.connect()
        
        # Vänta på authentication och initial data
        logger.info("⏳ Waiting for authentication...")
        for i in range(30):  # Vänta max 30 sekunder
            if client.authenticated:
                logger.info("✅ Authentication successful!")
                break
            await asyncio.sleep(1)
        else:
            logger.error("❌ Authentication timed out")
            return False
        
        # Vänta på initial account data
        logger.info("⏳ Waiting for initial account data...")
        await asyncio.sleep(5)
        
        # Testa data retrieval
        logger.info("\n📊 TESTING DATA RETRIEVAL:")
        
        # Test wallets
        wallets = client.get_wallets()
        logger.info(f"💰 Wallets: {len(wallets)} total")
        total_value = 0
        for wallet_key, wallet in wallets.items():
            if wallet['balance'] > 0:
                logger.info(f"  - {wallet['type']} {wallet['currency']}: {wallet['balance']} (available: {wallet['available']})")
                if wallet['currency'] in ['USD', 'TESTUSD']:
                    total_value += wallet['balance']
        
        logger.info(f"💰 Total USD Value: ${total_value:.2f}")
        
        # Test positions
        positions = client.get_positions()
        logger.info(f"📊 Positions: {len(positions)} total")
        for pos in positions:
            if pos['amount'] != 0:
                logger.info(f"  - {pos['symbol']}: {pos['amount']} @ {pos['base_price']} (PnL: ${pos['pl']:.2f})")
        
        # Test orders
        orders = client.get_orders()
        logger.info(f"📋 Orders: {len(orders)} total")
        for order in orders:
            logger.info(f"  - {order['symbol']}: {order['type']} {order['amount']} @ ${order['price']} ({order['status']})")
        
        # Test trade history
        trades = client.get_trade_history()
        logger.info(f"💱 Trade History: {len(trades)} total")
        for trade in trades[-3:]:  # Senaste 3 trades
            logger.info(f"  - {trade['symbol']}: {trade['exec_amount']} @ ${trade['exec_price']} (fee: ${trade['fee']})")
        
        # Låt WebSocket köra lite till för att få mer data
        logger.info("\n⏳ Listening for real-time updates for 10 seconds...")
        await asyncio.sleep(10)
        
        # Disconnect
        await client.disconnect()
        logger.info("🔌 Disconnected successfully")
        
        # Final verification
        logger.info("\n✅ TEST RESULTS:")
        logger.info(f"  - Authentication: ✅ Success")
        logger.info(f"  - Wallets: ✅ {len(wallets)} received")
        logger.info(f"  - Positions: ✅ {len(positions)} received")
        logger.info(f"  - Orders: ✅ {len(orders)} received")
        logger.info(f"  - Trades: ✅ {len(trades)} received")
        
        if len(wallets) > 0:
            logger.info("🎉 AUTHENTICATED WEBSOCKET TEST PASSED!")
            return True
        else:
            logger.warning("⚠️ No wallet data received - check API permissions")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

async def main():
    """Main test function."""
    logger.info("🚀 Starting Bitfinex Authenticated WebSocket Test")
    logger.info("Baserat på: https://bitfinex.readthedocs.io/en/latest/websocket.html")
    
    success = await test_authenticated_websocket()
    
    if success:
        logger.info("🎉 ALL TESTS PASSED!")
        logger.info("✅ Authenticated WebSocket service är redo för production")
    else:
        logger.error("❌ TESTS FAILED!")
        logger.error("Kontrollera API keys och permissions")
    
    return success

if __name__ == "__main__":
    asyncio.run(main())