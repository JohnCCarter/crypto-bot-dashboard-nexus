export interface Balance {
  currency: string;
  total_balance: number;
  available: number;
}

export interface Trade {
  id: string;
  symbol: string;
  amount: number;
  entry_price: number;
  pnl: number;
  timestamp: string;
  side: 'buy' | 'sell';
}

export interface OrderHistoryItem {
  id: string;
  symbol: string;
  order_type: 'market' | 'limit';
  side: 'buy' | 'sell';
  amount: number;
  price: number;
  fee: number;
  timestamp: string;
  status: 'filled' | 'cancelled' | 'pending';
}

export interface BotStatus {
  status: 'running' | 'stopped' | 'error';
  uptime: number;
  last_update: string;
}

export interface OrderBookEntry {
  price: number;
  amount: number;
}

export interface OrderBook {
  bids: OrderBookEntry[];
  asks: OrderBookEntry[];
  symbol: string;
}

export interface LogEntry {
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'debug';
  message: string;
}

export interface OHLCVData {
  timestamp: number;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface TradingConfig {
  // Strategy Settings
  SYMBOL: string;
  TIMEFRAME: string;
  EMA_LENGTH: number;
  EMA_FAST: number;
  EMA_SLOW: number;
  RSI_PERIOD: number;
  ATR_MULTIPLIER: number;
  VOLUME_MULTIPLIER: number;
  LOOKBACK: number;
  
  // Time & Risk Management
  TRADING_START_HOUR: number;
  TRADING_END_HOUR: number;
  STOP_LOSS_PERCENT: number;
  TAKE_PROFIT_PERCENT: number;
  MAX_TRADES_PER_DAY: number;
  MAX_DAILY_LOSS: number;
  RISK_PER_TRADE: number;
  
  // Email Notifications
  EMAIL_NOTIFICATIONS: boolean;
  EMAIL_SENDER: string;
  EMAIL_RECEIVER: string;
  EMAIL_SMTP_SERVER: string;
  EMAIL_SMTP_PORT: number;
}

export interface EmaCrossoverSignal {
  index: number;
  type: 'buy' | 'sell';
}

export interface EmaCrossoverBacktestResult {
  ema_fast: number[];
  ema_slow: number[];
  signals: EmaCrossoverSignal[];
  signal_result: any;
  // Lägg till övriga fält från backtest vid behov
  [key: string]: any;
}
