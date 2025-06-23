#!/usr/bin/env python3
"""
🚀 Minimal Flask Backend for Trading Dashboard
Provides basic API endpoints without complex dependencies
"""

from flask import Flask, jsonify
from flask_cors import CORS
import json
from datetime import datetime
import random

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=["http://localhost:8081", "http://localhost:3000", "http://127.0.0.1:8081"])

# Mock data
MOCK_BALANCES = [
    {"currency": "BTC", "total_balance": 1.234567, "available": 1.100000},
    {"currency": "ETH", "total_balance": 10.567890, "available": 9.500000},
    {"currency": "USD", "total_balance": 15420.50, "available": 12000.00}
]

MOCK_TRADES = [
    {
        "id": "trade_1",
        "symbol": "BTC/USD",
        "side": "buy",
        "amount": 0.1,
        "price": 45000.0,
        "timestamp": "2024-06-23T08:00:00Z",
        "status": "completed"
    },
    {
        "id": "trade_2", 
        "symbol": "ETH/USD",
        "side": "sell",
        "amount": 2.5,
        "price": 3200.0,
        "timestamp": "2024-06-23T07:30:00Z",
        "status": "completed"
    }
]

@app.route("/api/status", methods=["GET"])
def get_status():
    """API status endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "message": "Trading Bot API is running"
    })

@app.route("/api/balances", methods=["GET"])
def get_balances():
    """Get account balances"""
    return jsonify(MOCK_BALANCES)

@app.route("/api/trades", methods=["GET"])
def get_trades():
    """Get trade history"""
    return jsonify(MOCK_TRADES)

@app.route("/api/orderbook/<symbol>", methods=["GET"])
def get_orderbook(symbol):
    """Get orderbook for symbol"""
    # Generate mock orderbook data
    bids = [[45000 - i*10, random.uniform(0.1, 2.0)] for i in range(10)]
    asks = [[45000 + i*10, random.uniform(0.1, 2.0)] for i in range(10)]
    
    return jsonify({
        "symbol": symbol,
        "bids": bids,
        "asks": asks,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/market/ticker/<symbol>", methods=["GET"])
def get_ticker(symbol):
    """Get ticker data for symbol"""
    base_price = 45000 if "BTC" in symbol else 3200
    return jsonify({
        "symbol": symbol,
        "price": base_price + random.uniform(-100, 100),
        "change_24h": random.uniform(-5, 5),
        "volume_24h": random.uniform(1000, 10000),
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/chart/<symbol>", methods=["GET"])
def get_chart_data(symbol):
    """Get chart data for symbol"""
    # Generate mock OHLCV data
    base_price = 45000 if "BTC" in symbol else 3200
    data = []
    
    for i in range(100):
        timestamp = datetime.now().timestamp() - (100-i) * 3600  # Hourly data
        open_price = base_price + random.uniform(-500, 500)
        high = open_price + random.uniform(0, 200)
        low = open_price - random.uniform(0, 200)
        close = open_price + random.uniform(-100, 100)
        volume = random.uniform(10, 100)
        
        data.append({
            "timestamp": int(timestamp * 1000),
            "open": round(open_price, 2),
            "high": round(high, 2),
            "low": round(low, 2),
            "close": round(close, 2),
            "volume": round(volume, 4)
        })
    
    return jsonify(data)

@app.route("/api/bot-status", methods=["GET"])
def get_bot_status():
    """Get trading bot status"""
    return jsonify({
        "status": "running",
        "uptime": "2h 15m",
        "last_update": datetime.now().isoformat(),
        "active_trades": 2,
        "total_pnl": 1250.50
    })

@app.route("/api/positions", methods=["GET"])
def get_positions():
    """Get open positions"""
    return jsonify([
        {
            "symbol": "BTC/USD",
            "side": "long",
            "size": 0.5,
            "entry_price": 44800.0,
            "current_price": 45000.0,
            "pnl": 100.0,
            "pnl_pct": 0.45
        }
    ])

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    print("🚀 Starting Minimal Trading Bot Backend...")
    print("📊 Available endpoints:")
    print("   - GET /api/status")
    print("   - GET /api/balances") 
    print("   - GET /api/trades")
    print("   - GET /api/orderbook/<symbol>")
    print("   - GET /api/market/ticker/<symbol>")
    print("   - GET /api/chart/<symbol>")
    print("   - GET /api/bot-status")
    print("   - GET /api/positions")
    print("")
    print("🌐 Frontend URL: http://localhost:8081")
    print("🔧 Backend URL: http://localhost:5000")
    
    app.run(host="0.0.0.0", port=5000, debug=True)