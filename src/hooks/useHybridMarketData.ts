/**
 * Hybrid Market Data Hook - Smart kombination av WebSocket och REST
 * 
 * Strategi:
 * 1. REST för initial load (omedelbar data)
 * 2. WebSocket för live updates (real-time performance) 
 * 3. REST fallback när WebSocket fails (reliability)
 * 4. Smart data merging för seamless experience
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { useWebSocketMarket } from './useWebSocketMarket';
import { api } from '@/lib/api';
import { OrderBook, OHLCVData } from '@/types/trading';

interface RestTickerData {
  symbol?: string;
  last?: number;
  price?: number;
  bid?: number;
  ask?: number;
  volume?: number;
  timestamp?: string;
}

interface HybridMarketData {
  // Market data
  ticker: {
    symbol: string;
    price: number;
    bid?: number;
    ask?: number;
    volume: number;
    timestamp: string;
  } | null;
  
  orderbook: OrderBook | null;
  chartData: OHLCVData[];
  
  // Connection status
  connected: boolean;
  connecting: boolean;
  dataSource: 'websocket' | 'rest' | 'hybrid';
  
  // Error state
  error: string | null;
  
  // Methods
  refreshData: () => Promise<void>;
  switchToRestMode: () => void;
  switchToWebSocketMode: () => void;
}

export const useHybridMarketData = (
  symbol: string = 'BTCUSD',
  enableWebSocket: boolean = true
): HybridMarketData => {
  
  // State för REST data
  const [restTicker, setRestTicker] = useState<RestTickerData | null>(null);
  const [restOrderbook, setRestOrderbook] = useState<OrderBook | null>(null);
  const [chartData, setChartData] = useState<OHLCVData[]>([]);
  
  // State för hybrid control
  const [dataSource, setDataSource] = useState<'websocket' | 'rest' | 'hybrid'>('hybrid');
  const [isRestPolling, setIsRestPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // WebSocket hook
  const {
    ticker: wsTicker,
    orderbook: wsOrderbook,
    connected: wsConnected,
    connecting: wsConnecting,
    error: wsError
  } = useWebSocketMarket(enableWebSocket ? symbol : '');

  // Refs för polling control
  const restPollingInterval = useRef<NodeJS.Timeout | null>(null);
  const lastRestUpdate = useRef<number>(0);
  const initialLoadComplete = useRef<boolean>(false);

  // 🚀 INITIAL DATA LOAD (REST) - Omedelbar data när komponenten mountar
  const loadInitialData = useCallback(async () => {
    // Tillåt reload när symbol ändras (initialLoadComplete hanteras i useEffect)
    
    try {
      // Parallella REST calls för snabb initial load
      const [tickerData, orderbookData, ohlcvData] = await Promise.all([
        api.getMarketTicker(symbol).catch(() => null),
        api.getOrderBook(symbol, 20).catch(() => null),
        api.getChartData(symbol, '5m', 100).catch(() => [])
      ]);

      if (tickerData) {
        setRestTicker(tickerData);
      }

      if (orderbookData) {
        setRestOrderbook(orderbookData);
      }

      if (ohlcvData && ohlcvData.length > 0) {
        setChartData(ohlcvData);
      }

      initialLoadComplete.current = true;
      setError(null);
      
    } catch (err) {
      console.error('Failed to load initial market data');
      setError('Failed to load initial market data');
    }
  }, [symbol]); // Only depend on symbol

  // 📡 REST POLLING FALLBACK - När WebSocket är disconnected
  const startRestPolling = useCallback(() => {
    if (restPollingInterval.current) return;

    setIsRestPolling(true);
    setDataSource('rest');

    restPollingInterval.current = setInterval(async () => {
      try {
        const now = Date.now();
        
        // Rate limiting: Max 1 update per 2 sekunder
        if (now - lastRestUpdate.current < 2000) return;

        const [tickerData, orderbookData] = await Promise.all([
          api.getMarketTicker(symbol).catch(() => null),
          api.getOrderBook(symbol, 20).catch(() => null)
        ]);

        if (tickerData) {
          setRestTicker(tickerData);
        }

        if (orderbookData) {
          setRestOrderbook(orderbookData);
        }

        lastRestUpdate.current = now;
        setError(null);

      } catch (err) {
        setError('REST polling failed');
      }
    }, 2000); // Poll every 2 seconds
  }, [symbol]); // Only depend on symbol

  // 🛑 STOP REST POLLING
  const stopRestPolling = useCallback(() => {
    if (restPollingInterval.current) {
      clearInterval(restPollingInterval.current);
      restPollingInterval.current = null;
      setIsRestPolling(false);
    }
  }, []); // No dependencies needed

  // 🧠 SMART DATA SOURCE MANAGEMENT
  useEffect(() => {
    if (wsConnected && enableWebSocket) {
      // WebSocket is connected - use it as primary source
      stopRestPolling();
      setDataSource('websocket');
      
    } else if (enableWebSocket && !wsConnecting) {
      // WebSocket failed or disabled - fallback to REST
      startRestPolling();
      
    } else if (!enableWebSocket) {
      // Pure REST mode
      startRestPolling();
      setDataSource('rest');
    }

    return () => stopRestPolling();
  }, [wsConnected, wsConnecting, enableWebSocket, startRestPolling, stopRestPolling]);

  // 🔄 INITIAL LOAD EFFECT - Reset på symbol change för korrekt data
  useEffect(() => {
    // Reset initial load flag när symbol ändras
    initialLoadComplete.current = false;
    
    // Rensa gamla data för att undvika förvirring
    setRestTicker(null);
    setRestOrderbook(null);
    setChartData([]);
    setError(null);
    
    // Ladda data för nya symbolen
    loadInitialData();
  }, [symbol, loadInitialData]); // Re-run when symbol changes

  // 🎯 SMART DATA SELECTION - Prioritera WebSocket när tillgängligt
  const finalTicker = wsConnected && wsTicker ? {
    symbol: wsTicker.symbol,
    price: wsTicker.price,
    bid: wsTicker.bid,
    ask: wsTicker.ask,
    volume: wsTicker.volume,
    timestamp: wsTicker.timestamp
  } : restTicker ? {
    symbol: restTicker.symbol || symbol,
    price: restTicker.last || restTicker.price || 0,
    bid: restTicker.bid,
    ask: restTicker.ask,
    volume: restTicker.volume || 0,
    timestamp: restTicker.timestamp || new Date().toISOString()
  } : null;

  const finalOrderbook = wsConnected && wsOrderbook ? wsOrderbook : restOrderbook;

  // 📊 LIVE CHART UPDATES - Optimized with useMemo-like pattern
  useEffect(() => {
    if (!finalTicker || chartData.length === 0) return;
    
    const lastCandle = chartData[chartData.length - 1];
    if (!lastCandle) return;
    
    const currentTime = Date.now();
    const candleTime = lastCandle.timestamp;
    const timeDiff = currentTime - candleTime;
    
    // Only update if within same 5-minute window and price actually changed
    if (timeDiff < 5 * 60 * 1000 && lastCandle.close !== finalTicker.price) {
      setChartData(prevData => {
        const updatedData = [...prevData];
        const lastIdx = updatedData.length - 1;
        
        updatedData[lastIdx] = {
          ...updatedData[lastIdx],
          close: finalTicker.price,
          high: Math.max(updatedData[lastIdx].high, finalTicker.price),
          low: Math.min(updatedData[lastIdx].low, finalTicker.price),
          volume: updatedData[lastIdx].volume + (finalTicker.volume * 0.01)
        };
        
        return updatedData;
      });
    }
  }, [finalTicker?.price, chartData.length]); // Only depend on price and data length

  // 🔧 UTILITY METHODS - Stabilized
  const refreshData = useCallback(async () => {
    initialLoadComplete.current = false; // Allow reload
    await loadInitialData();
  }, [loadInitialData]);

  const switchToRestMode = useCallback(() => {
    stopRestPolling();
    startRestPolling();
  }, [startRestPolling, stopRestPolling]);

  const switchToWebSocketMode = useCallback(() => {
    stopRestPolling();
    setDataSource('websocket');
  }, [stopRestPolling]);

  // 🧹 CLEANUP
  useEffect(() => {
    return () => {
      stopRestPolling();
    };
  }, [stopRestPolling]);

  return {
    ticker: finalTicker,
    orderbook: finalOrderbook,
    chartData,
    connected: wsConnected,
    connecting: wsConnecting,
    dataSource,
    error: error || wsError,
    refreshData,
    switchToRestMode,
    switchToWebSocketMode
  };
};