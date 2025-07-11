import React, { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';

// Types from existing implementation
interface MarketData {
  symbol: string;
  price: number;
  volume: number;
  bid?: number;
  ask?: number;
  timestamp: string;
}

interface OrderBook {
  symbol: string;
  bids: Array<{ price: number; amount: number }>;
  asks: Array<{ price: number; amount: number }>;
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

interface ChannelSubscription {
  channelId: number;
  channel: string;
  symbol: string;
}

interface OrderFill {
  id: string;
  orderId: string;
  symbol: string;
  side: 'buy' | 'sell';
  amount: number;
  price: number;
  fee: number;
  timestamp: number;
}

interface LiveOrder {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  amount: number;
  price: number;
  filled: number;
  remaining: number;
  status: 'open' | 'filled' | 'cancelled' | 'partial';
  timestamp: number;
}

interface LiveBalance {
  currency: string;
  available: number;
  total: number;
  timestamp: number;
}

interface WebSocketMarketState {
  // Data for all symbols
  tickers: Record<string, MarketData>;
  orderbooks: Record<string, OrderBook>;
  trades: Record<string, Trade[]>;
  
  // Connection status
  connected: boolean;
  connecting: boolean;
  platformStatus: 'operative' | 'maintenance' | 'unknown';
  error: string | null;
  lastHeartbeat: number | null;
  latency: number | null;
  
  // Control functions
  subscribeToSymbol: (symbol: string) => void;
  unsubscribeFromSymbol: (symbol: string) => void;
  
  // Data getters for specific symbols
  getTickerForSymbol: (symbol: string) => MarketData | null;
  getOrderbookForSymbol: (symbol: string) => OrderBook | null;
  getTradesForSymbol: (symbol: string) => Trade[];
  
  // User data streams
  userFills: OrderFill[];
  liveOrders: Record<string, LiveOrder>;
  liveBalances: Record<string, LiveBalance>;
  userDataConnected: boolean;
  userDataError: string | null;
  
  // User data subscriptions
  subscribeToUserData: () => Promise<void>;
  unsubscribeFromUserData: () => Promise<void>;
}

const WebSocketMarketContext = createContext<WebSocketMarketState | null>(null);

export const useGlobalWebSocketMarket = (): WebSocketMarketState => {
  const context = useContext(WebSocketMarketContext);
  if (!context) {
    throw new Error('useGlobalWebSocketMarket must be used within WebSocketMarketProvider');
  }
  return context;
};

export const WebSocketMarketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Global state for all symbols
  const [tickers, setTickers] = useState<Record<string, MarketData>>({});
  const [orderbooks, setOrderbooks] = useState<Record<string, OrderBook>>({});
  const [trades] = useState<Record<string, Trade[]>>({});
  
  // Connection state
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [platformStatus, setPlatformStatus] = useState<'operative' | 'maintenance' | 'unknown'>('unknown');
  const [error, setError] = useState<string | null>(null);
  const [lastHeartbeat, setLastHeartbeat] = useState<number | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  
  // User data state
  const [userFills, setUserFills] = useState<OrderFill[]>([]);
  const [liveOrders, setLiveOrders] = useState<Record<string, LiveOrder>>({});
  const [liveBalances, setLiveBalances] = useState<Record<string, LiveBalance>>({});
  const [userDataConnected, setUserDataConnected] = useState(false);
  const [userDataError, setUserDataError] = useState<string | null>(null);
  
  // WebSocket refs - SINGLE CONNECTION with proper state management
  const ws = useRef<WebSocket | null>(null);
  const subscriptions = useRef<Map<number, ChannelSubscription>>(new Map());
  const subscribedSymbols = useRef<Set<string>>(new Set());
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeout = useRef<NodeJS.Timeout | null>(null);
  const pingInterval = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef<number>(0);
  const maxReconnectAttempts = 3;
  const pingCounter = useRef<number>(0);
  const connectionInitialized = useRef<boolean>(false); // Prevent multiple connections
  
  // User data WebSocket refs
  const userDataWS = useRef<WebSocket | null>(null);
  const userDataConnecting = useRef<boolean>(false);
  const userDataAuthenticated = useRef<boolean>(false);

  // Ping/Pong för latency measurement
  const sendPing = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      const pingId = ++pingCounter.current;
      const pingTime = Date.now();
      
      const pingMessage = {
        event: 'ping',
        cid: pingId
      };
      
      ws.current.send(JSON.stringify(pingMessage));
      sessionStorage.setItem(`ping_${pingId}`, pingTime.toString());
    }
  }, []);

  // Heartbeat timeout management
  const resetHeartbeatTimeout = useCallback(() => {
    if (heartbeatTimeout.current) {
      clearTimeout(heartbeatTimeout.current);
    }
    
    heartbeatTimeout.current = setTimeout(() => {
      setError('Heartbeat timeout');
      connect();
    }, 20000);
  }, []);

  // Advanced features activation
  const enableAdvancedFeatures = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      const confMessage = {
        event: 'conf',
        flags: 32768 + 131072
      };
      
      ws.current.send(JSON.stringify(confMessage));
    }
  }, []);

  // Data handlers
  const handleTickerUpdate = useCallback((data: BitfinexTickerData) => {
    setTickers(prev => ({
      ...prev,
      [data.symbol]: {
        symbol: data.symbol,
        price: data.price,
        volume: data.volume,
        bid: data.bid,
        ask: data.ask,
        timestamp: data.timestamp
      }
    }));
  }, []);

  const handleOrderbookUpdate = useCallback((data: BitfinexOrderbookData) => {
    setOrderbooks(prev => {
      if (data.update) {
        // Incremental update
        const current = prev[data.symbol];
        if (!current) return prev;
        
        const newOrderbook = { ...current };
        const { price, amount, side } = data.update;
        
        if (side === 'bid') {
          const bidIndex = newOrderbook.bids.findIndex(bid => bid.price === price);
          if (amount === 0) {
            if (bidIndex !== -1) {
              newOrderbook.bids.splice(bidIndex, 1);
            }
          } else {
            if (bidIndex !== -1) {
              newOrderbook.bids[bidIndex].amount = amount;
            } else {
              newOrderbook.bids.push({ price, amount });
              newOrderbook.bids.sort((a, b) => b.price - a.price);
            }
          }
        } else {
          const askIndex = newOrderbook.asks.findIndex(ask => ask.price === price);
          if (amount === 0) {
            if (askIndex !== -1) {
              newOrderbook.asks.splice(askIndex, 1);
            }
          } else {
            if (askIndex !== -1) {
              newOrderbook.asks[askIndex].amount = amount;
            } else {
              newOrderbook.asks.push({ price, amount });
              newOrderbook.asks.sort((a, b) => a.price - b.price);
            }
          }
        }
        
        return {
          ...prev,
          [data.symbol]: newOrderbook
        };
      } else {
        // Full snapshot
        return {
          ...prev,
          [data.symbol]: {
            symbol: data.symbol,
            bids: data.bids ? data.bids.sort((a, b) => b.price - a.price) : [],
            asks: data.asks ? data.asks.sort((a, b) => a.price - b.price) : []
          }
        };
      }
    });
  }, []);

  // SINGLE WebSocket connection with development mode protection
  const connect = useCallback(() => {
    // Prevent multiple connections (especially in React Strict Mode)
    if (connectionInitialized.current || ws.current?.readyState === WebSocket.OPEN) {
      return;
    }
    
    // If connecting, don't create another connection
    if (connecting) {
      return;
    }

    connectionInitialized.current = true;
    setConnecting(true);
    setError(null);

    try {
      ws.current = new WebSocket('wss://api-pub.bitfinex.com/ws/2');

      ws.current.onopen = () => {
        setConnected(true);
        setConnecting(false);
        setError(null);
        reconnectAttempts.current = 0;

        enableAdvancedFeatures();
        pingInterval.current = setInterval(sendPing, 30000);
        
        // Re-subscribe to all previously subscribed symbols
        subscribedSymbols.current.forEach(symbol => {
          subscribeToSymbol(symbol);
        });
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          if (data.event === 'info') {
            if (data.platform) {
              setPlatformStatus(data.platform.status === 1 ? 'operative' : 'maintenance');
            }
            
            if (data.code === 20051) {
              connect();
            } else if (data.code === 20060) {
              setPlatformStatus('maintenance');
            } else if (data.code === 20061) {
              setPlatformStatus('operative');
              subscribedSymbols.current.forEach(symbol => {
                subscribeToSymbol(symbol);
              });
            }
            return;
          }
          
          if (data.event === 'pong') {
            const pingTime = sessionStorage.getItem(`ping_${data.cid}`);
            if (pingTime) {
              const latencyMs = Date.now() - parseInt(pingTime);
              setLatency(latencyMs);
              sessionStorage.removeItem(`ping_${data.cid}`);
            }
            return;
          }
          
          if (data.event === 'subscribed') {
            const subscription: ChannelSubscription = {
              channelId: data.chanId,
              channel: data.channel,
              symbol: data.symbol
            };
            subscriptions.current.set(data.chanId, subscription);
            return;
          }
          
          if (data.event === 'error') {
            setError(`${data.msg} (Code: ${data.code})`);
            return;
          }
          
          if (Array.isArray(data) && data.length >= 2) {
            const [channelId, messageData] = data;
            
            if (messageData === 'hb') {
              setLastHeartbeat(Date.now());
              resetHeartbeatTimeout();
              return;
            }
            
            const subscription = subscriptions.current.get(channelId);
            if (!subscription) return;
            
            if (subscription.channel === 'ticker' && Array.isArray(messageData) && messageData.length >= 10) {
              handleTickerUpdate({
                symbol: subscription.symbol,
                price: messageData[6],
                volume: messageData[7], 
                bid: messageData[0],
                ask: messageData[2],
                timestamp: new Date().toISOString()
              });
            } else if (subscription.channel === 'book') {
              if (Array.isArray(messageData) && Array.isArray(messageData[0])) {
                const bids: Array<{ price: number; amount: number }> = [];
                const asks: Array<{ price: number; amount: number }> = [];
                
                messageData.forEach((entry: number[]) => {
                  const [price, , amount] = entry;
                  if (amount > 0) {
                    bids.push({ price, amount });
                  } else {
                    asks.push({ price, amount: Math.abs(amount) });
                  }
                });
                
                handleOrderbookUpdate({
                  symbol: subscription.symbol,
                  bids,
                  asks,
                  timestamp: new Date().toISOString()
                });
              } else if (Array.isArray(messageData) && messageData.length === 3) {
                const [price, , amount] = messageData;
                
                handleOrderbookUpdate({
                  symbol: subscription.symbol,
                  update: {
                    price,
                    amount: Math.abs(amount),
                    side: amount > 0 ? 'bid' : 'ask'
                  },
                  timestamp: new Date().toISOString()
                });
              }
            }
          }
        } catch {
          // Silent error handling - no spam
        }
      };

      ws.current.onclose = (event) => {
        setConnected(false);
        setConnecting(false);
        setPlatformStatus('unknown');
        connectionInitialized.current = false; // Reset connection flag

        if (heartbeatTimeout.current) {
          clearTimeout(heartbeatTimeout.current);
        }
        if (pingInterval.current) {
          clearInterval(pingInterval.current);
        }

        // Only reconnect if it wasn't a clean close and we're under retry limit
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          const delay = Math.min(5000 * Math.pow(2, reconnectAttempts.current), 60000);
          
          reconnectTimeout.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        } else if (reconnectAttempts.current >= maxReconnectAttempts) {
          setError('Max reconnection attempts reached');
        }
      };

      ws.current.onerror = () => {
        // Silent error handling - no spam
        setError('WebSocket connection failed');
        setConnecting(false);
        connectionInitialized.current = false; // Reset connection flag on error
      };

    } catch {
      setError('Failed to create WebSocket connection');
      setConnecting(false);
    }
  }, [handleTickerUpdate, handleOrderbookUpdate, enableAdvancedFeatures, sendPing, resetHeartbeatTimeout]);

  // Subscribe to symbol
  const subscribeToSymbol = useCallback((symbol: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      return;
    }

    // Track subscribed symbols
    subscribedSymbols.current.add(symbol);

    const bitfinexSymbol = symbol.startsWith('t') ? symbol : `t${symbol}`;

    const tickerMsg = {
      event: 'subscribe',
      channel: 'ticker',
      symbol: bitfinexSymbol
    };

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
    } catch {
      setError('Failed to subscribe to symbol');
    }
  }, []);

  // Unsubscribe from symbol
  const unsubscribeFromSymbol = useCallback((symbol: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
      return;
    }

    subscribedSymbols.current.delete(symbol);

    const channelsToUnsubscribe: number[] = [];
    subscriptions.current.forEach((subscription, channelId) => {
      if (subscription.symbol === symbol || subscription.symbol === `t${symbol}`) {
        channelsToUnsubscribe.push(channelId);
      }
    });

    channelsToUnsubscribe.forEach(channelId => {
      const unsubMsg = {
        event: 'unsubscribe',
        chanId: channelId
      };
      
      try {
        ws.current!.send(JSON.stringify(unsubMsg));
        subscriptions.current.delete(channelId);
      } catch {
        // Silent error handling
      }
    });
  }, []);

  // Data getters
  const getTickerForSymbol = useCallback((symbol: string): MarketData | null => {
    const bitfinexSymbol = symbol.startsWith('t') ? symbol : `t${symbol}`;
    return tickers[bitfinexSymbol] || tickers[symbol] || null;
  }, [tickers]);

  const getOrderbookForSymbol = useCallback((symbol: string): OrderBook | null => {
    const bitfinexSymbol = symbol.startsWith('t') ? symbol : `t${symbol}`;
    return orderbooks[bitfinexSymbol] || orderbooks[symbol] || null;
  }, [orderbooks]);

  const getTradesForSymbol = useCallback((symbol: string): Trade[] => {
    const bitfinexSymbol = symbol.startsWith('t') ? symbol : `t${symbol}`;
    return trades[bitfinexSymbol] || trades[symbol] || [];
  }, [trades]);

  // Auto-connect on mount with proper cleanup
  useEffect(() => {
    connect();

    return () => {
      // Clean shutdown - market data WebSocket
      connectionInitialized.current = false;
      
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
        reconnectTimeout.current = null;
      }
      if (heartbeatTimeout.current) {
        clearTimeout(heartbeatTimeout.current);
        heartbeatTimeout.current = null;
      }
      if (pingInterval.current) {
        clearInterval(pingInterval.current);
        pingInterval.current = null;
      }
      if (ws.current && ws.current.readyState !== WebSocket.CLOSED) {
        ws.current.close(1000, 'Provider unmount');
        ws.current = null;
      }
      
      // Clean shutdown - user data WebSocket
      if (userDataWS.current && userDataWS.current.readyState !== WebSocket.CLOSED) {
        userDataWS.current.close(1000, 'Provider unmount');
        userDataWS.current = null;
      }
      userDataConnecting.current = false;
      userDataAuthenticated.current = false;
    };
  }, [connect]);

  // User data WebSocket implementation
  const subscribeToUserData = useCallback(async (): Promise<void> => {
    // If already connected or connecting, don't create another connection
    if (userDataConnected || userDataConnecting.current) {
      return;
    }

    userDataConnecting.current = true;
    setUserDataError(null);

    try {
      // Get API credentials from environment or config
      const apiKey = process.env.REACT_APP_BITFINEX_API_KEY || 
                   localStorage.getItem('bitfinex_api_key') || '';
      const apiSecret = process.env.REACT_APP_BITFINEX_API_SECRET || 
                       localStorage.getItem('bitfinex_api_secret') || '';

      if (!apiKey || !apiSecret) {
        // For paper trading, we can simulate user data or use mock data
        console.log('📊 No API credentials found - using mock user data for paper trading');
        setUserDataConnected(true);
        userDataConnecting.current = false;
        
        // Simulate some mock data for paper trading
        setLiveBalances({
          'TESTUSD': {
            currency: 'TESTUSD',
            available: 10000,
            total: 10000,
            timestamp: Date.now()
          },
          'TESTBTC': {
            currency: 'TESTBTC',
            available: 0.1,
            total: 0.1,
            timestamp: Date.now()
          }
        });
        
        return;
      }

      // Connect to authenticated WebSocket for user data
      userDataWS.current = new WebSocket('wss://api-pub.bitfinex.com/ws/2');

      userDataWS.current.onopen = async () => {
        try {
          // Generate authentication payload
          const nonce = (Date.now() * 1000).toString();
          const authPayload = `AUTH${nonce}`;
          
          // This is a simplified version - in production you'd want to do this server-side
          // For now, we'll focus on the WebSocket structure
          const authMessage = {
            event: 'auth',
            apiKey: apiKey,
            authSig: 'placeholder_signature', // Would be HMAC-SHA384 in production
            authPayload: authPayload,
            authNonce: nonce
          };

          userDataWS.current?.send(JSON.stringify(authMessage));
        } catch {
          setUserDataError('Authentication failed');
          userDataConnecting.current = false;
        }
      };

      userDataWS.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Handle authentication response
          if (data.event === 'auth') {
            if (data.status === 'OK') {
              userDataAuthenticated.current = true;
              setUserDataConnected(true);
              setUserDataError(null);
              console.log('✅ User data WebSocket authenticated');
            } else {
              setUserDataError(`Authentication failed: ${data.msg || 'Unknown error'}`);
              userDataAuthenticated.current = false;
            }
            userDataConnecting.current = false;
            return;
          }

          // Handle user data messages
          if (Array.isArray(data) && data.length >= 2) {
            const [, messageData] = data;
            
            if (messageData === 'hb') {
              // Heartbeat - user data connection is alive
              return;
            }

            // Handle different user data message types
            if (Array.isArray(messageData) && messageData.length > 0) {
              const msgType = messageData[0];
              
              if (msgType === 'te') {
                // Trade execution (order fill)
                const executionData = messageData[1];
                if (executionData && executionData.length >= 6) {
                  const fill: OrderFill = {
                    id: executionData[0]?.toString() || '',
                    orderId: executionData[3]?.toString() || '',
                    symbol: executionData[1] || '',
                    side: (executionData[4] || 0) > 0 ? 'buy' : 'sell',
                    amount: Math.abs(executionData[4] || 0),
                    price: executionData[5] || 0,
                    fee: executionData[9] || 0,
                    timestamp: executionData[2] || Date.now()
                  };
                  
                  setUserFills(prev => {
                    // Remove any fill with the same id as the new fill
                    const filtered = prev.filter(f => f.id !== fill.id);
                    // Prepend the new fill and keep only the last 50 unique fills
                    return [fill, ...filtered].slice(0, 50);
                  });
                }
              } else if (msgType === 'ou' || msgType === 'on') {
                // Order update or new order
                const orderData = messageData[1];
                if (orderData && orderData.length >= 16) {
                  const order: LiveOrder = {
                    id: orderData[0]?.toString() || '',
                    symbol: orderData[3] || '',
                    side: (orderData[7] || 0) > 0 ? 'buy' : 'sell',
                    amount: Math.abs(orderData[7] || 0),
                    price: orderData[16] || 0,
                    filled: Math.abs(orderData[7] || 0) - Math.abs(orderData[6] || 0),
                    remaining: Math.abs(orderData[6] || 0),
                    status: parseOrderStatus(orderData[13]),
                    timestamp: orderData[5] || Date.now()
                  };
                  
                  setLiveOrders(prev => {
                    // Remove order if status is 'filled' or 'cancelled'
                    if (order.status === 'filled' || order.status === 'cancelled') {
                      const rest = Object.fromEntries(Object.entries(prev).filter(([k]) => k !== order.id));
                      return rest;
                    }
                    // Otherwise, add/update the order
                    return {
                      ...prev,
                      [order.id]: order
                    };
                  });
                }
              } else if (msgType === 'wu' || msgType === 'ws') {
                // Wallet update or snapshot
                const walletData = messageData[1];
                if (walletData && walletData.length >= 5) {
                  const balance: LiveBalance = {
                    currency: walletData[1] || '',
                    available: walletData[4] || 0,
                    total: walletData[2] || 0,
                    timestamp: Date.now()
                  };
                  
                  setLiveBalances(prev => ({
                    ...prev,
                    [balance.currency]: balance
                  }));
                }
              }
            }
          }
        } catch {
          console.error('❌ Error processing user data message');
        }
      };

      userDataWS.current.onclose = () => {
        setUserDataConnected(false);
        userDataAuthenticated.current = false;
        userDataConnecting.current = false;
        console.log('🔌 User data WebSocket disconnected');
      };

      userDataWS.current.onerror = () => {
        setUserDataError('User data WebSocket connection failed');
        userDataConnecting.current = false;
        console.error('❌ User data WebSocket error');
      };

    } catch {
      setUserDataError('Failed to connect to user data stream');
      userDataConnecting.current = false;
    }
  }, [userDataConnected]);

  const unsubscribeFromUserData = useCallback(async (): Promise<void> => {
    if (userDataWS.current) {
      userDataWS.current.close();
      userDataWS.current = null;
    }
    
    setUserDataConnected(false);
    userDataAuthenticated.current = false;
    userDataConnecting.current = false;
    setUserFills([]);
    setLiveOrders({});
    setLiveBalances({});
    
    console.log('🔌 User data WebSocket unsubscribed');
  }, []);

  // Helper function to parse order status
  const parseOrderStatus = (statusInfo: unknown): 'open' | 'filled' | 'cancelled' | 'partial' => {
    if (!statusInfo) return 'open';
    const statusStr = typeof statusInfo === 'string' ? statusInfo : statusInfo.toString();
    if (statusStr.includes('EXECUTED')) return 'filled';
    if (statusStr.includes('CANCELED')) return 'cancelled';
    if (statusStr.includes('PARTIALLY FILLED')) return 'partial';
    return 'open';
  };

  const value: WebSocketMarketState = {
    tickers,
    orderbooks,
    trades,
    connected,
    connecting,
    platformStatus,
    error,
    lastHeartbeat,
    latency,
    subscribeToSymbol,
    unsubscribeFromSymbol,
    getTickerForSymbol,
    getOrderbookForSymbol,
    getTradesForSymbol,
    userFills,
    liveOrders,
    liveBalances,
    userDataConnected,
    userDataError,
    subscribeToUserData,
    unsubscribeFromUserData
  };

  return (
    <WebSocketMarketContext.Provider value={value}>
      {children}
    </WebSocketMarketContext.Provider>
  );
};