/**
 * Hybrid Order Book - Real-time orderbook med WebSocket + REST fallback
 * 
 * Features:
 * - Live orderbook via WebSocket (real-time updates)
 * - Smart fallback till REST data vid anslutningsproblem
 * - Depth visualization med spread indikator
 * - Optimistic UI med skelett-loading
 */

import React, { useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useGlobalWebSocketMarket } from '@/contexts/WebSocketMarketProvider';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { OrderBook } from '@/types/trading';
import { Activity, Wifi, RefreshCw, TrendingUp, TrendingDown } from 'lucide-react';

interface HybridOrderBookProps {
  symbol?: string;
  maxLevels?: number;
  showSpread?: boolean;
}

export const HybridOrderBook: React.FC<HybridOrderBookProps> = ({ 
  symbol = 'BTCUSD',
  maxLevels = 10,
  showSpread = true 
}) => {
  // Get global WebSocket data (shared single connection)
  const { 
    connected, 
    getOrderbookForSymbol, 
    subscribeToSymbol,
    platformStatus
  } = useGlobalWebSocketMarket();
  
  // Subscribe to symbol on mount
  useEffect(() => {
    subscribeToSymbol(symbol);
    
    return () => {
      // Note: Don't unsubscribe automatically as other components might use the same symbol
      // unsubscribeFromSymbol(symbol);
    };
  }, [symbol, subscribeToSymbol]);
  
  // Get orderbook data for this specific symbol
  const wsOrderbook = getOrderbookForSymbol(symbol);
  
  // REST fallback data
  const { data: restOrderbook, isLoading, error, refetch } = useQuery<OrderBook>({
    queryKey: ['orderbook', symbol],
    queryFn: () => api.getOrderBook(symbol),
    refetchInterval: connected ? 10000 : 2000, // Slower polling if WS connected
    staleTime: 1000,
    enabled: !connected || !wsOrderbook // Only fetch if no WS data
  });

  // Use WebSocket data if available, otherwise fallback to REST
  const orderbook = wsOrderbook || restOrderbook;

  // Process orderbook data for display
  const processedData = useMemo(() => {
    if (!orderbook) {
      return {
        bids: [],
        asks: [],
        spread: 0,
        spreadPct: 0,
        midPrice: 0
      };
    }

    // Limit levels and sort
    const bids = orderbook.bids
      .sort((a, b) => b.price - a.price)
      .slice(0, maxLevels);
    
    const asks = orderbook.asks
      .sort((a, b) => a.price - b.price)
      .slice(0, maxLevels);

    // Calculate spread
    const bestBid = bids[0]?.price || 0;
    const bestAsk = asks[0]?.price || 0;
    const spread = bestAsk - bestBid;
    const midPrice = (bestBid + bestAsk) / 2;
    const spreadPct = midPrice > 0 ? (spread / midPrice) * 100 : 0;

    // Calculate cumulative volumes for depth visualization
    let cumBidVolume = 0;
    let cumAskVolume = 0;
    
    const bidsWithCum = bids.map(bid => {
      cumBidVolume += bid.amount;
      return { ...bid, cumulative: cumBidVolume };
    });
    
    const asksWithCum = asks.map(ask => {
      cumAskVolume += ask.amount;
      return { ...ask, cumulative: cumAskVolume };
    });

    const maxCumVolume = Math.max(cumBidVolume, cumAskVolume);

    return {
      bids: bidsWithCum.map(bid => ({
        ...bid,
        depthPct: maxCumVolume > 0 ? (bid.cumulative / maxCumVolume) * 100 : 0
      })),
      asks: asksWithCum.map(ask => ({
        ...ask,
        depthPct: maxCumVolume > 0 ? (ask.cumulative / maxCumVolume) * 100 : 0
      })),
      spread,
      spreadPct,
      midPrice,
      bestBid,
      bestAsk
    };
  }, [orderbook, maxLevels]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  const formatAmount = (amount: number) => {
    return amount.toFixed(6);
  };

  if (isLoading && !orderbook) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Order Book</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="animate-pulse flex justify-between">
                <div className="h-4 bg-muted rounded w-1/3"></div>
                <div className="h-4 bg-muted rounded w-1/4"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error && !orderbook) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Order Book</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4">
            <p className="text-red-500">Failed to load orderbook</p>
            <Button variant="outline" size="sm" onClick={() => refetch()} className="mt-2">
              <RefreshCw className="w-4 h-4 mr-2" />
              Retry
            </Button>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">Order Book ({symbol})</CardTitle>
          
          <div className="flex items-center gap-2">
            {connected ? (
              <Badge variant="default" className="bg-green-500">
                <Wifi className="w-3 h-3 mr-1" />
                Live
              </Badge>
            ) : (
              <Badge variant="secondary">
                <Activity className="w-3 h-3 mr-1" />
                REST
              </Badge>
            )}
            
            {platformStatus === 'maintenance' && (
              <Badge variant="destructive">Maintenance</Badge>
            )}
            
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Spread Information */}
        {showSpread && processedData.spread > 0 && (
          <div className="text-center p-3 bg-muted rounded-lg">
            <div className="text-lg font-bold">
              {formatPrice(processedData.midPrice)}
            </div>
            <div className="text-sm text-muted-foreground">
              Mid Price • Spread: {formatPrice(processedData.spread)} ({processedData.spreadPct.toFixed(3)}%)
            </div>
          </div>
        )}

        {/* Orderbook */}
        <div className="grid grid-cols-2 gap-4">
          {/* Bids (Buy Orders) */}
          <div>
            <div className="flex justify-between text-xs font-semibold text-muted-foreground mb-2">
              <span>Price</span>
              <span>Amount</span>
            </div>
            <div className="space-y-1">
              {processedData.bids.map((bid, i) => (
                <div 
                  key={`bid-${i}`} 
                  className="relative flex justify-between text-xs p-1 rounded"
                  style={{
                    background: `linear-gradient(to left, rgba(34, 197, 94, 0.1) ${bid.depthPct}%, transparent ${bid.depthPct}%)`
                  }}
                >
                  <span className="text-green-600 font-mono">
                    {formatPrice(bid.price)}
                  </span>
                  <span className="text-muted-foreground">
                    {formatAmount(bid.amount)}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Asks (Sell Orders) */}
          <div>
            <div className="flex justify-between text-xs font-semibold text-muted-foreground mb-2">
              <span>Price</span>
              <span>Amount</span>
            </div>
            <div className="space-y-1">
              {processedData.asks.map((ask, i) => (
                <div 
                  key={`ask-${i}`} 
                  className="relative flex justify-between text-xs p-1 rounded"
                  style={{
                    background: `linear-gradient(to right, rgba(239, 68, 68, 0.1) ${ask.depthPct}%, transparent ${ask.depthPct}%)`
                  }}
                >
                  <span className="text-red-600 font-mono">
                    {formatPrice(ask.price)}
                  </span>
                  <span className="text-muted-foreground">
                    {formatAmount(ask.amount)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Best Bid/Ask Summary */}
        <div className="flex justify-between items-center pt-2 border-t text-xs">
          <div className="flex items-center gap-1 text-green-600">
            <TrendingUp className="w-3 h-3" />
            <span>Best Bid: {formatPrice(processedData.bestBid)}</span>
          </div>
          <div className="flex items-center gap-1 text-red-600">
            <TrendingDown className="w-3 h-3" />
            <span>Best Ask: {formatPrice(processedData.bestAsk)}</span>
          </div>
        </div>

        {/* Data Source Status */}
        <div className="text-xs text-muted-foreground text-center">
          {connected && wsOrderbook ? '🟢 Real-time WebSocket data' : '🟡 REST API data'}
        </div>
      </CardContent>
    </Card>
  );
};