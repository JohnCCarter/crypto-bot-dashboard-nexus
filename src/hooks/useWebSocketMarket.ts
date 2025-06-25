/**
 * React hook för WebSocket marknadsdata från Bitfinex
 * Förbättrad med funktioner från officiell dokumentation
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

interface ChannelSubscription {
  channelId: number;
  channel: string;
  symbol: string;
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
  
  // Platform status (från Bitfinex info messages)
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
 * Hook för att hantera WebSocket marknadsdata med fullständig Bitfinex stöd
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
  
  const ws = useRef<WebSocket | null>(null);
  const subscriptions = useRef<Map<number, ChannelSubscription>>(new Map());
  const currentSymbol = useRef<string>(initialSymbol);
  const reconnectTimeout = useRef<NodeJS.Timeout | null>(null);
  const heartbeatTimeout = useRef<NodeJS.Timeout | null>(null);
  const pingInterval = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef<number>(0);
  const maxReconnectAttempts = 5; // Increased attempts
  const pingCounter = useRef<number>(0);
  const isUnmounting = useRef<boolean>(false);
  const connectionLock = useRef<boolean>(false);

  // Development mode detection
  const isDevelopment = process.env.NODE_ENV === 'development';
  const isStrictMode = useRef(false);

  // Ping/Pong för att testa anslutning och mäta latency
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

  // Hantera heartbeat timeout
  const resetHeartbeatTimeout = useCallback(() => {
    if (isUnmounting.current) return;
    
    if (heartbeatTimeout.current) {
      clearTimeout(heartbeatTimeout.current);
    }
    
    // Heartbeat ska komma var 15:e sekund enligt dokumentationen
    heartbeatTimeout.current = setTimeout(() => {
      if (!isUnmounting.current) {
        setError('Heartbeat timeout');
        connect();
      }
    }, 25000); // Increased timeout for stability
  }, []);

  // Aktivera avancerade funktioner (timestamps och checksums)
  const enableAdvancedFeatures = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN && !isUnmounting.current) {
      const confMessage = {
        event: 'conf',
        flags: 32768 + 131072 // TIMESTAMP + OB_CHECKSUM
      };
      
      try {
        ws.current.send(JSON.stringify(confMessage));
      } catch (error) {
        // Silent error - connection might be closing
      }
    }
  }, []);

  // WebSocket message handlers with defensive programming
  const handleTickerUpdate = useCallback((data: BitfinexTickerData) => {
    if (isUnmounting.current) return;
    
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
    if (isUnmounting.current) return;
    
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
    if (isUnmounting.current) return;
    
    if (data.trades && Array.isArray(data.trades)) {
      setTrades(prev => {
        // Add new trades and keep only latest 100
        const newTrades = [...data.trades, ...prev];
        return newTrades.slice(0, 100);
      });
    }
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

          // Aktivera avancerade funktioner
          enableAdvancedFeatures();
          
          // Starta ping/pong för latency mätning
          setTimeout(() => {
            if (!isUnmounting.current && ws.current?.readyState === WebSocket.OPEN) {
              pingInterval.current = setInterval(sendPing, 30000);
            }
          }, 1000);
          
          // Subscribe to initial symbol with delay
          setTimeout(() => {
            if (!isUnmounting.current) {
              subscribeToSymbol(currentSymbol.current);
            }
          }, 500);
        };

        ws.current.onmessage = (event) => {
          if (isUnmounting.current) return;
          
          try {
            const data = JSON.parse(event.data);
            
            // Hantera info messages (kritiskt för trading bots)
            if (data.event === 'info') {
              if (data.platform) {
                setPlatformStatus(data.platform.status === 1 ? 'operative' : 'maintenance');
              }
              
              // Hantera viktiga meddelanden
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
                // Resubscribe to all channels
                setTimeout(() => {
                  if (!isUnmounting.current) {
                    subscribeToSymbol(currentSymbol.current);
                  }
                }, 1000);
              }
              return;
            }
            
            // Hantera pong responses för latency mätning
            if (data.event === 'pong') {
              const pingTime = sessionStorage.getItem(`ping_${data.cid}`);
              if (pingTime) {
                const latencyMs = Date.now() - parseInt(pingTime);
                setLatency(latencyMs);
                sessionStorage.removeItem(`ping_${data.cid}`);
              }
              return;
            }
            
            // Hantera subscription responses
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
            
            // Handle different message types
            if (Array.isArray(data) && data.length >= 2) {
              const [channelId, messageData] = data;
              
              // Hantera heartbeat (enligt dokumentationen)
              if (messageData === 'hb') {
                setLastHeartbeat(Date.now());
                resetHeartbeatTimeout();
                return;
              }
              
              // Hitta subscription för detta channel ID
              const subscription = subscriptions.current.get(channelId);
              if (!subscription) {
                return;
              }
              
              // Route messages based på channel type
              if (subscription.channel === 'ticker' && Array.isArray(messageData) && messageData.length >= 10) {
                // Ticker data format
                handleTickerUpdate({
                  symbol: subscription.symbol,
                  price: messageData[6], // LAST_PRICE
                  volume: messageData[7], // VOLUME  
                  bid: messageData[0], // BID
                  ask: messageData[2], // ASK
                  timestamp: new Date().toISOString()
                });
              } else if (subscription.channel === 'book') {
                if (Array.isArray(messageData) && Array.isArray(messageData[0])) {
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
                    symbol: subscription.symbol,
                    bids,
                    asks,
                    timestamp: new Date().toISOString()
                  });
                } else if (Array.isArray(messageData) && messageData.length === 3) {
                  // Orderbook update [PRICE, COUNT, AMOUNT]
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

          // Rensa timeouts
          if (heartbeatTimeout.current) {
            clearTimeout(heartbeatTimeout.current);
          }
          if (pingInterval.current) {
            clearInterval(pingInterval.current);
          }

          // Attempt reconnection if not a clean close and under retry limit
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

      }, isDevelopment ? 200 : 50);

    } catch (error) {
      setError('Failed to create WebSocket connection');
      setConnecting(false);
      connectionLock.current = false;
    }
  }, [handleTickerUpdate, handleOrderbookUpdate, handleTradeUpdate, enableAdvancedFeatures, sendPing, resetHeartbeatTimeout, isDevelopment]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    isUnmounting.current = true;
    
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

    if (ws.current) {
      try {
        ws.current.close(1000, 'User initiated disconnect');
      } catch (error) {
        // Silent cleanup
      }
      ws.current = null;
    }

    setConnected(false);
    setConnecting(false);
    setPlatformStatus('unknown');
    subscriptions.current.clear();
  }, []);

  // Subscribe to symbol with better error handling
  const subscribeToSymbol = useCallback((symbol: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN || isUnmounting.current) {
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

    // Subscribe to orderbook med optimala inställningar
    const bookMsg = {
      event: 'subscribe', 
      channel: 'book',
      symbol: bitfinexSymbol,
      prec: 'P0', // Högsta precision
      freq: 'F0', // Realtid updates
      len: '25'   // Top 25 levels
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

  // Unsubscribe from symbol (nu med korrekt channel ID hantering)
  const unsubscribeFromSymbol = useCallback((symbol: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN || isUnmounting.current) {
      return;
    }

    // Hitta channel IDs för detta symbol
    const channelsToUnsubscribe: number[] = [];
    subscriptions.current.forEach((subscription, channelId) => {
      if (subscription.symbol === symbol || subscription.symbol === `t${symbol}`) {
        channelsToUnsubscribe.push(channelId);
      }
    });

    // Unsubscribe från varje kanal
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

  // Auto-connect on mount with better cleanup
  useEffect(() => {
    // Clear WebSocket spam protection on fresh mount
    const wsKeys = Object.keys(sessionStorage).filter(key => 
      key.startsWith('ws_') || key.startsWith('ping_')
    );
    wsKeys.forEach(key => sessionStorage.removeItem(key));
    
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
      disconnect();
    };
  }, [connect, disconnect, isDevelopment]);

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