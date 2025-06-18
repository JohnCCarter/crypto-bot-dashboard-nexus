/**
 * React hook för WebSocket marknadsdata från Bitfinex
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { OrderBook } from '@/types/trading';

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

interface BitfinexTickerData {
  symbol: string;
  price: number;
  volume: number;
  bid: number;
  ask: number;
  timestamp: string;
}

interface BitfinexOrderbookData {
  symbol: string;
  bids?: Array<{ price: number; amount: number }>;
  asks?: Array<{ price: number; amount: number }>;
  update?: {
    price: number;
    amount: number;
    side: 'bid' | 'ask';
  };
  timestamp: string;
}

interface BitfinexTradeData {
  symbol: string;
  trades: Trade[];
  timestamp: string;
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
  
  // Error state
  error: string | null;
  
  // Control functions
  connect: () => void;
  disconnect: () => void;
  subscribeToSymbol: (symbol: string) => void;
  unsubscribeFromSymbol: (symbol: string) => void;
}

/**
 * Hook för att hantera WebSocket marknadsdata
 */
export const useWebSocketMarket = (initialSymbol: string = 'BTCUSD'): WebSocketMarketData => {
  const [ticker, setTicker] = useState<MarketData | null>(null);
  const [orderbook, setOrderbook] = useState<OrderBook | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const ws = useRef<WebSocket | null>(null);
  const subscriptions = useRef<Set<string>>(new Set());
  const currentSymbol = useRef<string>(initialSymbol);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef<number>(0);
  const maxReconnectAttempts = 5;

  // WebSocket message handlers
  const handleTickerUpdate = useCallback((data: BitfinexTickerData) => {
    console.log('📊 [WS] Ticker update:', data);
    setTicker({
      symbol: data.symbol,
      price: data.price,
      volume: data.volume,
      bid: data.bid,
      ask: data.ask,
      timestamp: data.timestamp
    });
  }, []);

  const handleOrderbookUpdate = useCallback((data: BitfinexOrderbookData) => {
    console.log('📚 [WS] Orderbook update:', data);
    
    if (data.update) {
      // Incremental update
      setOrderbook(prev => {
        if (!prev) return null;
        
        const newOrderbook = { ...prev };
        const { price, amount, side } = data.update!;
        
        if (side === 'bid') {
          // Update bids
          const bidIndex = newOrderbook.bids.findIndex(bid => bid.price === price);
          if (amount === 0) {
            // Remove level
            if (bidIndex !== -1) {
              newOrderbook.bids.splice(bidIndex, 1);
            }
          } else {
            // Update or add level
            if (bidIndex !== -1) {
              newOrderbook.bids[bidIndex].amount = amount;
            } else {
              newOrderbook.bids.push({ price, amount });
              newOrderbook.bids.sort((a, b) => b.price - a.price); // Sort descending
            }
          }
        } else {
          // Update asks
          const askIndex = newOrderbook.asks.findIndex(ask => ask.price === price);
          if (amount === 0) {
            // Remove level
            if (askIndex !== -1) {
              newOrderbook.asks.splice(askIndex, 1);
            }
          } else {
            // Update or add level
            if (askIndex !== -1) {
              newOrderbook.asks[askIndex].amount = amount;
            } else {
              newOrderbook.asks.push({ price, amount });
              newOrderbook.asks.sort((a, b) => a.price - b.price); // Sort ascending
            }
          }
        }
        
        return newOrderbook;
      });
    } else {
      // Full snapshot
      setOrderbook({
        symbol: data.symbol,
        bids: data.bids ? data.bids.sort((a, b) => b.price - a.price) : [],
        asks: data.asks ? data.asks.sort((a, b) => a.price - b.price) : []
      });
    }
  }, []);

  const handleTradeUpdate = useCallback((data: BitfinexTradeData) => {
    console.log('💱 [WS] Trade update:', data);
    
    if (data.trades && Array.isArray(data.trades)) {
      setTrades(prev => {
        // Add new trades and keep only latest 100
        const newTrades = [...data.trades, ...prev];
        return newTrades.slice(0, 100);
      });
    }
  }, []);

  // Connect to WebSocket
  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      console.log('🔄 [WS] Already connected');
      return;
    }

    setConnecting(true);
    setError(null);

    try {
      // Bitfinex WebSocket API
      ws.current = new WebSocket('wss://api-pub.bitfinex.com/ws/2');

      ws.current.onopen = () => {
        console.log('✅ [WS] Connected to Bitfinex');
        setConnected(true);
        setConnecting(false);
        setError(null);
        reconnectAttempts.current = 0;

        // Subscribe to initial symbol
        subscribeToSymbol(currentSymbol.current);
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle different message types
          if (Array.isArray(data) && data.length >= 2) {
            const [channelId, messageData] = data;
            
            // Skip heartbeat messages
            if (messageData === 'hb') return;
            
            // Route messages based on subscription type
            // This is a simplified routing - in production you'd track channel IDs
            if (Array.isArray(messageData) && messageData.length >= 10) {
              // Ticker data format
              handleTickerUpdate({
                symbol: currentSymbol.current,
                price: messageData[6], // LAST_PRICE
                volume: messageData[7], // VOLUME  
                bid: messageData[0], // BID
                ask: messageData[2], // ASK
                timestamp: new Date().toISOString()
              });
            } else if (Array.isArray(messageData) && Array.isArray(messageData[0])) {
              // Orderbook snapshot
              const bids: Array<{ price: number; amount: number }> = [];
              const asks: Array<{ price: number; amount: number }> = [];
              
              messageData.forEach((entry: number[]) => {
                const [price, count, amount] = entry;
                if (amount > 0) {
                  bids.push({ price, amount });
                } else {
                  asks.push({ price, amount: Math.abs(amount) });
                }
              });
              
              handleOrderbookUpdate({
                symbol: currentSymbol.current,
                bids,
                asks,
                timestamp: new Date().toISOString()
              });
            }
          } else if (data.event === 'subscribed') {
            console.log(`✅ [WS] Subscribed to ${data.channel}:${data.symbol}`);
          } else if (data.event === 'error') {
            console.error('❌ [WS] Subscription error:', data);
            setError(`Subscription error: ${data.msg}`);
          }
        } catch (e) {
          console.error('❌ [WS] Message parsing error:', e);
        }
      };

      ws.current.onclose = (event) => {
        console.log('🔌 [WS] Disconnected:', event.code, event.reason);
        setConnected(false);
        setConnecting(false);

        // Attempt reconnection if not a clean close
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
          console.log(`🔄 [WS] Reconnecting in ${delay}ms (attempt ${reconnectAttempts.current + 1}/${maxReconnectAttempts})`);
          
          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setError('Max reconnection attempts reached');
        }
      };

      ws.current.onerror = (error) => {
        console.error('❌ [WS] WebSocket error:', error);
        setError('WebSocket connection error');
        setConnecting(false);
      };

    } catch (error) {
      console.error('❌ [WS] Failed to create WebSocket:', error);
      setError('Failed to create WebSocket connection');
      setConnecting(false);
    }
  }, [handleTickerUpdate, handleOrderbookUpdate, handleTradeUpdate]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) {
      clearTimeout(reconnectTimeout.current);
      reconnectTimeout.current = null;
    }

    if (ws.current) {
      ws.current.close(1000, 'User initiated disconnect');
      ws.current = null;
    }

    setConnected(false);
    setConnecting(false);
    subscriptions.current.clear();
  }, []);

  // Subscribe to symbol
  const subscribeToSymbol = useCallback((symbol: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      console.warn('⚠️ [WS] Cannot subscribe - not connected');
      return;
    }

    const bitfinexSymbol = symbol.startsWith('t') ? symbol : `t${symbol}`;
    currentSymbol.current = symbol;

    // Subscribe to ticker
    const tickerMsg = {
      event: 'subscribe',
      channel: 'ticker',
      symbol: bitfinexSymbol
    };

    // Subscribe to orderbook
    const bookMsg = {
      event: 'subscribe', 
      channel: 'book',
      symbol: bitfinexSymbol,
      prec: 'P0',
      freq: 'F0',
      len: '25'
    };

    try {
      ws.current.send(JSON.stringify(tickerMsg));
      ws.current.send(JSON.stringify(bookMsg));
      
      subscriptions.current.add(symbol);
      console.log(`📡 [WS] Subscribing to ${symbol}`);
    } catch (error) {
      console.error('❌ [WS] Failed to send subscription:', error);
      setError('Failed to subscribe to symbol');
    }
  }, []);

  // Unsubscribe from symbol
  const unsubscribeFromSymbol = useCallback((symbol: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      return;
    }

    // Bitfinex doesn't have a direct unsubscribe - would need to track channel IDs
    // For now, just remove from our tracking
    subscriptions.current.delete(symbol);
    console.log(`📡 [WS] Unsubscribed from ${symbol}`);
  }, []);

  // Auto-connect on mount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    ticker,
    orderbook,
    trades,
    connected,
    connecting,
    error,
    connect,
    disconnect,
    subscribeToSymbol,
    unsubscribeFromSymbol
  };
};