#!/bin/bash

# Performance Test Script för Trading Bot
echo "🚀 Performance Testing - Trading Bot"
echo "====================================="

# Test 1: Backend WebSocket Proxy Response Time
echo "📊 Testing Backend WebSocket Proxy..."
echo "Status endpoint:"
time curl -s http://localhost:5000/api/ws-proxy/status | jq '.'

echo -e "\nTicker endpoint:"
time curl -s http://localhost:5000/api/ws-proxy/ticker | jq '.'

# Test 2: API Response Times
echo -e "\n📈 Testing API Endpoints..."
echo "Status API:"
time curl -s http://localhost:5000/api/status | jq '.status'

echo -e "\nTicker API:"
time curl -s http://localhost:5000/api/market/ticker/BTCUSD | jq '.last'

# Test 3: Memory Usage Check
echo -e "\n💾 Memory Usage Check..."
if command -v ps &> /dev/null; then
    echo "Python processes memory usage:"
    ps aux | grep python | grep -v grep | awk '{print $2, $4, $11}' | head -5
fi

# Test 4: API Rate Test
echo -e "\n⚡ API Rate Test (5 calls)..."
for i in {1..5}; do
    echo "Call $i:"
    time curl -s http://localhost:5000/api/ws-proxy/ticker > /dev/null
    sleep 0.5
done

echo -e "\n✅ Performance test completed!"
echo "🎯 Recommendations:"
echo "   - Backend API calls should be < 100ms"
echo "   - WebSocket proxy should be < 50ms"  
echo "   - Memory usage should be stable"
echo "   - Rate limiting should prevent excessive calls"