/**
 * Hybrid Order Book - Real-time orderbook med WebSocket + REST fallback
 * 
 * Features:
 * - Omedelbar initial orderbook via REST
 * - Real-time updates via WebSocket
 * - Visual highlighting av price changes
 * - Graceful fallback till REST polling
 */

import React, { useMemo, useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useHybridMarketData } from '@/hooks/useHybridMarketData';
import { TrendingUp, TrendingDown, Wifi, Activity, RefreshCw, Settings, Heart } from 'lucide-react';
import { useWebSocketMarket } from '@/hooks/useWebSocketMarket';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Loader2 } from 'lucide-react';
import { Alert, AlertDescription, AlertTriangle } from '@/components/ui/alert';
import { OrderBook } from '@/types/trading';

interface HybridOrderBookProps {
  symbol?: string;
  maxLevels?: number;
  showControls?: boolean;
}

export const HybridOrderBook: React.FC<HybridOrderBookProps> = ({
  symbol = 'BTCUSD',
  maxLevels = 10,
  showControls = true
}) => {
  const [mode, setMode] = useState<'websocket' | 'rest'>('websocket');
  const [showDetails, setShowDetails] = useState(false);
  
  // WebSocket data med förbättrade funktioner
  const wsData = useWebSocketMarket(symbol);
  
  // REST data som fallback
  const { data: restOrderbook, isLoading: restLoading, error: restError, refetch } = useQuery<OrderBook>({
    queryKey: ['orderbook', symbol, 'rest'],
    queryFn: () => api.getOrderBook(symbol),
    refetchInterval: mode === 'rest' ? 2000 : false,
    enabled: mode === 'rest' || !wsData.connected
  });

  // Välj data source
  const orderbook = mode === 'websocket' ? wsData.orderbook : restOrderbook;
  const isLoading = mode === 'websocket' ? wsData.connecting : restLoading;
  const error = mode === 'websocket' ? wsData.error : restError;
  const isConnected = mode === 'websocket' ? wsData.connected : !restLoading;

  // Auto-fallback: Byt till REST om WebSocket inte fungerar
  useEffect(() => {
    if (mode === 'websocket' && wsData.error && !wsData.connected) {
      console.log('🔄 [Hybrid] WebSocket failed, falling back to REST');
      setMode('rest');
    }
  }, [mode, wsData.error, wsData.connected]);

  // Beräkna connection status med mer detaljer
  const getConnectionStatus = () => {
    if (mode === 'websocket') {
      if (wsData.connecting) return 'Ansluter...';
      if (!wsData.connected) return 'Frånkopplad';
      
      // Platform status från Bitfinex
      if (wsData.platformStatus === 'maintenance') return 'Underhållsläge';
      if (wsData.platformStatus === 'operative') {
        const latencyText = wsData.latency ? ` (${wsData.latency}ms)` : '';
        return `Live WebSocket${latencyText}`;
      }
      
      return 'WebSocket Ansluten';
    } else {
      return isLoading ? 'Laddar...' : 'REST Polling';
    }
  };

  const getStatusColor = () => {
    if (mode === 'websocket') {
      if (wsData.connecting) return 'text-yellow-500';
      if (!wsData.connected) return 'text-red-500';
      if (wsData.platformStatus === 'maintenance') return 'text-orange-500';
      if (wsData.platformStatus === 'operative') return 'text-green-500';
      return 'text-blue-500';
    } else {
      return isLoading ? 'text-yellow-500' : 'text-blue-500';
    }
  };

  // Beräkna spread
  const spread = orderbook?.asks?.[0] && orderbook?.bids?.[0] 
    ? orderbook.asks[0].price - orderbook.bids[0].price 
    : 0;

  const spreadPercentage = orderbook?.asks?.[0] 
    ? (spread / orderbook.asks[0].price) * 100 
    : 0;

  if (isLoading) {
    return (
      <Card className="h-[600px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Orderbook - {symbol}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-full">
          <div className="flex items-center space-x-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Laddar orderbook...</span>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !orderbook) {
    return (
      <Card className="h-[600px]">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Orderbook - {symbol}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-full">
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Kunde inte ladda orderbook: {typeof error === 'string' ? error : error?.message || 'Okänt fel'}
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  const visibleBids = orderbook.bids.slice(0, maxLevels);
  const visibleAsks = orderbook.asks.slice(0, maxLevels).reverse();

  return (
    <Card className="h-[600px]">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            Orderbook - {symbol}
          </CardTitle>
          
          <div className="flex items-center gap-2">
            {/* Nya status indikatorer */}
            <div className="flex items-center gap-1 text-xs">
              <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
              <span className={getStatusColor()}>{getConnectionStatus()}</span>
            </div>
            
            {/* Heartbeat indikator för WebSocket */}
            {mode === 'websocket' && wsData.lastHeartbeat && (
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <Heart className="h-3 w-3" />
                <span>{Math.round((Date.now() - wsData.lastHeartbeat) / 1000)}s</span>
              </div>
            )}
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDetails(!showDetails)}
              className="h-7"
            >
              <Settings className="h-3 w-3" />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => mode === 'rest' ? refetch() : wsData.connect()}
              className="h-7"
            >
              <RefreshCw className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {/* Kontrollpanel */}
        {showDetails && (
          <div className="mt-3 p-3 bg-muted rounded-lg space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Datakälla:</span>
              <div className="flex gap-1">
                <Button
                  variant={mode === 'websocket' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setMode('websocket')}
                  className="h-7 text-xs"
                >
                  WebSocket
                </Button>
                <Button
                  variant={mode === 'rest' ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setMode('rest')}
                  className="h-7 text-xs"
                >
                  REST
                </Button>
              </div>
            </div>
            
            {/* WebSocket stats */}
            {mode === 'websocket' && (
              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-muted-foreground">Platform Status:</span>
                  <p className="font-mono">
                    {wsData.platformStatus === 'operative' ? '✅ Operativ' : 
                     wsData.platformStatus === 'maintenance' ? '🔧 Underhåll' : 
                     '❓ Okänd'}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Latency:</span>
                  <p className="font-mono">
                    {wsData.latency ? `${wsData.latency}ms` : 'Mäter...'}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Senaste Heartbeat:</span>
                  <p className="font-mono">
                    {wsData.lastHeartbeat 
                      ? `${Math.round((Date.now() - wsData.lastHeartbeat) / 1000)}s sedan`
                      : 'Väntar...'}
                  </p>
                </div>
                <div>
                  <span className="text-muted-foreground">Anslutning:</span>
                  <p className="font-mono">
                    {wsData.connected ? '🟢 Ansluten' : '🔴 Frånkopplad'}
                  </p>
                </div>
              </div>
            )}
            
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Spread:</span>
              <span className="font-mono">
                ${spread.toFixed(2)} ({spreadPercentage.toFixed(3)}%)
              </span>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-300 rounded text-red-700">
            Error: {error}
          </div>
        )}

        {/* Spread Information */}
        {spread && (
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <div className="flex justify-between items-center">
              <div className="text-sm text-gray-600">
                <strong>Spread:</strong> {spread.toFixed(2)}
              </div>
              <div className="text-sm text-gray-600">
                Percentage: {spreadPercentage.toFixed(3)}%
              </div>
            </div>
          </div>
        )}

        <div className="grid grid-cols-2 gap-4">
          {/* Bids (Buy Orders) */}
          <div>
            <div className="flex items-center mb-2">
              <TrendingUp className="w-4 h-4 text-green-600 mr-1" />
              <h3 className="font-semibold text-green-600">Bids</h3>
            </div>
            
            <div className="space-y-1">
              <div className="grid grid-cols-2 gap-2 text-xs font-medium text-gray-500 mb-1">
                <div>Price (USD)</div>
                <div className="text-right">Amount</div>
              </div>
              
              {visibleBids.length > 0 ? (
                visibleBids.map((bid, index) => (
                  <div
                    key={`bid-${bid.price}-${index}`}
                    className="grid grid-cols-2 gap-2 text-sm py-1 px-2 rounded bg-green-50 hover:bg-green-100 transition-colors"
                  >
                    <div className="font-mono text-green-700">
                      {bid.price.toFixed(2)}
                    </div>
                    <div className="text-right font-mono text-gray-700">
                      {bid.amount.toFixed(4)}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-500 py-4">
                  {isLoading ? 'Loading bids...' : 'No bid data'}
                </div>
              )}
            </div>
          </div>

          {/* Asks (Sell Orders) */}
          <div>
            <div className="flex items-center mb-2">
              <TrendingDown className="w-4 h-4 text-red-600 mr-1" />
              <h3 className="font-semibold text-red-600">Asks</h3>
            </div>
            
            <div className="space-y-1">
              <div className="grid grid-cols-2 gap-2 text-xs font-medium text-gray-500 mb-1">
                <div>Price (USD)</div>
                <div className="text-right">Amount</div>
              </div>
              
              {visibleAsks.length > 0 ? (
                visibleAsks.map((ask, index) => (
                  <div
                    key={`ask-${ask.price}-${index}`}
                    className="grid grid-cols-2 gap-2 text-sm py-1 px-2 rounded bg-red-50 hover:bg-red-100 transition-colors"
                  >
                    <div className="font-mono text-red-700">
                      {ask.price.toFixed(2)}
                    </div>
                    <div className="text-right font-mono text-gray-700">
                      {ask.amount.toFixed(4)}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-500 py-4">
                  {isLoading ? 'Loading asks...' : 'No ask data'}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Current Price Display */}
        {wsData.ticker && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg text-center">
            <div className="text-sm text-gray-600 mb-1">Current Price</div>
            <div className="text-2xl font-bold text-blue-600">
              {wsData.ticker.price.toFixed(2)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Last update: {new Date(wsData.ticker.timestamp).toLocaleTimeString()}
            </div>
          </div>
        )}

        {/* Status Footer */}
        <div className="mt-4 flex justify-between items-center text-xs text-gray-500">
          <div>
            Levels: {visibleBids.length + visibleAsks.length} | 
            Source: {mode === 'websocket' ? 'WebSocket' : 'REST'}
          </div>
          
          <div className="flex items-center space-x-2">
            {mode === 'websocket' && isConnected && (
              <div className="flex items-center text-green-600">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-1"></div>
                Real-time
              </div>
            )}
            
            {!isConnected && mode === 'rest' && (
              <div className="flex items-center text-yellow-600">
                <div className="w-2 h-2 bg-yellow-500 rounded-full mr-1"></div>
                Polling
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};