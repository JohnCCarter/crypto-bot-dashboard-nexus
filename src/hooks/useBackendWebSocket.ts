/**
 * Backend-Proxied WebSocket Hook
 * Använder backend proxy för att få WebSocket data och undviker browser security issues
 */

import { useState, useEffect, useRef } from 'react';

interface BackendWebSocketData {
  ticker: {
    symbol: string;
    price: number;
    volume: number;
    bid: number;
    ask: number;
    timestamp: number;
  } | null;
  
  connected: boolean;
  error: string | null;
  lastUpdate: number | null;
}

export const useBackendWebSocket = (symbol: string = 'BTCUSD'): BackendWebSocketData => {
  const [ticker, setTicker] = useState<BackendWebSocketData['ticker']>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<number | null>(null);
  
  const pollInterval = useRef<NodeJS.Timeout | null>(null);
  const isActive = useRef(true);

  // Poll WebSocket proxy data from backend
  const pollWebSocketData = async () => {
    if (!isActive.current) return;
    
    try {
      // Get WebSocket status
      const statusResponse = await fetch('/api/ws-proxy/status');
      const statusData = await statusResponse.json();
      
      setConnected(statusData.connected);
      
      if (statusData.error) {
        setError(statusData.error);
      } else {
        setError(null);
      }
      
      // Get ticker data if available
      if (statusData.has_ticker_data) {
        const tickerResponse = await fetch('/api/ws-proxy/ticker');
        
        if (tickerResponse.ok) {
          const tickerData = await tickerResponse.json();
          setTicker(tickerData);
          setLastUpdate(Date.now());
        }
      }
      
    } catch (err) {
      console.error('❌ [Backend WS] Polling error:', err);
      setError('Failed to poll WebSocket data from backend');
      setConnected(false);
    }
  };

  useEffect(() => {
    isActive.current = true;
    
    // Initial fetch
    pollWebSocketData();
    
    // Poll every 1 second for live updates
    pollInterval.current = setInterval(pollWebSocketData, 1000);
    
    return () => {
      isActive.current = false;
      if (pollInterval.current) {
        clearInterval(pollInterval.current);
        pollInterval.current = null;
      }
    };
  }, [symbol]);

  return {
    ticker,
    connected,
    error,
    lastUpdate
  };
};