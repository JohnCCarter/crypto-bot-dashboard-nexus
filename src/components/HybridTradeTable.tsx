/**
 * Hybrid Trade Table - Live PnL Tracking med WebSocket + REST - Performance Optimized
 * 
 * Features:
 * - Live profit/loss tracking med real-time pricing
 * - Real-time position valuation
 * - Live percentage returns
 * - Smart fallback till REST data
 * - Performance optimizations med memoization
 */

import React, { useMemo, memo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { Trade } from '@/types/trading';
import { TrendingUp, TrendingDown, Activity, RefreshCw, Wifi, DollarSign } from 'lucide-react';
import { useWebSocketMarket } from '@/hooks/useWebSocketMarket';

// Enhanced Trade interface with live data
interface EnhancedTrade extends Trade {
  unrealizedPnl: number;
  pnlPercentage: number;
  currentPrice: number;
}

interface HybridTradeTableProps {
  symbol?: string;
  maxTrades?: number;
}

export const HybridTradeTable: React.FC<HybridTradeTableProps> = memo(({ 
  symbol = 'BTCUSD',
  maxTrades = 10 
}) => {
  // Get live pricing data via WebSocket Market
  const wsData = useWebSocketMarket(symbol);
  
  // Get trades data via REST
  const { data: trades = [], isLoading, error, refetch } = useQuery<Trade[]>({
    queryKey: ['trades', symbol],
    queryFn: () => api.getActiveTrades(),
    refetchInterval: 5000,
    staleTime: 2000
  });

  // Enhance trades with live pricing and calculate P&L
  const enhancedTrades: EnhancedTrade[] = React.useMemo(() => {
    if (!trades) return [];
    
    const currentPrice = wsData.ticker?.price || 0;
    
    return trades.slice(0, maxTrades).map((trade): EnhancedTrade => {
      const direction = trade.side === 'buy' ? 1 : -1;
      const unrealizedPnl = currentPrice > 0 ? (currentPrice - trade.entry_price) * direction * trade.amount : 0;
      const pnlPercentage = trade.entry_price > 0 ? (unrealizedPnl / (trade.entry_price * trade.amount)) * 100 : 0;
      
      return {
        ...trade,
        unrealizedPnl,
        pnlPercentage,
        currentPrice
      };
    });
  }, [trades, wsData.ticker, maxTrades]);

  // Safe format functions with null checks
  const formatCurrency = (value: number | null | undefined) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '$0.00';
    }
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatCrypto = (value: number | null | undefined, decimals = 6) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '0.000000';
    }
    return value.toFixed(decimals);
  };

  const formatPercentage = (value: number | null | undefined) => {
    if (value === null || value === undefined || isNaN(value)) {
      return '0.00';
    }
    return value.toFixed(2);
  };

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Live Active Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={`skeleton-${i}`} className="animate-pulse flex justify-between">
                <div className="h-4 bg-muted rounded w-1/4"></div>
                <div className="h-4 bg-muted rounded w-1/6"></div>
                <div className="h-4 bg-muted rounded w-1/6"></div>
                <div className="h-4 bg-muted rounded w-1/6"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Live Active Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4">
            <p className="text-red-500">Failed to load trades data</p>
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
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <DollarSign className="w-4 h-4" />
            Live Active Trades ({enhancedTrades.length})
          </CardTitle>
          
          <div className="flex items-center gap-2">
            {wsData.connected ? (
              <Badge variant="default" className="bg-green-500">
                <Wifi className="w-3 h-3 mr-1" />
                Live P&L
              </Badge>
            ) : wsData.error ? (
              <Badge variant="destructive" className="max-w-48 truncate" title={wsData.error}>
                <Activity className="w-3 h-3 mr-1" />
                {wsData.error.includes('Failed to connect') ? 'Connection Failed' : 'WebSocket Error'}
              </Badge>
            ) : (
              <Badge variant="secondary">
                <Activity className="w-3 h-3 mr-1" />
                Static P&L
              </Badge>
            )}
            
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="w-3 h-3" />
            </Button>
          </div>
        </div>

        {/* Live Portfolio Summary */}
        {enhancedTrades.length > 0 && (
          <div className="mt-3 p-3 bg-muted rounded-lg">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className={`text-lg font-bold ${
                  enhancedTrades[0].unrealizedPnl >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(enhancedTrades[0].unrealizedPnl)}
                </div>
                <div className="text-xs text-muted-foreground">Total P&L</div>
              </div>
              
              <div>
                <div className={`text-lg font-bold ${
                  enhancedTrades[0].pnlPercentage >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {enhancedTrades[0].pnlPercentage >= 0 ? '+' : ''}{formatPercentage(enhancedTrades[0].pnlPercentage)}%
                </div>
                <div className="text-xs text-muted-foreground">Total Return</div>
              </div>
              
              <div>
                <div className="text-lg font-bold">
                  {enhancedTrades.filter(t => t.unrealizedPnl > 0).length}/{enhancedTrades.filter(t => t.unrealizedPnl < 0).length}
                </div>
                <div className="text-xs text-muted-foreground">W/L Ratio</div>
              </div>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent>
        {enhancedTrades.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>No active trades</p>
            <p className="text-xs mt-1">Open positions will appear here with live P&L</p>
          </div>
        ) : (
          <div className="space-y-4">
            {/* Table Header */}
            <div className="grid grid-cols-6 gap-2 text-xs font-medium text-muted-foreground border-b pb-2">
              <span>Symbol</span>
              <span>Side</span>
              <span>Amount</span>
              <span>Entry → Current</span>
              <span>Live P&L</span>
              <span>Return %</span>
            </div>
            
            {/* Trade Rows */}
            {enhancedTrades.map((trade, index) => (
              <div key={`trade-${trade.id || index}-${index}`} 
                   className={`grid grid-cols-6 gap-2 items-center p-2 rounded-lg transition-colors ${
                     trade.unrealizedPnl > 0 ? 'bg-green-50 border border-green-200' :
                     trade.unrealizedPnl < 0 ? 'bg-red-50 border border-red-200' :
                     'bg-muted/50'
                   }`}>
                
                {/* Symbol */}
                <span className="font-medium text-sm">{trade.symbol}</span>
                
                {/* Side */}
                <Badge variant={trade.side === 'buy' ? 'default' : 'destructive'} className="w-fit text-xs">
                  {trade.side?.toUpperCase() || 'UNKNOWN'}
                </Badge>
                
                {/* Amount */}
                <span className="text-sm font-mono">{formatCrypto(trade.amount, 4)}</span>
                
                {/* Price Movement */}
                <div className="text-sm">
                  <div className="font-mono">{formatCurrency(trade.entry_price)}</div>
                  <div className={`font-mono text-xs ${
                    trade.unrealizedPnl >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    → {formatCurrency(trade.currentPrice)}
                  </div>
                </div>
                
                {/* Live P&L */}
                <div className={`text-sm font-medium ${
                  trade.unrealizedPnl >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  <div className="flex items-center gap-1">
                    {trade.unrealizedPnl >= 0 ? 
                      <TrendingUp className="w-3 h-3" /> : 
                      <TrendingDown className="w-3 h-3" />
                    }
                    {formatCurrency(Math.abs(trade.unrealizedPnl))}
                  </div>
                </div>
                
                {/* Return % */}
                <div className={`text-sm font-bold ${
                  trade.pnlPercentage >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {trade.pnlPercentage >= 0 ? '+' : ''}{formatPercentage(trade.pnlPercentage)}%
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Live Data Status */}
        <div className="flex justify-between items-center text-xs text-muted-foreground pt-4 border-t mt-4">
          <span>
            Market price: {wsData.ticker ? formatCurrency(wsData.ticker.price) : 'Loading...'}
          </span>
          <div className="flex items-center gap-2">
            {wsData.connected ? (
              <span className="text-green-600">🟢 Live P&L updates</span>
            ) : wsData.error ? (
              <div className="flex items-center gap-2">
                <span className="text-red-600">🔴 WebSocket Error</span>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={() => refetch()} 
                  className="h-6 px-2 text-xs"
                >
                  Refresh
                </Button>
              </div>
            ) : (
              <span className="text-yellow-600">🟡 Static P&L</span>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
});

HybridTradeTable.displayName = 'HybridTradeTable';