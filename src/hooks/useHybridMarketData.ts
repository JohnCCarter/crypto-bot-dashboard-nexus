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
    try {
      console.log('🔄 [Hybrid] Loading initial data via REST...');
      
      // Parallella REST calls för snabb initial load
      const [tickerData, orderbookData, ohlcvData] = await Promise.all([
        api.getMarketTicker(symbol).catch(() => null),
        api.getOrderBook(symbol, 20).catch(() => null),
        api.getChartData(symbol, '5m', 100).catch(() => [])
      ]);

      if (tickerData) {
        setRestTicker(tickerData);
        console.log(`✅ [Hybrid] Initial ticker loaded: $${tickerData.last}`);
      }

      if (orderbookData) {
        setRestOrderbook(orderbookData);
        console.log(`✅ [Hybrid] Initial orderbook loaded: ${orderbookData.bids?.length} bids`);
      }

      if (ohlcvData && ohlcvData.length > 0) {
        setChartData(ohlcvData);
        console.log(`✅ [Hybrid] Initial chart data loaded: ${ohlcvData.length} candles`);
      }

      initialLoadComplete.current = true;
      setError(null);
      
    } catch (err) {
      console.error('❌ [Hybrid] Initial data load failed:', err);
      setError('Failed to load initial market data');
    }
  }, [symbol]);

  // 📡 REST POLLING FALLBACK - När WebSocket är disconnected
  const startRestPolling = useCallback(() => {
    if (restPollingInterval.current) return;

    console.log('🔄 [Hybrid] Starting REST polling fallback...');
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
          console.log(`🔄 [Hybrid] REST ticker update: $${tickerData.last}`);
        }

        if (orderbookData) {
          setRestOrderbook(orderbookData);
        }

        lastRestUpdate.current = now;
        setError(null);

      } catch (err) {
        console.error('❌ [Hybrid] REST polling error:', err);
        setError('REST polling failed');
      }
    }, 2000); // Poll every 2 seconds
  }, [symbol]);

  // 🛑 STOP REST POLLING
  const stopRestPolling = useCallback(() => {
    if (restPollingInterval.current) {
      clearInterval(restPollingInterval.current);
      restPollingInterval.current = null;
      setIsRestPolling(false);
      console.log('⏹️ [Hybrid] REST polling stopped');
    }
  }, []);

  // 🧠 SMART DATA SOURCE MANAGEMENT
  useEffect(() => {
    if (wsConnected && enableWebSocket) {
      // WebSocket is connected - use it as primary source
      stopRestPolling();
      setDataSource('websocket');
      console.log('✅ [Hybrid] Switched to WebSocket mode');
      
    } else if (enableWebSocket && !wsConnecting) {
      // WebSocket failed or disabled - fallback to REST
      startRestPolling();
      console.log('⚠️ [Hybrid] WebSocket unavailable, using REST fallback');
      
    } else if (!enableWebSocket) {
      // Pure REST mode
      startRestPolling();
      setDataSource('rest');
    }

    return () => stopRestPolling();
  }, [wsConnected, wsConnecting, enableWebSocket, startRestPolling, stopRestPolling]);

  // 🔄 INITIAL LOAD EFFECT
  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);

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

  // 📊 LIVE CHART UPDATES - Merge WebSocket ticker updates into chart
  useEffect(() => {
    if (finalTicker && chartData.length > 0) {
      setChartData(prevData => {
        const updatedData = [...prevData];
        const lastCandle = updatedData[updatedData.length - 1];
        
        if (lastCandle) {
          // Update the latest candle with live price
          const currentTime = Date.now();
          const candleTime = lastCandle.timestamp;
          const timeDiff = currentTime - candleTime;
          
          // If within same 5-minute window, update current candle
          if (timeDiff < 5 * 60 * 1000) {
            lastCandle.close = finalTicker.price;
            lastCandle.high = Math.max(lastCandle.high, finalTicker.price);
            lastCandle.low = Math.min(lastCandle.low, finalTicker.price);
            lastCandle.volume += finalTicker.volume * 0.01; // Small volume increment
          }
        }
        
        return updatedData;
      });
    }
  }, [finalTicker, chartData.length]);

  // 🔧 UTILITY METHODS
  const refreshData = useCallback(async () => {
    console.log('🔄 [Hybrid] Manual data refresh triggered');
    await loadInitialData();
  }, [loadInitialData]);

  const switchToRestMode = useCallback(() => {
    console.log('🔄 [Hybrid] Manually switching to REST mode');
    stopRestPolling();
    startRestPolling();
  }, [startRestPolling, stopRestPolling]);

  const switchToWebSocketMode = useCallback(() => {
    console.log('🔄 [Hybrid] Manually switching to WebSocket mode');
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