/**
 * Hybrid Trade Table - Optimerad version utan excessive polling
 * 
 * Features:
 * - Centraliserad data via useOptimizedMarketData
 * - Eliminerade redundanta API-anrop
 * - Position P&L visualization med buy/sell indicators
 * - Volume analysis och position tracking
 */

import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useOptimizedMarketData } from '@/hooks/useOptimizedMarketData';
import { TrendingUp, TrendingDown, Volume2, RefreshCw, Wifi, Activity } from 'lucide-react';

interface HybridTradeTableProps {
  symbol: string; // Make symbol required to prevent hardcoding
  maxTrades?: number;
  showVolume?: boolean;
}

export const HybridTradeTable: React.FC<HybridTradeTableProps> = ({ 
  symbol,
  maxTrades = 20,
  showVolume = true 
}) => {
  // Use centralized optimized data
  const { 
    activeTrades,
    ticker,
    connected,
    error,
    refreshData
  } = useOptimizedMarketData(symbol);

  // Process trades for display with live P&L
  const processedTrades = useMemo(() => {
    if (!activeTrades || activeTrades.length === 0) {
      return {
        recentTrades: [],
        totalVolume: 0,
        totalPnL: 0,
        avgPrice: 0,
        activePositions: 0
      };
    }

    const currentPrice = ticker?.price || 0;
    
    // Limit and sort trades by timestamp (newest first)
    const recentTrades = [...activeTrades]
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())
      .slice(0, maxTrades)
      .map(trade => {
        // Calculate live P&L using current market price
        const livePrice = currentPrice > 0 ? currentPrice : (trade.entry_price || 0);
        const direction = (trade.side === 'buy') ? 1 : -1;
        const livePnL = (livePrice - (trade.entry_price || 0)) * direction * (trade.amount || 0);
        
        return {
          ...trade,
          currentPrice: livePrice,
          livePnL
        };
      });

    // Calculate aggregated statistics
    const totalVolume = recentTrades.reduce((sum, trade) => sum + (trade.amount || 0), 0);
    const totalPnL = recentTrades.reduce((sum, trade) => sum + (trade.livePnL || 0), 0);
    const avgPrice = recentTrades.length > 0 
      ? recentTrades.reduce((sum, trade) => sum + (trade.entry_price || 0), 0) / recentTrades.length 
      : 0;
    
    const activePositions = recentTrades.length;

    return {
      recentTrades,
      totalVolume,
      totalPnL,
      avgPrice,
      activePositions
    };
  }, [activeTrades, maxTrades, ticker]);

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

  const formatTime = (timestamp: string) => {
    if (!timestamp) return 'N/A';
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch {
      return 'Invalid';
    }
  };

  if (!activeTrades && !error) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Active Positions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex justify-between">
                <div className="h-4 bg-muted rounded w-1/4"></div>
                <div className="h-4 bg-muted rounded w-1/4"></div>
                <div className="h-4 bg-muted rounded w-1/4"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error && (!activeTrades || activeTrades.length === 0)) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Active Positions</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4">
            <p className="text-red-500">Failed to load position data: {error}</p>
            <Button variant="outline" size="sm" onClick={() => refreshData(true)} className="mt-2">
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
          <CardTitle className="text-sm font-medium">Active Positions ({symbol})</CardTitle>
          
          <div className="flex items-center gap-2">
            {connected ? (
              <Badge variant="default" className="bg-green-500">
                <Wifi className="w-3 h-3 mr-1" />
                Live P&L
              </Badge>
            ) : (
              <Badge variant="secondary">
                <Activity className="w-3 h-3 mr-1" />
                Static P&L
              </Badge>
            )}
            
            <Button variant="outline" size="sm" onClick={() => refreshData(true)}>
              <RefreshCw className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Position Statistics */}
        {showVolume && processedTrades.activePositions > 0 && (
          <div className="grid grid-cols-3 gap-4 p-3 bg-muted rounded-lg">
            <div className="text-center">
              <div className="text-sm text-muted-foreground">Total P&L</div>
              <div className={`font-bold ${
                processedTrades.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatPrice(processedTrades.totalPnL)}
              </div>
              <div className={`text-xs flex items-center justify-center gap-1 ${
                processedTrades.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {processedTrades.totalPnL >= 0 ? 
                  <TrendingUp className="w-3 h-3" /> : 
                  <TrendingDown className="w-3 h-3" />
                }
                {ticker ? 'Live' : 'Static'}
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-sm text-muted-foreground">Volume</div>
              <div className="font-bold">{formatAmount(processedTrades.totalVolume)} BTC</div>
              <div className="text-xs text-muted-foreground">
                {processedTrades.activePositions} positions
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-sm text-muted-foreground">Avg Entry</div>
              <div className="font-bold">{formatPrice(processedTrades.avgPrice)}</div>
              <div className="text-xs text-muted-foreground">
                Current: {ticker ? formatPrice(ticker.price) : 'N/A'}
              </div>
            </div>
          </div>
        )}

        {/* Position List */}
        <div className="space-y-1 max-h-96 overflow-y-auto">
          {/* Header */}
          <div className="grid grid-cols-4 gap-4 text-xs font-semibold text-muted-foreground py-2 border-b">
            <span>Time</span>
            <span>Side</span>
            <span className="text-right">Entry Price</span>
            <span className="text-right">P&L</span>
          </div>
          
          {/* Position Rows */}
          {processedTrades.recentTrades.length > 0 ? (
            processedTrades.recentTrades.map((trade, index) => (
              <div 
                key={`${trade.id || 'unknown'}-${trade.timestamp || index}`}
                className={`grid grid-cols-4 gap-4 text-xs py-2 px-2 rounded transition-colors ${
                  (trade.livePnL || 0) > 0 ? 'bg-green-50 hover:bg-green-100' :
                  (trade.livePnL || 0) < 0 ? 'bg-red-50 hover:bg-red-100' :
                  'hover:bg-muted'
                }`}
              >
                <span className="text-muted-foreground">
                  {formatTime(trade.timestamp)}
                </span>
                
                <Badge 
                  variant={(trade.side === 'buy') ? 'default' : 'destructive'} 
                  className="w-fit text-xs"
                >
                  {trade.side?.toUpperCase() || 'UNKNOWN'}
                </Badge>
                
                <span className="text-right font-mono">
                  {formatPrice(trade.entry_price || 0)}
                </span>
                
                <span className={`text-right font-mono ${
                  (trade.livePnL || 0) > 0 ? 'text-green-600' :
                  (trade.livePnL || 0) < 0 ? 'text-red-600' :
                  'text-muted-foreground'
                }`}>
                  {(trade.livePnL || 0) >= 0 ? '+' : ''}{formatPrice(trade.livePnL || 0)}
                  {(trade.livePnL || 0) !== 0 && (
                    <span className="ml-1">
                      {(trade.livePnL || 0) > 0 ? '↗' : '↘'}
                    </span>
                  )}
                </span>
              </div>
            ))
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              <Volume2 className="w-8 h-8 mx-auto mb-2" />
              <p>No active positions</p>
              <p className="text-xs">Open positions will appear here with live P&L</p>
            </div>
          )}
        </div>

        {/* Data Source Status */}
        <div className="flex justify-between items-center text-xs text-muted-foreground pt-2 border-t">
          <span>
            Showing {processedTrades.recentTrades.length} active positions
          </span>
          <span>
            {connected && ticker ? '🟢 Optimized live updates' : '🟡 Offline mode'}
          </span>
        </div>
      </CardContent>
    </Card>
  );
};