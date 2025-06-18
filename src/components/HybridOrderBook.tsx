/**
 * Hybrid Order Book - Real-time orderbook med WebSocket + REST fallback
 * 
 * Features:
 * - Omedelbar initial orderbook via REST
 * - Real-time updates via WebSocket
 * - Visual highlighting av price changes
 * - Graceful fallback till REST polling
 */

import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useHybridMarketData } from '@/hooks/useHybridMarketData';
import { TrendingUp, TrendingDown, Wifi, Activity, RefreshCw } from 'lucide-react';

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
  const {
    orderbook,
    ticker,
    connected,
    connecting,
    dataSource,
    error,
    refreshData,
    switchToRestMode,
    switchToWebSocketMode
  } = useHybridMarketData(symbol);

  // Format price for display
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  // Format amount with proper decimals
  const formatAmount = (amount: number) => {
    return amount.toFixed(4);
  };

  // Get limited orderbook data
  const limitedOrderbook = useMemo(() => {
    if (!orderbook) return { bids: [], asks: [] };
    
    return {
      bids: orderbook.bids.slice(0, maxLevels),
      asks: orderbook.asks.slice(0, maxLevels)
    };
  }, [orderbook, maxLevels]);

  // Calculate spread
  const spread = useMemo(() => {
    if (!limitedOrderbook.bids.length || !limitedOrderbook.asks.length) return null;
    
    const bestBid = limitedOrderbook.bids[0]?.price || 0;
    const bestAsk = limitedOrderbook.asks[0]?.price || 0;
    const spreadValue = bestAsk - bestBid;
    const spreadPercent = (spreadValue / bestBid) * 100;
    
    return {
      value: spreadValue,
      percent: spreadPercent,
      bestBid,
      bestAsk
    };
  }, [limitedOrderbook]);

  // Connection status badge
  const getConnectionBadge = () => {
    switch (dataSource) {
      case 'websocket':
        return (
          <Badge variant="default" className="bg-green-500">
            <Wifi className="w-3 h-3 mr-1" />
            Live
          </Badge>
        );
      case 'rest':
        return (
          <Badge variant="secondary" className="bg-yellow-500">
            <Activity className="w-3 h-3 mr-1" />
            Polling
          </Badge>
        );
      default:
        return (
          <Badge variant="outline">
            Connecting...
          </Badge>
        );
    }
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-2">
          <CardTitle className="text-lg font-bold">
            Order Book - {symbol}
          </CardTitle>
          {getConnectionBadge()}
        </div>

        {showControls && (
          <div className="flex space-x-1">
            <Button
              variant="outline"
              size="sm"
              onClick={refreshData}
              disabled={connecting}
            >
              <RefreshCw className={`w-4 h-4 ${connecting ? 'animate-spin' : ''}`} />
            </Button>
            
            {dataSource !== 'websocket' && (
              <Button
                variant="outline"
                size="sm"
                onClick={switchToWebSocketMode}
                className="text-green-600"
              >
                <Wifi className="w-4 h-4" />
              </Button>
            )}
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
                <strong>Spread:</strong> {formatPrice(spread.value)} ({spread.percent.toFixed(4)}%)
              </div>
              <div className="text-sm text-gray-600">
                Best: {formatPrice(spread.bestBid)} / {formatPrice(spread.bestAsk)}
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
              
              {limitedOrderbook.bids.length > 0 ? (
                limitedOrderbook.bids.map((bid, index) => (
                  <div
                    key={`bid-${bid.price}-${index}`}
                    className="grid grid-cols-2 gap-2 text-sm py-1 px-2 rounded bg-green-50 hover:bg-green-100 transition-colors"
                  >
                    <div className="font-mono text-green-700">
                      {formatPrice(bid.price)}
                    </div>
                    <div className="text-right font-mono text-gray-700">
                      {formatAmount(bid.amount)}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-500 py-4">
                  {connecting ? 'Loading bids...' : 'No bid data'}
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
              
              {limitedOrderbook.asks.length > 0 ? (
                limitedOrderbook.asks.map((ask, index) => (
                  <div
                    key={`ask-${ask.price}-${index}`}
                    className="grid grid-cols-2 gap-2 text-sm py-1 px-2 rounded bg-red-50 hover:bg-red-100 transition-colors"
                  >
                    <div className="font-mono text-red-700">
                      {formatPrice(ask.price)}
                    </div>
                    <div className="text-right font-mono text-gray-700">
                      {formatAmount(ask.amount)}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-center text-gray-500 py-4">
                  {connecting ? 'Loading asks...' : 'No ask data'}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Current Price Display */}
        {ticker && (
          <div className="mt-4 p-3 bg-blue-50 rounded-lg text-center">
            <div className="text-sm text-gray-600 mb-1">Current Price</div>
            <div className="text-2xl font-bold text-blue-600">
              {formatPrice(ticker.price)}
            </div>
            <div className="text-xs text-gray-500 mt-1">
              Last update: {new Date(ticker.timestamp).toLocaleTimeString()}
            </div>
          </div>
        )}

        {/* Status Footer */}
        <div className="mt-4 flex justify-between items-center text-xs text-gray-500">
          <div>
            Levels: {limitedOrderbook.bids.length + limitedOrderbook.asks.length} | 
            Source: {dataSource}
          </div>
          
          <div className="flex items-center space-x-2">
            {connected && dataSource === 'websocket' && (
              <div className="flex items-center text-green-600">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-1"></div>
                Real-time
              </div>
            )}
            
            {!connected && dataSource === 'rest' && (
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