/**
 * Optimized Market Data Hook - Centraliserad och Effektiv
 * 
 * Ersätter multipla overlapping polling-system med:
 * 1. Single source of truth för all marknadsdata
 * 2. Smart caching och rate limiting  
 * 3. Minimal API-anrop (max 1 per endpoint per 3-5 sekunder)
 * 4. Shared state mellan komponenter
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { api } from '@/lib/api';
import { OrderBook, OHLCVData, Balance, BotStatus, OrderHistoryItem, Trade, LogEntry } from '@/types/trading';

interface MarketTicker {
  symbol: string;
  price: number;
  bid?: number;
  ask?: number;
  volume: number;
  timestamp: string;
}

interface OptimizedMarketData {
  // Market data
  ticker: MarketTicker | null;
  orderbook: OrderBook | null;
  chartData: OHLCVData[];
  
  // Trading data  
  balances: Balance[];
  activeTrades: Trade[];
  orderHistory: OrderHistoryItem[];
  botStatus: BotStatus;
  logs: LogEntry[];
  
  // Status
  connected: boolean;
  lastUpdate: number | null;
  error: string | null;
  
  // Control
  refreshData: (force?: boolean) => Promise<void>;
  refreshSymbolData: (symbol: string) => Promise<void>;
}

// Global state management
class MarketDataManager {
  private static instance: MarketDataManager;
  private subscribers: Set<(data: OptimizedMarketData) => void> = new Set();
  private data: OptimizedMarketData = {
    ticker: null,
    orderbook: null,
    chartData: [],
    balances: [],
    activeTrades: [],
    orderHistory: [],
    botStatus: { status: 'stopped', uptime: 0, last_update: new Date().toISOString() },
    logs: [],
    connected: false,
    lastUpdate: null,
    error: null,
    refreshData: () => Promise.resolve(),
    refreshSymbolData: () => Promise.resolve()
  };
  
  private currentSymbol: string = 'BTCUSD';
  private lastFetch: Record<string, number> = {};
  private isPolling: boolean = false;
  private pollInterval: NodeJS.Timeout | null = null;
  
  public static getInstance(): MarketDataManager {
    if (!MarketDataManager.instance) {
      MarketDataManager.instance = new MarketDataManager();
    }
    return MarketDataManager.instance;
  }

  public subscribe(callback: (data: OptimizedMarketData) => void): () => void {
    this.subscribers.add(callback);
    
    // Send current data immediately
    callback(this.data);
    
    // Start polling if this is first subscriber
    if (this.subscribers.size === 1) {
      this.startPolling();
    }
    
    return () => {
      this.subscribers.delete(callback);
      // Stop polling if no more subscribers
      if (this.subscribers.size === 0) {
        this.stopPolling();
      }
    };
  }
  
  private notifySubscribers(): void {
    this.subscribers.forEach(callback => callback(this.data));
  }
  
  private shouldFetch(endpoint: string, minInterval: number): boolean {
    const now = Date.now();
    const lastFetch = this.lastFetch[endpoint] || 0;
    return (now - lastFetch) >= minInterval;
  }
  
  private markFetched(endpoint: string): void {
    this.lastFetch[endpoint] = Date.now();
  }

  public async refreshMarketData(symbol: string, force: boolean = false): Promise<void> {
    const MARKET_INTERVAL = 3000; // 3 seconds for market data
    
    try {
      const promises: Promise<void>[] = [];
      
      // Ticker data (high frequency)
      if (force || this.shouldFetch('ticker', MARKET_INTERVAL)) {
        promises.push(
          api.getMarketTicker(symbol)
            .then(ticker => {
              this.data.ticker = {
                symbol: ticker.symbol || symbol,
                price: ticker.last || ticker.price || 0,
                bid: ticker.bid,
                ask: ticker.ask,
                volume: ticker.volume || 0,
                timestamp: ticker.timestamp || new Date().toISOString()
              };
              this.markFetched('ticker');
            })
            .catch(() => null)
        );
      }
      
      // Orderbook data (medium frequency)
      if (force || this.shouldFetch('orderbook', MARKET_INTERVAL)) {
        promises.push(
          api.getOrderBook(symbol, 20)
            .then(orderbook => {
              this.data.orderbook = orderbook;
              this.markFetched('orderbook');
            })
            .catch(() => null)
        );
      }
      
      // Chart data (lower frequency - only when needed)
      if (force || this.shouldFetch('chart', 10000)) { // 10 seconds
        promises.push(
          api.getChartData(symbol, '5m', 100)
            .then(chartData => {
              this.data.chartData = chartData;
              this.markFetched('chart');
            })
            .catch(() => null)
        );
      }
      
      await Promise.all(promises);
      this.data.connected = true;
      this.data.error = null;
      
    } catch (error) {
      this.data.connected = false;
      this.data.error = error instanceof Error ? error.message : 'Market data fetch failed';
    }
  }

  public async refreshTradingData(force: boolean = false): Promise<void> {
    const TRADING_INTERVAL = 5000; // 5 seconds for trading data
    
    try {
      const promises: Promise<void>[] = [];
      
      // Balances (medium frequency)
      if (force || this.shouldFetch('balances', TRADING_INTERVAL)) {
        promises.push(
          api.getBalances()
            .then(balances => {
              this.data.balances = balances;
              this.markFetched('balances');
            })
            .catch(() => null)
        );
      }
      
      // Active trades (medium frequency)
      if (force || this.shouldFetch('trades', TRADING_INTERVAL)) {
        promises.push(
          api.getActiveTrades()
            .then(trades => {
              this.data.activeTrades = trades;
              this.markFetched('trades');
            })
            .catch(() => null)
        );
      }
      
      // Order history (lower frequency)
      if (force || this.shouldFetch('orders', 10000)) { // 10 seconds
        promises.push(
          api.getOrderHistory()
            .then(orders => {
              this.data.orderHistory = orders;
              this.markFetched('orders');
            })
            .catch(() => null)
        );
      }
      
      // Bot status (medium frequency)
      if (force || this.shouldFetch('status', 7000)) { // 7 seconds
        promises.push(
          api.getBotStatus()
            .then(status => {
              this.data.botStatus = status;
              this.markFetched('status');
            })
            .catch(() => null)
        );
      }
      
      // Logs (lower frequency)
      if (force || this.shouldFetch('logs', 15000)) { // 15 seconds
        promises.push(
          api.getLogs()
            .then(logs => {
              this.data.logs = logs;
              this.markFetched('logs');
            })
            .catch(() => null)
        );
      }
      
      await Promise.all(promises);
      
    } catch (error) {
      this.data.error = error instanceof Error ? error.message : 'Trading data fetch failed';
    }
  }

  public async refreshAll(symbol?: string, force: boolean = false): Promise<void> {
    if (symbol) {
      this.currentSymbol = symbol;
    }
    
    await Promise.all([
      this.refreshMarketData(this.currentSymbol, force),
      this.refreshTradingData(force)
    ]);
    
    this.data.lastUpdate = Date.now();
    this.notifySubscribers();
  }

  private startPolling(): void {
    if (this.isPolling) return;
    
    this.isPolling = true;
    console.log('🚀 [OptimizedMarketData] Starting efficient polling...');
    
    // Initial load
    this.refreshAll(this.currentSymbol, true);
    
    // Smart polling - staggered intervals
    this.pollInterval = setInterval(() => {
      this.refreshAll(this.currentSymbol);
    }, 3000); // Base interval: 3 seconds
  }
  
  private stopPolling(): void {
    if (!this.isPolling) return;
    
    this.isPolling = false;
    if (this.pollInterval) {
      clearInterval(this.pollInterval);
      this.pollInterval = null;
    }
    
    console.log('⏹️ [OptimizedMarketData] Stopped polling');
  }
  
  public setSymbol(symbol: string): void {
    if (symbol !== this.currentSymbol) {
      this.currentSymbol = symbol;
      // Force refresh market data for new symbol
      this.refreshMarketData(symbol, true).then(() => {
        this.notifySubscribers();
      });
    }
  }
}

/**
 * React Hook för optimerad marknadsdata
 * Centraliserar all data-fetching och eliminerar redundanta API-anrop
 */
export const useOptimizedMarketData = (symbol?: string): OptimizedMarketData => {
  const [data, setData] = useState<OptimizedMarketData>({
    ticker: null,
    orderbook: null,
    chartData: [],
    balances: [],
    activeTrades: [],
    orderHistory: [],
    botStatus: { status: 'stopped', uptime: 0, last_update: new Date().toISOString() },
    logs: [],
    connected: false,
    lastUpdate: null,
    error: null,
    refreshData: () => Promise.resolve(),
    refreshSymbolData: () => Promise.resolve()
  });
  
  const manager = MarketDataManager.getInstance();
  
  // Update symbol if provided
  useEffect(() => {
    if (symbol) {
      manager.setSymbol(symbol);
    }
  }, [symbol, manager]);
  
  // Subscribe to manager updates
  useEffect(() => {
    const unsubscribe = manager.subscribe(setData);
    return unsubscribe;
  }, [manager]);
  
  // Add control methods
  const refreshData = useCallback(async (force: boolean = false) => {
    await manager.refreshAll(symbol, force);
  }, [manager, symbol]);
  
  const refreshSymbolData = useCallback(async (targetSymbol: string) => {
    await manager.refreshMarketData(targetSymbol, true);
  }, [manager]);
  
  return {
    ...data,
    refreshData,
    refreshSymbolData
  };
};