/**
 * React hook för marknadsdata via Backend WebSocket Proxy
 * Använder backend som proxy istället för direkta Bitfinex WebSocket
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { OrderBook } from '@/types/trading';
import { logger } from '../utils/logger';

interface MarketData {
  symbol: string;
  price: number;
  volume: number;
  bid?: number;
  ask?: number;
  timestamp: string;
}

interface Trade {
  id: string;
  timestamp: number;
  amount: number;
  price: number;
}

interface WebSocketMarketData {
  // Live ticker data
  ticker: MarketData | null;
  
  // Live orderbook
  orderbook: OrderBook | null;
  
  // Recent trades
  trades: Trade[];
  
  // Connection status
  connected: boolean;
  connecting: boolean;
  
  // Platform status
  platformStatus: 'operative' | 'maintenance' | 'unknown';
  
  // Error state
  error: string | null;
  
  // Control functions
  connect: () => void;
  disconnect: () => void;
  subscribeToSymbol: (symbol: string) => void;
  unsubscribeFromSymbol: (symbol: string) => void;
  
  // Connection quality
  lastHeartbeat: number | null;
  latency: number | null;
}

/**
 * Hook för att hantera marknadsdata via Backend WebSocket Proxy
 * Ersätter direkta Bitfinex WebSocket med säker backend-proxy
 */
export const useWebSocketMarket = (initialSymbol: string = 'BTCUSD'): WebSocketMarketData => {
  const [ticker, setTicker] = useState<MarketData | null>(null);
  const [orderbook, setOrderbook] = useState<OrderBook | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [platformStatus, setPlatformStatus] = useState<'operative' | 'maintenance' | 'unknown'>('unknown');
  const [error, setError] = useState<string | null>(null);
  const [lastHeartbeat, setLastHeartbeat] = useState<number | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  
  const currentSymbol = useRef<string>(initialSymbol);
  const pollInterval = useRef<NodeJS.Timeout | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const isActive = useRef<boolean>(false);

  // Fetch ticker data from backend WebSocket proxy
  const fetchTickerData = useCallback(async () => {
    try {
      const response = await fetch('/api/ws-proxy/ticker', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (response.ok) {
        const tickerData = await response.json();
        
        // Map backend ticker format to our format
        setTicker({
          symbol: tickerData.symbol || currentSymbol.current,
          price: tickerData.price || 0,
          volume: tickerData.volume || 0,
          bid: tickerData.bid,
          ask: tickerData.ask,
          timestamp: new Date().toISOString()
        });
        
        setLastHeartbeat(Date.now());
        setError(null);
        
                 if (!connected) {
           setConnected(true);
           setConnecting(false);
           setPlatformStatus('operative');
           console.log('✅ [WS-Proxy] Connected to backend WebSocket proxy');
         }
      } else {
        throw new Error(`Backend ticker API returned ${response.status}`);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      
             if (connected) {
         setConnected(false);
         setError(`Backend WebSocket proxy error: ${errorMsg}`);
         console.error(`❌ [WS-Proxy] Error: ${errorMsg}`);
       }
    }
  }, [connected, currentSymbol]);

  // Check backend WebSocket proxy status
  const checkProxyStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/ws-proxy/status');
      
      if (response.ok) {
        const status = await response.json();
        
        if (status.connected && status.has_ticker_data) {
          setPlatformStatus('operative');
          setError(null);
          
                     if (!connected) {
             setConnected(true);
             setConnecting(false);
             console.log('✅ [WS-Proxy] Backend WebSocket proxy is operational');
           }
        } else {
          setConnected(false);
          setError('Backend WebSocket proxy not connected to Bitfinex');
          setPlatformStatus('maintenance');
        }
        
        if (status.last_heartbeat) {
          setLastHeartbeat(status.last_heartbeat * 1000); // Convert to milliseconds
        }
      } else {
        throw new Error(`Proxy status API returned ${response.status}`);
      }
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setConnected(false);
      setError(`Cannot reach backend WebSocket proxy: ${errorMsg}`);
      setPlatformStatus('unknown');
    }
  }, [connected]);

  // Fetch orderbook data (fallback to REST API)
  const fetchOrderbookData = useCallback(async () => {
    try {
      const symbol = currentSymbol.current;
      const response = await fetch(`/api/market/orderbook/${symbol}?limit=20`);
      
      if (response.ok) {
        const orderbookData = await response.json();
        
        setOrderbook({
          symbol: symbol,
          bids: orderbookData.bids || [],
          asks: orderbookData.asks || []
        });
      }
         } catch (err) {
       // Silent fallback - orderbook är inte kritisk
       console.warn('⚠️ [WS-Proxy] Could not fetch orderbook data');
     }
  }, [currentSymbol]);

  // Main polling function
  const poll = useCallback(async () => {
    if (!isActive.current) return;
    
    await Promise.all([
      fetchTickerData(),
      checkProxyStatus(),
      fetchOrderbookData()
    ]);
  }, [fetchTickerData, checkProxyStatus, fetchOrderbookData]);

  // Connect to backend WebSocket proxy
  const connect = useCallback(() => {
    if (isActive.current) {
      return; // Already connecting/connected
    }

    setConnecting(true);
    setError(null);
    isActive.current = true;
    
         console.log('🔄 [WS-Proxy] Connecting to backend WebSocket proxy...');

    // Initial check
    poll();
    
    // Start polling every 2 seconds for real-time feel
    pollInterval.current = setInterval(poll, 2000);
    
  }, [poll]);

  // Disconnect from backend WebSocket proxy  
  const disconnect = useCallback(() => {
    isActive.current = false;
    
    if (pollInterval.current) {
      clearInterval(pollInterval.current);
      pollInterval.current = null;
    }
    
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    setConnected(false);
    setConnecting(false);
    setPlatformStatus('unknown');
    setError(null);
    
         console.log('🔌 [WS-Proxy] Disconnected from backend WebSocket proxy');
  }, []);

  // Subscribe to symbol (just update current symbol for REST calls)
  const subscribeToSymbol = useCallback((symbol: string) => {
    currentSymbol.current = symbol;
         console.log(`📡 [WS-Proxy] Switched to symbol: ${symbol}`);
    
    // Immediate poll for new symbol
    if (isActive.current) {
      poll();
    }
  }, [poll]);

  // Unsubscribe is a no-op for REST polling
  const unsubscribeFromSymbol = useCallback((symbol: string) => {
         console.log(`📡 [WS-Proxy] Unsubscribed from: ${symbol}`);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();
    
    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  // Calculate latency based on fetch times
  useEffect(() => {
    if (connected) {
      const start = Date.now();
      fetch('/api/ws-proxy/status')
        .then(() => {
          const latencyMs = Date.now() - start;
          setLatency(latencyMs);
        })
        .catch(() => {
          // Silent - latency measurement failed
        });
    }
  }, [connected, ticker]); // Re-measure on each ticker update

  return {
    ticker,
    orderbook,
    trades,
    connected,
    connecting,
    platformStatus,
    error,
    connect,
    disconnect,
    subscribeToSymbol,
    unsubscribeFromSymbol,
    lastHeartbeat,
    latency
  };
};