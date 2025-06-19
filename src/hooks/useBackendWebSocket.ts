/**
 * Backend-Proxied WebSocket Hook - Performance Optimized
 * Använder backend proxy med smart caching och rate limiting
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

// Global cache för att dela data mellan komponenter
let globalCache: {
  ticker: BackendWebSocketData['ticker'];
  connected: boolean;
  error: string | null;
  lastUpdate: number;
  lastFetch: number;
} | null = null;

// Global subscribers för att uppdatera alla komponenter
const subscribers = new Set<(data: BackendWebSocketData) => void>();

// Rate limiting - max 1 API call per 3 sekunder
const MIN_FETCH_INTERVAL = 3000;
let fetchPromise: Promise<void> | null = null;

export const useBackendWebSocket = (symbol: string = 'BTCUSD'): BackendWebSocketData => {
  const [data, setData] = useState<BackendWebSocketData>({
    ticker: globalCache?.ticker || null,
    connected: globalCache?.connected || false,
    error: globalCache?.error || null,
    lastUpdate: globalCache?.lastUpdate || null
  });
  
  const isActive = useRef(true);

  // Smart fetch with caching and rate limiting
  const fetchWebSocketData = async (): Promise<void> => {
    const now = Date.now();
    
    // Rate limiting - använd cache om för ny data
    if (globalCache && (now - globalCache.lastFetch) < MIN_FETCH_INTERVAL) {
      return;
    }

    // Prevent duplicate API calls
    if (fetchPromise) {
      return fetchPromise;
    }

    fetchPromise = (async () => {
      try {
        // Single API call för både status och ticker
        const [statusResponse, tickerResponse] = await Promise.all([
          fetch('/api/ws-proxy/status'),
          fetch('/api/ws-proxy/ticker').catch(() => null) // Optional ticker
        ]);
        
        const statusData = await statusResponse.json();
        
        const newData: BackendWebSocketData = {
          ticker: null,
          connected: statusData.connected,
          error: statusData.error,
          lastUpdate: now
        };

        // Get ticker if available
        if (tickerResponse?.ok) {
          const tickerData = await tickerResponse.json();
          newData.ticker = tickerData;
        }

        // Update global cache
        globalCache = {
          ...newData,
          lastFetch: now
        };

        // Notify all subscribers
        subscribers.forEach(callback => callback(newData));
        
      } catch (err) {
        // Rate limited error logging - max 1 error log per 10 seconds
        const errorKey = 'lastErrorLog';
        const lastErrorLog = parseInt(sessionStorage.getItem(errorKey) || '0');
        
        if (now - lastErrorLog > 10000) {
          console.error('❌ [Backend WS] Polling error:', err);
          sessionStorage.setItem(errorKey, now.toString());
        }

        const errorData: BackendWebSocketData = {
          ticker: globalCache?.ticker || null,
          connected: false,
          error: 'Failed to poll WebSocket data from backend',
          lastUpdate: now
        };

        globalCache = {
          ...errorData,
          lastFetch: now
        };

        subscribers.forEach(callback => callback(errorData));
      } finally {
        fetchPromise = null;
      }
    })();

    return fetchPromise;
  };

  useEffect(() => {
    isActive.current = true;
    
    // Subscribe to global updates
    const updateCallback = (newData: BackendWebSocketData) => {
      if (isActive.current) {
        setData(newData);
      }
    };
    
    subscribers.add(updateCallback);
    
    // Initial fetch if no cache or cache is stale
    if (!globalCache || (Date.now() - globalCache.lastFetch) > MIN_FETCH_INTERVAL) {
      fetchWebSocketData();
    }
    
    // Slower polling - var 5:e sekund istället för varje sekund
    const pollInterval = setInterval(() => {
      fetchWebSocketData();
    }, 5000);
    
    return () => {
      isActive.current = false;
      subscribers.delete(updateCallback);
      clearInterval(pollInterval);
    };
  }, [symbol]);

  return data;
};