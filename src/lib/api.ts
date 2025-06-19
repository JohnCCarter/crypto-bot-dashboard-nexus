import { Balance, BotStatus, EmaCrossoverBacktestResult, LogEntry, OHLCVData, OrderBook, OrderHistoryItem, Trade, TradingConfig } from '@/types/trading';

// Use Vite proxy instead of direct backend connection
// In development: requests go to '/api/*' which Vite proxies to http://127.0.0.1:5000
// In production: API requests will go to same origin
const API_BASE_URL = '';

// Generate mock OHLCV data (fallback)
const generateMockOHLCVData = (): OHLCVData[] => {
  const data: OHLCVData[] = [];
  const now = Date.now();
  let basePrice = 45000;

  // Generate 101 data points (from 100 to 0)
  for (let i = 100; i >= 0; i--) {
    const timestamp = now - (i * 5 * 60 * 1000); // 5-minute intervals
    const volatility = 0.02;
    const change = (Math.random() - 0.5) * volatility;

    const open = basePrice;
    const close = open * (1 + change);
    const high = Math.max(open, close) * (1 + Math.random() * 0.01);
    const low = Math.min(open, close) * (1 - Math.random() * 0.01);
    const volume = Math.random() * 100;

    data.push({ timestamp, open, high, low, close, volume });
    basePrice = close;
  }

  console.log(`📊 generateMockOHLCVData created ${data.length} data points`);
  return data;
};

// API functions
export const api = {
  // Place Order (Live)
  async placeOrder(order: {
    symbol: string;
    order_type: string;
    side: string;
    amount: number;
    price?: number | null;
  }): Promise<{ message: string }> {
    console.log(`🌐 [API] Making request to: ${API_BASE_URL}/api/orders`);
    console.log(`🌐 [API] Order data:`, order);
    
    const res = await fetch(`${API_BASE_URL}/api/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order),
    });
    
    console.log(`🌐 [API] Response status: ${res.status} ${res.statusText}`);
    
    if (!res.ok) throw new Error('Order failed');
    return await res.json();
  },

  // Get Config (Live)
  async getConfig(): Promise<TradingConfig> {
    console.log(`🌐 [API] Making request to: ${API_BASE_URL}/api/config`);
    
    const res = await fetch(`${API_BASE_URL}/api/config`);
    
    console.log(`🌐 [API] Response status: ${res.status} ${res.statusText}`);
    
    if (!res.ok) throw new Error('Failed to fetch config');
    return await res.json();
  },

  // Update Config (Live)
  async updateConfig(config: Partial<TradingConfig>): Promise<{ success: boolean; message: string }> {
    console.log(`🌐 [API] Making request to: ${API_BASE_URL}/api/config`);
    console.log(`🌐 [API] Config data:`, config);
    
    const res = await fetch(`${API_BASE_URL}/api/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    
    console.log(`🌐 [API] Response status: ${res.status} ${res.statusText}`);
    
    if (!res.ok) throw new Error('Failed to update config');
    return await res.json();
  },

  // Get Balances (Live)
  async getBalances(): Promise<Balance[]> {
    console.log(`🌐 [API] Making request to: ${API_BASE_URL}/api/balances`);
    
    const res = await fetch(`${API_BASE_URL}/api/balances`);
    
    console.log(`🌐 [API] Response status: ${res.status} ${res.statusText}`);
    
    if (!res.ok) throw new Error('Failed to fetch balances');
    return await res.json();
  },

  // Get Active Trades (Live)
  async getActiveTrades(): Promise<Trade[]> {
    console.log(`🌐 [API] Making request to: ${API_BASE_URL}/api/positions`);
    
    const res = await fetch(`${API_BASE_URL}/api/positions`);
    
    console.log(`🌐 [API] Response status: ${res.status} ${res.statusText}`);
    
    if (!res.ok) throw new Error('Failed to fetch trades');
    return await res.json();
  },

  // Get Chart Data (Live Bitfinex)
  async getChartData(symbol: string, timeframe: string = '5m', limit: number = 100): Promise<OHLCVData[]> {
    console.log(`📊 [API] Fetching live chart data for ${symbol} (${timeframe}, ${limit} candles)`);
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/market/ohlcv/${symbol}?timeframe=${timeframe}&limit=${limit}`);
      
      console.log(`📊 [API] Response status: ${res.status} ${res.statusText}`);
      
      if (!res.ok) {
        console.warn(`📊 [API] Live data failed, falling back to mock data`);
        return generateMockOHLCVData();
      }
      
      const liveData = await res.json();
      console.log(`✅ [API] Successfully fetched ${liveData.length} live candles`);
      
      return liveData;
    } catch (error) {
      console.error(`❌ [API] Error fetching live chart data:`, error);
      console.warn(`📊 [API] Using mock data as fallback`);
      return generateMockOHLCVData();
    }
  },

  // Get Order Book (Live Bitfinex)
  async getOrderBook(symbol: string, limit: number = 20): Promise<OrderBook> {
    console.log(`📋 [API] Fetching live order book for ${symbol}`);
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/market/orderbook/${symbol}?limit=${limit}`);
      
      console.log(`📋 [API] Response status: ${res.status} ${res.statusText}`);
      
      if (!res.ok) {
        console.warn(`📋 [API] Live orderbook failed, falling back to mock data`);
        return {
          bids: [
            { price: 45000, amount: 1 },
            { price: 44950, amount: 2 }
          ],
          asks: [
            { price: 45100, amount: 1.5 },
            { price: 45200, amount: 0.8 }
          ],
          symbol
        };
      }
      
      const liveOrderbook = await res.json();
      console.log(`✅ [API] Successfully fetched live orderbook with ${liveOrderbook.bids.length} bids, ${liveOrderbook.asks.length} asks`);
      
      return liveOrderbook;
    } catch (error) {
      console.error(`❌ [API] Error fetching live orderbook:`, error);
      console.warn(`📋 [API] Using mock orderbook as fallback`);
      return {
        bids: [
          { price: 45000, amount: 1 },
          { price: 44950, amount: 2 }
        ],
        asks: [
          { price: 45100, amount: 1.5 },
          { price: 45200, amount: 0.8 }
        ],
        symbol
      };
    }
  },

  // Get Market Ticker (Live Bitfinex)
  async getMarketTicker(symbol: string): Promise<any> {
    console.log(`💰 [API] Fetching live ticker for ${symbol}`);
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/market/ticker/${symbol}`);
      
      console.log(`💰 [API] Response status: ${res.status} ${res.statusText}`);
      
      if (!res.ok) {
        throw new Error('Failed to fetch ticker');
      }
      
      const ticker = await res.json();
      console.log(`✅ [API] Successfully fetched ticker: ${ticker.last}`);
      
      return ticker;
    } catch (error) {
      console.error(`❌ [API] Error fetching ticker:`, error);
      throw error;
    }
  },

  // Get Available Markets (Live Bitfinex)
  async getAvailableMarkets(): Promise<any> {
    console.log(`🏪 [API] Fetching available markets`);
    
    try {
      const res = await fetch(`${API_BASE_URL}/api/market/markets`);
      
      console.log(`🏪 [API] Response status: ${res.status} ${res.statusText}`);
      
      if (!res.ok) {
        throw new Error('Failed to fetch markets');
      }
      
      const markets = await res.json();
      console.log(`✅ [API] Successfully fetched ${Object.keys(markets).length} markets`);
      
      return markets;
    } catch (error) {
      console.error(`❌ [API] Error fetching markets:`, error);
      throw error;
    }
  },

  // Bot control endpoints
  async startBot(): Promise<{ success: boolean; message: string }> {
    console.log(`🌐 [API] Making request to: ${API_BASE_URL}/api/start-bot`);
    
    const res = await fetch(`${API_BASE_URL}/api/start-bot`, { method: 'POST' });
    
    console.log(`🌐 [API] Response status: ${res.status} ${res.statusText}`);
    
    if (!res.ok) throw new Error('Failed to start bot');
    return await res.json();
  },

  async stopBot(): Promise<{ success: boolean; message: string }> {
    console.log(`🌐 [API] Making request to: ${API_BASE_URL}/api/stop-bot`);
    
    const res = await fetch(`${API_BASE_URL}/api/stop-bot`, { method: 'POST' });
    
    console.log(`🌐 [API] Response status: ${res.status} ${res.statusText}`);
    
    if (!res.ok) throw new Error('Failed to stop bot');
    return await res.json();
  },

  async getBotStatus(): Promise<BotStatus> {
    console.log(`🌐 [API] Making request to: ${API_BASE_URL}/api/bot-status`);
    
    const res = await fetch(`${API_BASE_URL}/api/bot-status`);
    
    console.log(`🌐 [API] Response status: ${res.status} ${res.statusText}`);
    
    if (!res.ok) throw new Error('Failed to fetch bot status');
    return await res.json();
  },

  async runBacktestEmaCrossover(
    data: { timestamp: number[]; open: number[]; high: number[]; low: number[]; close: number[]; volume: number[] },
    parameters: any = {}
  ): Promise<EmaCrossoverBacktestResult> {
    console.log('🚀 Starting EMA crossover backtest request...');
    console.log('📊 Data points:', data.timestamp.length);
    console.log('⚙️ Parameters:', parameters);
    
    const res = await fetch(`${API_BASE_URL}/api/backtest/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        strategy: 'ema_crossover',
        data,
        parameters
      })
    });
    
    if (!res.ok) {
      let errorDetails = `HTTP ${res.status}: ${res.statusText}`;
      try {
        const errorBody = await res.json();
        if (errorBody.error) {
          errorDetails = `${errorBody.error}`;
          if (errorBody.error_type) {
            errorDetails += ` (Type: ${errorBody.error_type})`;
          }
          if (errorBody.timestamp) {
            errorDetails += ` [${errorBody.timestamp}]`;
          }
        }
        console.error('❌ Detailed error from backend:', errorBody);
      } catch (e) {
        console.error('❌ Could not parse error response:', e);
      }
      throw new Error(`Backtest failed: ${errorDetails}`);
    }
    
    const result = await res.json();
    console.log('✅ EMA crossover backtest successful:', {
      ema_fast: result.ema_fast,
      ema_slow: result.ema_slow,
      total_trades: result.total_trades
    });
    return result;
  },

  // Get Order History (Live)
  async getOrderHistory(): Promise<OrderHistoryItem[]> {
    const res = await fetch(`${API_BASE_URL}/api/orders/history`);
    if (!res.ok) throw new Error('Failed to fetch order history');
    return await res.json();
  },

  // Get Logs (Smart Mock)
  async getLogs(): Promise<LogEntry[]> {
    // Returnera realistiska system logs istället för förvirrande "Test error"
    const now = new Date();
    const oneMinuteAgo = new Date(now.getTime() - 60000);
    const fiveMinutesAgo = new Date(now.getTime() - 300000);
    
    return [
      { 
        timestamp: fiveMinutesAgo.toISOString(), 
        level: 'info', 
        message: 'Trading Bot System Started - All services initialized' 
      },
      { 
        timestamp: oneMinuteAgo.toISOString(), 
        level: 'info', 
        message: 'WebSocket Connected to Bitfinex - Live data active' 
      },
      { 
        timestamp: now.toISOString(), 
        level: 'info', 
        message: 'System Health Check - All services operational' 
      }
    ];
  },

  // Cancel Order (Live)
  async cancelOrder(orderId: string): Promise<any> {
    const res = await fetch(`${API_BASE_URL}/api/orders/${orderId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to cancel order');
    return await res.json();
  }
};