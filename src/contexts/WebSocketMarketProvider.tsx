import React, { createContext, useContext, useRef, useState, useCallback, useEffect } from 'react';

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
  const [trades, setTrades] = useState<Record<string, Trade[]>>({});
  
  // Connection state
  const [connected, setConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [platformStatus, setPlatformStatus] = useState<'operative' | 'maintenance' | 'unknown'>('unknown');
  const [error, setError] = useState<string | null>(null);
  const [lastHeartbeat, setLastHeartbeat] = useState<number | null>(null);
  const [latency, setLatency] = useState<number | null>(null);
  
  // WebSocket refs - SINGLE CONNECTION with better stability
  const ws = useRef<WebSocket | null>(null);
  const subscriptions = useRef<Map<number, ChannelSubscription>>(new Map());
  const subscribedSymbols = useRef<Set<string>>(new Set());
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeout = useRef<NodeJS.Timeout | null>(null);
  const pingInterval = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef<number>(0);
  const maxReconnectAttempts = 5; // Increased attempts
  const pingCounter = useRef<number>(0);
  const isUnmounting = useRef<boolean>(false);
  const connectionLock = useRef<boolean>(false);

  // Detect development mode and React Strict Mode
  const isDevelopment = process.env.NODE_ENV === 'development';
  const isStrictMode = useRef(false);

  // Ping/Pong för latency measurement
  const sendPing = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN && !isUnmounting.current) {
      const pingId = ++pingCounter.current;
      const pingTime = Date.now();
      
      const pingMessage = {
        event: 'ping',
        cid: pingId
      };
      
      try {
        ws.current.send(JSON.stringify(pingMessage));
        sessionStorage.setItem(`ping_${pingId}`, pingTime.toString());
      } catch (error) {
        // Silent error - connection might be closing
      }
    }
  }, []);

  // Heartbeat timeout management
  const resetHeartbeatTimeout = useCallback(() => {
    if (isUnmounting.current) return;
    
    if (heartbeatTimeout.current) {
      clearTimeout(heartbeatTimeout.current);
    }
    
    heartbeatTimeout.current = setTimeout(() => {
      if (!isUnmounting.current) {
        setError('Heartbeat timeout');
        connect();
      }
    }, 25000); // Increased timeout for stability
  }, []);

  // Advanced features activation
  const enableAdvancedFeatures = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN && !isUnmounting.current) {
      const confMessage = {
        event: 'conf',
        flags: 32768 + 131072
      };
      
      try {
        ws.current.send(JSON.stringify(confMessage));
      } catch (error) {
        // Silent error - connection might be closing
      }
    }
  }, []);

  // Data handlers with defensive programming
  const handleTickerUpdate = useCallback((data: BitfinexTickerData) => {
    if (isUnmounting.current) return;
    
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
    if (isUnmounting.current) return;
    
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

  const handleTradeUpdate = useCallback((data: { symbol: string; trades: Trade[] }) => {
    if (isUnmounting.current) return;
    
    setTrades(prev => ({
      ...prev,
      [data.symbol]: [...data.trades, ...(prev[data.symbol] || [])].slice(0, 100)
    }));
  }, []);

  // Enhanced WebSocket connection with stability improvements
  const connect = useCallback(() => {
    // Prevent multiple simultaneous connections
    if (connectionLock.current || isUnmounting.current) {
      return;
    }

    if (ws.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Check if we're in Strict Mode (double useEffect calls)
    if (isDevelopment && !isStrictMode.current) {
      isStrictMode.current = true;
      // Add delay in development to prevent double connections
      setTimeout(() => connect(), 100);
      return;
    }

    connectionLock.current = true;
    setConnecting(true);
    setError(null);

    // Clean up any existing connection
    if (ws.current) {
      try {
        ws.current.close(1000, 'Reconnecting');
      } catch (error) {
        // Silent cleanup
      }
      ws.current = null;
    }

    try {
      // Add small delay to prevent browser-specific connection issues
      setTimeout(() => {
        if (isUnmounting.current) {
          connectionLock.current = false;
          return;
        }

        ws.current = new WebSocket('wss://api-pub.bitfinex.com/ws/2');

        ws.current.onopen = () => {
          if (isUnmounting.current) return;
          
          setConnected(true);
          setConnecting(false);
          setError(null);
          reconnectAttempts.current = 0;
          connectionLock.current = false;

          enableAdvancedFeatures();
          
          // Start ping with delay to avoid immediate spam
          setTimeout(() => {
            if (!isUnmounting.current && ws.current?.readyState === WebSocket.OPEN) {
              pingInterval.current = setInterval(sendPing, 30000);
            }
          }, 1000);
          
          // Re-subscribe to all previously subscribed symbols with delay
          setTimeout(() => {
            if (!isUnmounting.current) {
              subscribedSymbols.current.forEach(symbol => {
                subscribeToSymbol(symbol);
              });
            }
          }, 500);
        };

        ws.current.onmessage = (event) => {
          if (isUnmounting.current) return;
          
          try {
            const data = JSON.parse(event.data);
            
            if (data.event === 'info') {
              if (data.platform) {
                setPlatformStatus(data.platform.status === 1 ? 'operative' : 'maintenance');
              }
              
              if (data.code === 20051) {
                // Server restart - reconnect with delay
                setTimeout(() => {
                  if (!isUnmounting.current) {
                    connect();
                  }
                }, 1000);
              } else if (data.code === 20060) {
                setPlatformStatus('maintenance');
              } else if (data.code === 20061) {
                setPlatformStatus('operative');
                setTimeout(() => {
                  if (!isUnmounting.current) {
                    subscribedSymbols.current.forEach(symbol => {
                      subscribeToSymbol(symbol);
                    });
                  }
                }, 1000);
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
                    const [price, count, amount] = entry;
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
                  const [price, count, amount] = messageData;
                  
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
          } catch (e) {
            // Silent error handling - prevent console spam
          }
        };

        ws.current.onclose = (event) => {
          if (isUnmounting.current) return;
          
          setConnected(false);
          setConnecting(false);
          setPlatformStatus('unknown');
          connectionLock.current = false;

          // Clean up intervals
          if (heartbeatTimeout.current) {
            clearTimeout(heartbeatTimeout.current);
          }
          if (pingInterval.current) {
            clearInterval(pingInterval.current);
          }

          // Only attempt reconnection for unexpected closes
          if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts && !isUnmounting.current) {
            const delay = Math.min(3000 * Math.pow(1.5, reconnectAttempts.current), 30000);
            
            reconnectTimeout.current = setTimeout(() => {
              if (!isUnmounting.current) {
                reconnectAttempts.current++;
                connect();
              }
            }, delay);
          } else if (reconnectAttempts.current >= maxReconnectAttempts) {
            setError('Max reconnection attempts reached - check internet connection');
          }
        };

        ws.current.onerror = () => {
          if (isUnmounting.current) return;
          
          // Silent error handling to prevent browser console spam
          setError('WebSocket connection failed');
          setConnecting(false);
          connectionLock.current = false;
        };

      }, isDevelopment ? 200 : 50); // Delay in development mode

    } catch (error) {
      setError('Failed to create WebSocket connection');
      setConnecting(false);
      connectionLock.current = false;
    }
  }, [handleTickerUpdate, handleOrderbookUpdate, enableAdvancedFeatures, sendPing, resetHeartbeatTimeout, isDevelopment]);

  // Subscribe to symbol with better error handling
  const subscribeToSymbol = useCallback((symbol: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN || isUnmounting.current) {
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
      // Add small delay between subscriptions
      setTimeout(() => {
        if (ws.current?.readyState === WebSocket.OPEN && !isUnmounting.current) {
          ws.current.send(JSON.stringify(bookMsg));
        }
      }, 100);
    } catch (error) {
      setError('Failed to subscribe to symbol');
    }
  }, []);

  // Unsubscribe from symbol
  const unsubscribeFromSymbol = useCallback((symbol: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN || isUnmounting.current) {
      return;
    }

    subscribedSymbols.current.delete(symbol);

    const channelsToUnsubscribe: number[] = [];
    subscriptions.current.forEach((subscription, channelId) => {
      if (subscription.symbol === symbol || subscription.symbol === `t${symbol}`) {
        channelsToUnsubscribe.push(channelId);
      }
    });

    channelsToUnsubscribe.forEach((channelId, index) => {
      const unsubMsg = {
        event: 'unsubscribe',
        chanId: channelId
      };
      
      try {
        // Add small delays between unsubscriptions
        setTimeout(() => {
          if (ws.current?.readyState === WebSocket.OPEN && !isUnmounting.current) {
            ws.current.send(JSON.stringify(unsubMsg));
            subscriptions.current.delete(channelId);
          }
        }, index * 50);
      } catch (error) {
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

  // Auto-connect on mount with better cleanup
  useEffect(() => {
    // Delay initial connection in development mode
    const delay = isDevelopment ? 500 : 100;
    
    const connectTimer = setTimeout(() => {
      if (!isUnmounting.current) {
        connect();
      }
    }, delay);

    return () => {
      isUnmounting.current = true;
      clearTimeout(connectTimer);
      
      // Clean up all timers
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (heartbeatTimeout.current) {
        clearTimeout(heartbeatTimeout.current);
      }
      if (pingInterval.current) {
        clearInterval(pingInterval.current);
      }
      
      // Close WebSocket connection
      if (ws.current) {
        try {
          ws.current.close(1000, 'Provider unmount');
        } catch (error) {
          // Silent cleanup
        }
        ws.current = null;
      }
      
      // Clear subscriptions
      subscriptions.current.clear();
      subscribedSymbols.current.clear();
    };
  }, [connect, isDevelopment]);

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
    getTradesForSymbol
  };

  return (
    <WebSocketMarketContext.Provider value={value}>
      {children}
    </WebSocketMarketContext.Provider>
  );
};