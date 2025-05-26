
import { Balance, Trade, OrderHistoryItem, BotStatus, OrderBook, LogEntry, TradingConfig, OHLCVData } from '@/types/trading';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000';

// Mock data for development
const mockBalances: Balance[] = [
  { currency: 'USD', total_balance: 10000, available: 8500 },
  { currency: 'BTC', total_balance: 0.5, available: 0.3 },
  { currency: 'ETH', total_balance: 2.5, available: 2.0 }
];

const mockTrades: Trade[] = [
  {
    id: '1',
    symbol: 'BTCUSD',
    amount: 0.1,
    entry_price: 45000,
    pnl: 250.50,
    timestamp: '2024-01-15T10:30:00Z',
    side: 'buy'
  },
  {
    id: '2',
    symbol: 'ETHUSD',
    amount: 1.5,
    entry_price: 2800,
    pnl: -125.75,
    timestamp: '2024-01-15T09:15:00Z',
    side: 'buy'
  }
];

const mockOrderHistory: OrderHistoryItem[] = [
  {
    id: '1',
    symbol: 'BTCUSD',
    order_type: 'market',
    side: 'buy',
    amount: 0.1,
    price: 45000,
    fee: 2.25,
    timestamp: '2024-01-15T10:30:00Z',
    status: 'filled'
  },
  {
    id: '2',
    symbol: 'ETHUSD',
    order_type: 'limit',
    side: 'sell',
    amount: 0.5,
    price: 2850,
    fee: 0.71,
    timestamp: '2024-01-15T09:45:00Z',
    status: 'cancelled'
  }
];

const mockBotStatus: BotStatus = {
  status: 'running',
  uptime: 86400,
  last_update: new Date().toISOString()
};

const mockOrderBook: OrderBook = {
  symbol: 'BTCUSD',
  bids: [
    { price: 44995, amount: 0.5 },
    { price: 44990, amount: 1.2 },
    { price: 44985, amount: 0.8 },
    { price: 44980, amount: 2.1 },
    { price: 44975, amount: 0.3 }
  ],
  asks: [
    { price: 45005, amount: 0.7 },
    { price: 45010, amount: 1.1 },
    { price: 45015, amount: 0.9 },
    { price: 45020, amount: 1.8 },
    { price: 45025, amount: 0.4 }
  ]
};

const mockLogs: LogEntry[] = [
  { timestamp: '2024-01-15T10:35:00Z', level: 'info', message: 'Bot started successfully' },
  { timestamp: '2024-01-15T10:36:15Z', level: 'info', message: 'Market data connection established' },
  { timestamp: '2024-01-15T10:37:30Z', level: 'warning', message: 'High volatility detected' },
  { timestamp: '2024-01-15T10:38:45Z', level: 'info', message: 'Order placed: BUY 0.1 BTC @ $45000' },
  { timestamp: '2024-01-15T10:39:12Z', level: 'error', message: 'API rate limit exceeded, retrying...' }
];

const mockConfig: TradingConfig = {
  SYMBOL: 'BTCUSD',
  TIMEFRAME: '5m',
  EMA_LENGTH: 20,
  EMA_FAST: 12,
  EMA_SLOW: 26,
  RSI_PERIOD: 14,
  ATR_MULTIPLIER: 2.0,
  VOLUME_MULTIPLIER: 1.5,
  LOOKBACK: 100,
  TRADING_START_HOUR: 9,
  TRADING_END_HOUR: 17,
  STOP_LOSS_PERCENT: 2.0,
  TAKE_PROFIT_PERCENT: 4.0,
  MAX_TRADES_PER_DAY: 5,
  MAX_DAILY_LOSS: 500,
  RISK_PER_TRADE: 1.0,
  EMAIL_NOTIFICATIONS: true,
  EMAIL_SENDER: 'bot@trading.com',
  EMAIL_RECEIVER: 'trader@example.com',
  EMAIL_SMTP_SERVER: 'smtp.gmail.com',
  EMAIL_SMTP_PORT: 587
};

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
  // Bot Control
  async getBotStatus(): Promise<BotStatus> {
    // In production: return fetch(`${API_BASE_URL}/api/status`).then(r => r.json());
    return new Promise(resolve => setTimeout(() => resolve(mockBotStatus), 500));
  },

  async startBot(): Promise<{ success: boolean; message: string }> {
    // In production: return fetch(`${API_BASE_URL}/api/start-bot`, { method: 'POST' }).then(r => r.json());
    return new Promise(resolve => 
      setTimeout(() => resolve({ success: true, message: 'Bot started successfully' }), 1000)
    );
  },

  async stopBot(): Promise<{ success: boolean; message: string }> {
    // In production: return fetch(`${API_BASE_URL}/api/stop-bot`, { method: 'POST' }).then(r => r.json());
    return new Promise(resolve => 
      setTimeout(() => resolve({ success: true, message: 'Bot stopped successfully' }), 1000)
    );
  },

  // Trading Data
  async getBalances(): Promise<Balance[]> {
    // In production: return fetch(`${API_BASE_URL}/api/balances`).then(r => r.json());
    return new Promise(resolve => setTimeout(() => resolve(mockBalances), 300));
  },

  async getActiveTrades(): Promise<Trade[]> {
    // In production: return fetch(`${API_BASE_URL}/api/positions`).then(r => r.json());
    return new Promise(resolve => setTimeout(() => resolve(mockTrades), 300));
  },

  async getOrderHistory(): Promise<OrderHistoryItem[]> {
    // In production: return fetch(`${API_BASE_URL}/api/orders`).then(r => r.json());
    return new Promise(resolve => setTimeout(() => resolve(mockOrderHistory), 300));
  },

  async getOrderBook(symbol: string): Promise<OrderBook> {
    // In production: return fetch(`${API_BASE_URL}/api/orderbook/${symbol}`).then(r => r.json());
    return new Promise(resolve => setTimeout(() => resolve(mockOrderBook), 200));
  },

  async getLogs(): Promise<LogEntry[]> {
    // In production: return fetch(`${API_BASE_URL}/api/logs`).then(r => r.json());
    return new Promise(resolve => setTimeout(() => resolve(mockLogs), 200));
  },

  async getChartData(symbol: string): Promise<OHLCVData[]> {
    // In production: return fetch(`${API_BASE_URL}/api/chart/${symbol}`).then(r => r.json());
    return new Promise(resolve => setTimeout(() => resolve(generateMockOHLCVData()), 400));
  },

  // Configuration
  async getConfig(): Promise<TradingConfig> {
    // In production: return fetch(`${API_BASE_URL}/api/config`).then(r => r.json());
    return new Promise(resolve => setTimeout(() => resolve(mockConfig), 300));
  },

  async updateConfig(config: Partial<TradingConfig>): Promise<{ success: boolean; message: string }> {
    // In production: return fetch(`${API_BASE_URL}/api/config`, { method: 'POST', body: JSON.stringify(config) }).then(r => r.json());
    return new Promise(resolve => 
      setTimeout(() => resolve({ success: true, message: 'Configuration updated successfully' }), 800)
    );
  }
};
