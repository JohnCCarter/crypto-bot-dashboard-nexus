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
import { useBackendWebSocket } from '@/hooks/useBackendWebSocket';

// Enhanced Trade interface with live data
interface EnhancedTrade extends Trade {
  current_price: number;
  live_pnl: number;
  live_pnl_pct: number;
  current_value: number;
  cost_basis: number;
  price_change: number;
  price_change_pct: number;
  is_winning: boolean;
  is_losing: boolean;
}

interface HybridTradeTableProps {
  symbol?: string;
  maxTrades?: number;
}

export const HybridTradeTable: React.FC<HybridTradeTableProps> = memo(({ 
  symbol = 'BTCUSD',
  maxTrades = 10 
}) => {
  // Get live pricing data via Backend WebSocket Proxy
  const wsData = useBackendWebSocket(symbol);
  
  // Get trades data via REST
  const { data: trades = [], isLoading, error, refetch } = useQuery<Trade[]>({
    queryKey: ['activeTrades'],
    queryFn: api.getActiveTrades,
    refetchInterval: 5000, // Fallback polling
    staleTime: 2000
  });

  // Calculate live trade metrics with current market price
  const liveTradesData = useMemo(() => {
    if (!trades.length || !wsData.ticker) {
      return {
        trades: trades as EnhancedTrade[],
        totalPnL: 0,
        totalPnLPct: 0,
        totalValue: 0,
        winners: 0,
        losers: 0
      };
    }

    const currentPrice = wsData.ticker.price;
    
    // Safety check for currentPrice
    if (!currentPrice || typeof currentPrice !== 'number' || isNaN(currentPrice)) {
      console.warn('[HybridTradeTable] Invalid current price:', currentPrice);
      return {
        trades: trades as EnhancedTrade[],
        totalPnL: 0,
        totalPnLPct: 0,
        totalValue: 0,
        winners: 0,
        losers: 0
      };
    }

    let totalPnL = 0;
    let totalValue = 0;
    let totalCostBasis = 0;
    let winners = 0;
    let losers = 0;

    const enhancedTrades: EnhancedTrade[] = trades
      .filter(trade => {
        // Filter out invalid trades
        return trade && 
               typeof trade.amount === 'number' && 
               typeof trade.entry_price === 'number' &&
               !isNaN(trade.amount) && 
               !isNaN(trade.entry_price) &&
               trade.amount > 0 && 
               trade.entry_price > 0;
      })
      .map(trade => {
        // Calculate live PnL with safety checks
        const priceChange = currentPrice - trade.entry_price;
        const positionMultiplier = trade.side === 'buy' ? 1 : -1;
        const livePnL = priceChange * trade.amount * positionMultiplier;
        const livePnLPct = (priceChange / trade.entry_price) * 100 * positionMultiplier;
        
        // Current position value
        const currentValue = trade.amount * currentPrice;
        const costBasis = trade.amount * trade.entry_price;
        
        // Update totals
        totalPnL += livePnL;
        totalValue += currentValue;
        totalCostBasis += costBasis;
        
        if (livePnL > 0) winners++;
        else if (livePnL < 0) losers++;

        return {
          ...trade,
          current_price: currentPrice,
          live_pnl: livePnL,
          live_pnl_pct: livePnLPct,
          current_value: currentValue,
          cost_basis: costBasis,
          price_change: priceChange,
          price_change_pct: (priceChange / trade.entry_price) * 100,
          is_winning: livePnL > 0,
          is_losing: livePnL < 0
        };
      });

    const totalPnLPct = totalCostBasis > 0 ? (totalPnL / totalCostBasis) * 100 : 0;

    return {
      trades: enhancedTrades,
      totalPnL: isNaN(totalPnL) ? 0 : totalPnL,
      totalPnLPct: isNaN(totalPnLPct) ? 0 : totalPnLPct,
      totalValue: isNaN(totalValue) ? 0 : totalValue,
      totalCostBasis: isNaN(totalCostBasis) ? 0 : totalCostBasis,
      winners,
      losers
    };
  }, [trades, wsData.ticker]);

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
            Live Active Trades ({liveTradesData.trades.length})
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
        {liveTradesData.trades.length > 0 && (
          <div className="mt-3 p-3 bg-muted rounded-lg">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className={`text-lg font-bold ${
                  liveTradesData.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {formatCurrency(liveTradesData.totalPnL)}
                </div>
                <div className="text-xs text-muted-foreground">Total P&L</div>
              </div>
              
              <div>
                <div className={`text-lg font-bold ${
                  liveTradesData.totalPnLPct >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {liveTradesData.totalPnLPct >= 0 ? '+' : ''}{formatPercentage(liveTradesData.totalPnLPct)}%
                </div>
                <div className="text-xs text-muted-foreground">Total Return</div>
              </div>
              
              <div>
                <div className="text-lg font-bold">
                  {liveTradesData.winners}/{liveTradesData.losers}
                </div>
                <div className="text-xs text-muted-foreground">W/L Ratio</div>
              </div>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent>
        {liveTradesData.trades.length === 0 ? (
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
            {liveTradesData.trades
              .slice(0, maxTrades)
              .map((trade, index) => (
              <div key={`trade-${trade.id || index}-${index}`} 
                   className={`grid grid-cols-6 gap-2 items-center p-2 rounded-lg transition-colors ${
                     trade.is_winning ? 'bg-green-50 border border-green-200' :
                     trade.is_losing ? 'bg-red-50 border border-red-200' :
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
                    trade.price_change >= 0 ? 'text-green-600' : 'text-red-600'
                  }`}>
                    → {formatCurrency(trade.current_price)}
                  </div>
                </div>
                
                {/* Live P&L */}
                <div className={`text-sm font-medium ${
                  trade.live_pnl >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  <div className="flex items-center gap-1">
                    {trade.live_pnl >= 0 ? 
                      <TrendingUp className="w-3 h-3" /> : 
                      <TrendingDown className="w-3 h-3" />
                    }
                    {formatCurrency(Math.abs(trade.live_pnl))}
                  </div>
                </div>
                
                {/* Return % */}
                <div className={`text-sm font-bold ${
                  trade.live_pnl_pct >= 0 ? 'text-green-600' : 'text-red-600'
                }`}>
                  {trade.live_pnl_pct >= 0 ? '+' : ''}{formatPercentage(trade.live_pnl_pct)}%
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