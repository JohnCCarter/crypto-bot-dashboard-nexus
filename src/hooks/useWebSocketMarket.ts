/**
 * React hook för WebSocket marknadsdata från Bitfinex
 * Förbättrad med funktioner från officiell dokumentation
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
  const maxReconnectAttempts = 5;
  const pingCounter = useRef<number>(0);

  // Ping/Pong för att testa anslutning och mäta latency
  const sendPing = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      const pingId = ++pingCounter.current;
      const pingTime = Date.now();
      
      const pingMessage = {
        event: 'ping',
        cid: pingId
      };
      
      console.log('🏓 [WS] Sending ping:', pingId);
      ws.current.send(JSON.stringify(pingMessage));
      
      // Store ping time for latency calculation
      sessionStorage.setItem(`ping_${pingId}`, pingTime.toString());
    }
  }, []);

  // Hantera heartbeat timeout
  const resetHeartbeatTimeout = useCallback(() => {
    if (heartbeatTimeout.current) {
      clearTimeout(heartbeatTimeout.current);
    }
    
    // Heartbeat ska komma var 15:e sekund enligt dokumentationen
    heartbeatTimeout.current = setTimeout(() => {
      console.warn('💔 [WS] Heartbeat timeout - reconnecting');
      setError('Heartbeat timeout');
      connect();
    }, 20000); // 20 sekunder timeout (5 sekunder marginal)
  }, []);

  // Aktivera avancerade funktioner (timestamps och checksums)
  const enableAdvancedFeatures = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      const confMessage = {
        event: 'conf',
        flags: 32768 + 131072 // TIMESTAMP + OB_CHECKSUM
      };
      
      console.log('⚙️ [WS] Enabling advanced features');
      ws.current.send(JSON.stringify(confMessage));
    }
  }, []);

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

        // Aktivera avancerade funktioner
        enableAdvancedFeatures();
        
        // Starta ping/pong för latency mätning
        pingInterval.current = setInterval(sendPing, 30000); // Ping var 30:e sekund
        
        // Subscribe to initial symbol
        subscribeToSymbol(currentSymbol.current);
      };

      ws.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          
          // Hantera info messages (kritiskt för trading bots)
          if (data.event === 'info') {
            console.log('ℹ️ [WS] Info message:', data);
            
            if (data.platform) {
              setPlatformStatus(data.platform.status === 1 ? 'operative' : 'maintenance');
            }
            
            // Hantera viktiga meddelanden
            if (data.code === 20051) {
              console.warn('🔄 [WS] Server restart required - reconnecting');
              connect();
            } else if (data.code === 20060) {
              console.warn('🔧 [WS] Entering maintenance mode');
              setPlatformStatus('maintenance');
            } else if (data.code === 20061) {
              console.log('✅ [WS] Maintenance ended - resubscribing');
              setPlatformStatus('operative');
              // Resubscribe to all channels
              subscribeToSymbol(currentSymbol.current);
            }
            return;
          }
          
          // Hantera pong responses för latency mätning
          if (data.event === 'pong') {
            const pingTime = sessionStorage.getItem(`ping_${data.cid}`);
            if (pingTime) {
              const latencyMs = Date.now() - parseInt(pingTime);
              setLatency(latencyMs);
              console.log(`🏓 [WS] Pong received - latency: ${latencyMs}ms`);
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
            console.log(`✅ [WS] Subscribed to ${data.channel}:${data.symbol} (Channel ID: ${data.chanId})`);
            return;
          }
          
          if (data.event === 'error') {
            console.error('❌ [WS] Error:', data);
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
              console.log('💓 [WS] Heartbeat received');
              return;
            }
            
            // Hitta subscription för detta channel ID
            const subscription = subscriptions.current.get(channelId);
            if (!subscription) {
              console.warn(`⚠️ [WS] Unknown channel ID: ${channelId}`);
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
          console.error('❌ [WS] Message parsing error:', e);
        }
      };

      ws.current.onclose = (event) => {
        console.log('🔌 [WS] Disconnected:', event.code, event.reason);
        setConnected(false);
        setConnecting(false);
        setPlatformStatus('unknown');

        // Rensa timeouts
        if (heartbeatTimeout.current) {
          clearTimeout(heartbeatTimeout.current);
        }
        if (pingInterval.current) {
          clearInterval(pingInterval.current);
        }

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
        
        // Detaljerad error diagnostik
        let errorMessage = 'WebSocket connection error';
        
        // Försök identifiera error type
        if (error instanceof Event) {
          const target = error.target as WebSocket;
          if (target) {
            switch (target.readyState) {
              case WebSocket.CONNECTING:
                errorMessage = 'Failed to connect to Bitfinex WebSocket server. Check internet connection.';
                break;
              case WebSocket.CLOSING:
                errorMessage = 'WebSocket connection closing unexpectedly';
                break;
              case WebSocket.CLOSED:
                errorMessage = 'WebSocket connection closed by server. Possible network issue or firewall blocking.';
                break;
              default:
                errorMessage = 'Unknown WebSocket error';
            }
          }
        }
        
        console.warn(`🚨 [WS] Detailed error: ${errorMessage}`);
        setError(errorMessage);
        setConnecting(false);
      };

    } catch (error) {
      console.error('❌ [WS] Failed to create WebSocket:', error);
      setError('Failed to create WebSocket connection');
      setConnecting(false);
    }
  }, [handleTickerUpdate, handleOrderbookUpdate, handleTradeUpdate, enableAdvancedFeatures, sendPing, resetHeartbeatTimeout]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
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
      ws.current.close(1000, 'User initiated disconnect');
      ws.current = null;
    }

    setConnected(false);
    setConnecting(false);
    setPlatformStatus('unknown');
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
      ws.current.send(JSON.stringify(bookMsg));
      
      console.log(`📡 [WS] Subscribing to ${symbol}`);
    } catch (error) {
      console.error('❌ [WS] Failed to send subscription:', error);
      setError('Failed to subscribe to symbol');
    }
  }, []);

  // Unsubscribe from symbol (nu med korrekt channel ID hantering)
  const unsubscribeFromSymbol = useCallback((symbol: string) => {
    if (!ws.current || ws.current.readyState !== WebSocket.OPEN) {
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
    channelsToUnsubscribe.forEach(channelId => {
      const unsubMsg = {
        event: 'unsubscribe',
        chanId: channelId
      };
      
      try {
        ws.current!.send(JSON.stringify(unsubMsg));
        subscriptions.current.delete(channelId);
        console.log(`📡 [WS] Unsubscribed from channel ${channelId}`);
      } catch (error) {
        console.error('❌ [WS] Failed to unsubscribe:', error);
      }
    });
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