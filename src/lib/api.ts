import { Balance, BotStatus, EmaCrossoverBacktestResult, LogEntry, OHLCVData, OrderBook, OrderHistoryItem, Trade, TradingConfig } from '@/types/trading';

const API_BASE_URL = 'http://localhost:5000';

// Generate mock OHLCV data
const generateMockOHLCVData = (): OHLCVData[] => {
  const data: OHLCVData[] = [];
  const now = Date.now();
  let basePrice = 45000;

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
  }): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE_URL}/api/orders`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(order),
    });
    if (!res.ok) throw new Error('Order failed');
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
    return await res.json();
  },

  // Get Active Trades (Live)
  async getActiveTrades(): Promise<Trade[]> {
    const res = await fetch(`${API_BASE_URL}/api/positions`);
    if (!res.ok) throw new Error('Failed to fetch trades');
    return await res.json();
  },

  // Get Chart Data (Mock)
  async getChartData(symbol: string): Promise<OHLCVData[]> {
    return new Promise(resolve => setTimeout(() => resolve(generateMockOHLCVData()), 400));
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

  async runBacktestEmaCrossover(
    data: { timestamp: number[]; open: number[]; high: number[]; low: number[]; close: number[]; volume: number[] },
    parameters: any = {}
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
    if (!res.ok) throw new Error('Backtest failed');
    return await res.json();
  },

  // Get Order History (Live)
  async getOrderHistory(): Promise<OrderHistoryItem[]> {
    const res = await fetch(`${API_BASE_URL}/api/orders/history`);
    if (!res.ok) throw new Error('Failed to fetch order history');
    return await res.json();
  },

  // Get Order Book (Mock)
  async getOrderBook(symbol: string): Promise<OrderBook> {
    // Returnera mockad orderbok
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
  },

  // Get Logs (Mock)
  async getLogs(): Promise<LogEntry[]> {
    // Returnera mockade loggar
    return [
      { timestamp: new Date().toISOString(), level: 'info', message: 'Bot started' },
      { timestamp: new Date().toISOString(), level: 'error', message: 'Test error' }
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