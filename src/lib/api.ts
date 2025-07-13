import { Balance, BotStatus, EmaCrossoverBacktestResult, LogEntry, MarketData, OHLCVData, OrderBook, OrderHistoryItem, Trade, TradingConfig } from '@/types/trading';

// Use Vite proxy instead of direct backend connection
// In development: requests go to '/api/*' which Vite proxies to http://127.0.0.1:8001
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
    position_type?: string;
  }): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order),
    });
    
    if (!res.ok) {
      const errorData: { error?: string; message?: string } = await res.json().catch(() => ({}));
      throw new Error(errorData.error || errorData.message || 'Failed to place order');
    }
    
    return await res.json();
  },

  // Get Config (Live)
  async getConfig(): Promise<TradingConfig> {
    const res = await fetch(`${API_BASE_URL}/api/config`);
    
    if (!res.ok) throw new Error('Failed to fetch config');
    return await res.json();
  },

  // Update Config (Live)
  async updateConfig(config: Partial<TradingConfig>): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/config`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(config),
    });
    
    if (!res.ok) throw new Error('Failed to update config');
    return await res.json();
  },

  // Get Balances (Live)
  async getBalances(): Promise<Balance[]> {
    const res = await fetch(`${API_BASE_URL}/api/balances`);
    
    if (!res.ok) throw new Error('Failed to fetch balances');
    const data = await res.json();
    return data.balances || [];
  },

  // Get Active Trades (Live)
  async getActiveTrades(): Promise<Trade[]> {
    const res = await fetch(`${API_BASE_URL}/api/positions`);
    
    if (!res.ok) throw new Error('Failed to fetch trades');
    const data = await res.json();
    return data.positions || [];
  },

  // Get Chart Data (Live Bitfinex)
  async getChartData(symbol: string, timeframe: string = '5m', limit: number = 100): Promise<OHLCVData[]> {
    const res = await fetch(`${API_BASE_URL}/api/market/ohlcv/${symbol}?timeframe=${timeframe}&limit=${limit}`);
    
    if (!res.ok) {
      return generateMockOHLCVData();
    }
    
    const liveData = await res.json();
    return liveData;
  },

  // Get Order Book (Live Bitfinex)
  async getOrderBook(symbol: string, limit: number = 20): Promise<OrderBook> {
    const res = await fetch(`${API_BASE_URL}/api/orderbook/${symbol}?limit=${limit}`);
    if (!res.ok) {
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
    return liveOrderbook;
  },

  // Get Market Ticker (Live Bitfinex)
  async getMarketTicker(symbol: string): Promise<MarketData> {
    const res = await fetch(`${API_BASE_URL}/api/market/ticker/${symbol}`);
    if (!res.ok) {
      throw new Error('Failed to fetch ticker');
    }
    const ticker = await res.json();
    return ticker;
  },

  // Get Available Markets (Live Bitfinex)
  async getAvailableMarkets(): Promise<{ markets: string[] }> {
    const res = await fetch(`${API_BASE_URL}/api/market/markets`);
    if (!res.ok) {
      throw new Error('Failed to fetch markets');
    }
    const markets = await res.json();
    return markets;
  },

  // Bot control endpoints
  async startBot(): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/start-bot`, { method: 'POST' });
    
    if (!res.ok) throw new Error('Failed to start bot');
    return await res.json();
  },

  async stopBot(): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/stop-bot`, { method: 'POST' });
    
    if (!res.ok) throw new Error('Failed to stop bot');
    return await res.json();
  },

  async getBotStatus(): Promise<BotStatus> {
    const res = await fetch(`${API_BASE_URL}/api/bot-status`);
    
    if (!res.ok) throw new Error('Failed to fetch bot status');
    return await res.json();
  },

  // Run Backtest (EMA Crossover)
  async runBacktestEmaCrossover(
    data: { timestamp: number[]; open: number[]; high: number[]; low: number[]; close: number[]; volume: number[] },
    parameters: Record<string, unknown> = {}
  ): Promise<EmaCrossoverBacktestResult> {
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
        const errorBody: { error?: string; error_type?: string; timestamp?: string } = await res.json();
        if (errorBody.error) {
          errorDetails = `${errorBody.error}`;
          if (errorBody.error_type) {
            errorDetails += ` (Type: ${errorBody.error_type})`;
          }
          if (errorBody.timestamp) {
            errorDetails += ` [${errorBody.timestamp}]`;
          }
        }
      } catch {
        // Failed to parse error response - use default error
      }
      throw new Error(`Backtest failed: ${errorDetails}`);
    }
    const result = await res.json();
    return result;
  },

  // Get Order History (Live) - Combines history + open orders
  async getOrderHistory(): Promise<OrderHistoryItem[]> {
    try {
      // Fetch both order history and open orders
      const [historyRes, openOrdersRes] = await Promise.all([
        fetch(`${API_BASE_URL}/api/orders/history`),
        fetch(`${API_BASE_URL}/api/orders`)
      ]);
      
      const history = historyRes.ok ? await historyRes.json() : [];
      const openOrdersData = openOrdersRes.ok ? await openOrdersRes.json() : { orders: [] };
      const openOrders = openOrdersData.orders || [];
      
      // Combine and sort by timestamp (newest first)
      const allOrders = [...history, ...openOrders].sort((a, b) => 
        (b.timestamp || 0) - (a.timestamp || 0)
      );
      
      return allOrders;
    } catch (error) {
      console.error('Failed to fetch order history:', error);
      return [];
    }
  },

  // Get Logs (From TradingLogger)
  async getLogs(): Promise<LogEntry[]> {
    // Import TradingLogger and return its logs with compatible types
    const { logger } = await import('@/utils/logger');
    const tradingLogs = logger.getLogs();
    
    // Map TradingLogger levels to compatible LogEntry levels
    return tradingLogs.map(log => ({
      timestamp: log.timestamp,
      level: log.level === 'success' ? 'info' : 
             log.level === 'status' ? 'info' : 
             log.level as 'error', // error maps directly
      message: log.message
    }));
  },

  // Cancel Order (Live)
  async cancelOrder(orderId: string): Promise<{ success: boolean; message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/orders/${orderId}`, {
      method: 'DELETE',
    });
    if (!res.ok) throw new Error('Failed to cancel order');
    return await res.json();
  }
};