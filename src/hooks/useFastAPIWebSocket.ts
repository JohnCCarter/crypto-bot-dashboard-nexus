/**
 * React hook för FastAPI WebSocket-endpoints
 * Hanterar anslutning, prenumerationer och datahantering för FastAPI WebSockets
 */

import { useCallback, useEffect, useState } from 'react';
import { v4 as uuidv4 } from 'uuid';
import { useWebSocket } from './useWebSocket';

// Typer för marknadsdata
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

// Typer för användardata
interface Balance {
  currency: string;
  available: number;
  total: number;
}

interface Order {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  amount: number;
  price: number;
  status: string;
}

interface Position {
  symbol: string;
  amount: number;
  base_price: number;
  pnl: number;
}

// WebSocket meddelanden
interface WebSocketMessage {
  action?: string;
  channel?: string;
  symbol?: string;
  status?: string;
  error?: string;
  type?: string;
  /**
   * Möjliga datatyper: MarketData, OrderBook, Trade[], Balance, Order, Position, eller null.
   * Utöka unionen vid behov om fler typer tillkommer.
   */
  data?: MarketData | OrderBook | Trade[] | Balance | Order | Position | null;
}

// Hook returtyp
interface FastAPIWebSocketMarketHook {
  // Marknadsdata
  ticker: MarketData | null;
  orderbook: OrderBook | null;
  trades: Trade[];
  
  // Användardata
  balances: Balance[];
  orders: Order[];
  positions: Position[];
  
  // Anslutningsstatus
  isMarketConnected: boolean;
  isUserConnected: boolean;
  error: string | null;
  
  // Kontroll
  subscribeToMarket: (symbol: string, channel: 'ticker' | 'orderbook' | 'trades') => void;
  unsubscribeFromMarket: (symbol: string, channel: 'ticker' | 'orderbook' | 'trades') => void;
  connectUserData: (apiKey: string, apiSecret: string) => void;
  disconnectUserData: () => void;
}

/**
 * Hook för att ansluta till FastAPI WebSocket-endpoints
 */
export const useFastAPIWebSocket = (symbol: string = 'BTCUSD'): FastAPIWebSocketMarketHook => {
  const clientId = useState<string>(() => uuidv4())[0];
  
  // State
  const [ticker, setTicker] = useState<MarketData | null>(null);
  const [orderbook, setOrderbook] = useState<OrderBook | null>(null);
  const [trades, setTrades] = useState<Trade[]>([]);
  const [balances, setBalances] = useState<Balance[]>([]);
  const [orders, setOrders] = useState<Order[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [userCredentials, setUserCredentials] = useState<{ apiKey: string, apiSecret: string } | null>(null);
  
  // WebSocket URLs
  const marketWsUrl = `ws://${window.location.hostname}:8001/ws/market/${clientId}`;
  const userWsUrl = `ws://${window.location.hostname}:8001/ws/user/${clientId}`;
  
  // Hantera marknadsdata meddelanden
  const handleMarketMessage = useCallback((message: WebSocketMessage) => {
    if (message.error) {
      setError(message.error);
      return;
    }
    
    if (message.type === 'ticker' && message.data) {
      setTicker(message.data);
    } else if (message.type === 'orderbook' && message.data) {
      setOrderbook(message.data);
    } else if (message.type === 'trades' && message.data) {
      setTrades(prevTrades => {
        const newTrades = [...message.data, ...prevTrades];
        return newTrades.slice(0, 100);
      });
    }
  }, []);
  
  // Hantera användardata meddelanden
  const handleUserMessage = useCallback((message: WebSocketMessage) => {
    if (message.error) {
      setError(message.error);
      return;
    }
    
    if (message.type === 'balance' && message.data) {
      setBalances(prevBalances => {
        const newBalance = message.data;
        const balanceIndex = prevBalances.findIndex(b => b.currency === newBalance.currency);
        if (balanceIndex >= 0) {
          const updatedBalances = [...prevBalances];
          updatedBalances[balanceIndex] = newBalance;
          return updatedBalances;
        } else {
          return [...prevBalances, newBalance];
        }
      });
    } else if (message.type === 'order' && message.data) {
      setOrders(prevOrders => {
        const newOrder = message.data;
        const orderIndex = prevOrders.findIndex(o => o.id === newOrder.id);
        if (orderIndex >= 0) {
          const updatedOrders = [...prevOrders];
          updatedOrders[orderIndex] = newOrder;
          return updatedOrders;
        } else {
          return [...prevOrders, newOrder];
        }
      });
    } else if (message.type === 'position' && message.data) {
      setPositions(prevPositions => {
        const newPosition = message.data;
        const positionIndex = prevPositions.findIndex(p => p.symbol === newPosition.symbol);
        if (positionIndex >= 0) {
          const updatedPositions = [...prevPositions];
          updatedPositions[positionIndex] = newPosition;
          return updatedPositions;
        } else {
          return [...prevPositions, newPosition];
        }
      });
    }
  }, []);
  
  // WebSocket hooks
  const { isConnected: isMarketConnected, sendMessage: sendMarketMessage } = useWebSocket<WebSocketMessage>(
    marketWsUrl,
    handleMarketMessage
  );
  
  const { isConnected: isUserConnected, sendMessage: sendUserMessage } = useWebSocket<WebSocketMessage>(
    userWsUrl,
    handleUserMessage,
    false // Ingen automatisk återanslutning för användardata
  );
  
  // Prenumerera på marknadsdata
  const subscribeToMarket = useCallback((symbol: string, channel: 'ticker' | 'orderbook' | 'trades') => {
    if (isMarketConnected) {
      sendMarketMessage({
        action: 'subscribe',
        channel,
        symbol
      });
    }
  }, [isMarketConnected, sendMarketMessage]);
  
  // Avprenumerera på marknadsdata
  const unsubscribeFromMarket = useCallback((symbol: string, channel: 'ticker' | 'orderbook' | 'trades') => {
    if (isMarketConnected) {
      sendMarketMessage({
        action: 'unsubscribe',
        channel,
        symbol
      });
    }
  }, [isMarketConnected, sendMarketMessage]);
  
  // Anslut till användardata
  const connectUserData = useCallback((apiKey: string, apiSecret: string) => {
    setUserCredentials({ apiKey, apiSecret });
  }, []);
  
  // Koppla från användardata
  const disconnectUserData = useCallback(() => {
    setUserCredentials(null);
  }, []);
  
  // Skicka autentiseringsuppgifter när användardata WebSocket är ansluten
  useEffect(() => {
    if (isUserConnected && userCredentials) {
      sendUserMessage({
        api_key: userCredentials.apiKey,
        api_secret: userCredentials.apiSecret
      });
    }
  }, [isUserConnected, userCredentials, sendUserMessage]);
  
  // Prenumerera på initial symbol
  useEffect(() => {
    if (isMarketConnected && symbol) {
      subscribeToMarket(symbol, 'ticker');
      subscribeToMarket(symbol, 'orderbook');
      subscribeToMarket(symbol, 'trades');
    }
  }, [isMarketConnected, symbol, subscribeToMarket]);
  
  return {
    ticker, orderbook, trades,
    balances, orders, positions,
    isMarketConnected, isUserConnected, error,
    subscribeToMarket, unsubscribeFromMarket,
    connectUserData, disconnectUserData
  };
}; 