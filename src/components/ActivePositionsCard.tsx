/**
 * Active Positions Card - Dedikerad komponent för aktiva positioner
 * 
 * Features:
 * - Live positions från /api/positions endpoint
 * - Tydlig separation mellan MARGIN och SPOT positioner
 * - Real-time P&L calculation med WebSocket priser
 * - Klar visuell hierarki och UX
 */

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useGlobalWebSocketMarket } from '@/contexts/WebSocketMarketProvider';
import { useQuery } from '@tanstack/react-query';
import {
    Activity,
    AlertTriangle,
    Coins,
    Layers,
    RefreshCw,
    Target
} from 'lucide-react';
import React, { useEffect, useMemo } from 'react';

interface Position {
  id: string;
  symbol: string;
  side: 'buy' | 'sell';
  amount: number;
  entry_price: number;
  mark_price: number;
  pnl: number;
  pnl_percentage: number;
  position_type: 'margin' | 'spot_holding';
  margin_mode?: string;
  collateral?: number;
  timestamp: number;
}

interface ActivePositionsCardProps {
  symbol?: string;
  showOnlySymbol?: boolean;
  maxPositions?: number;
}

export const ActivePositionsCard: React.FC<ActivePositionsCardProps> = ({ 
  symbol,
  showOnlySymbol = false,
  maxPositions = 10
}) => {
  // Get global WebSocket data for live pricing
  const { 
    connected, 
    getTickerForSymbol,
    subscribeToSymbol
  } = useGlobalWebSocketMarket();
  
  // Subscribe to symbols for live pricing
  useEffect(() => {
    console.log(`🎯 [Positions] Component mounted`);
    console.log(`🎯 [Positions] Symbol filter: ${symbol || 'all'}`);
    console.log(`🎯 [Positions] Show only symbol: ${showOnlySymbol}`);
    console.log(`🎯 [Positions] Max positions: ${maxPositions}`);
    console.log(`🎯 [Positions] WebSocket connected: ${connected}`);
    
    if (symbol) {
      console.log(`🎯 [Positions] Subscribing to specific symbol: ${symbol}`);
      subscribeToSymbol(symbol);
    } else {
      console.log(`🎯 [Positions] Subscribing to common symbols for portfolio-wide pricing`);
      ['BTCUSD', 'ETHUSD', 'LTCUSD'].forEach(s => {
        console.log(`🎯 [Positions] Subscribing to ${s}`);
        subscribeToSymbol(s);
      });
    }
    
    return () => {
      console.log(`🎯 [Positions] Component unmounting`);
    };
  }, [symbol, subscribeToSymbol, showOnlySymbol, maxPositions, connected]);
  
  // Fetch active positions from correct API endpoint
  const { data: positions = [], isLoading, error, refetch } = useQuery<Position[]>({
    queryKey: ['active-positions'],
    queryFn: async () => {
      console.log(`🎯 [Positions] Fetching positions from API...`);
      try {
        const res = await fetch('/api/positions');
        if (!res.ok) {
          console.error(`❌ [Positions] API request failed: ${res.status} ${res.statusText}`);
          throw new Error('Failed to fetch positions');
        }
        const data = await res.json();
        console.log(`✅ [Positions] Received ${data.length} positions from API`);
        console.log(`🎯 [Positions] Position data:`, data);
        return data;
      } catch (error) {
        console.error(`❌ [Positions] Failed to fetch positions:`, error);
        throw error;
      }
    },
    refetchInterval: connected ? 5000 : 10000, // Faster when connected
    staleTime: 1000, // Shorter stale time for faster updates
    refetchOnMount: true, // Always fetch on mount
    refetchOnWindowFocus: true, // Fetch when window gets focus
    retry: 1, // Only retry once to avoid delays
    onError: (error) => {
      console.error(`❌ [Positions] Query error:`, error);
      console.error(`❌ [Positions] Error type: ${error instanceof Error ? error.constructor.name : typeof error}`);
    }
  });

  // Process positions med live pricing
  const processedPositions = useMemo(() => {
    console.log(`🎯 [Positions] Processing ${positions.length} positions...`);
    
    if (!positions || positions.length === 0) {
      console.log(`🎯 [Positions] No positions to process`);
      return {
        marginPositions: [],
        spotPositions: [],
        totalMarginPnL: 0,
        totalSpotValue: 0,
        totalPositions: 0
      };
    }

    let filteredPositions = positions;
    console.log(`🎯 [Positions] Starting with ${filteredPositions.length} positions`);
    
    // Filter by symbol if specified
    if (showOnlySymbol && symbol) {
      const symbolFilter = symbol.replace('USD', '/USD');
      console.log(`🎯 [Positions] Filtering by symbol: ${symbolFilter}`);
      filteredPositions = positions.filter(pos => pos.symbol === symbolFilter);
      console.log(`🎯 [Positions] After symbol filter: ${filteredPositions.length} positions`);
    }

    // Limit number of positions
    if (maxPositions) {
      console.log(`🎯 [Positions] Limiting to max ${maxPositions} positions`);
      filteredPositions = filteredPositions.slice(0, maxPositions);
      console.log(`🎯 [Positions] After limit: ${filteredPositions.length} positions`);
    }

    // Separate margin and spot positions med live pricing
    const marginPositions: (Position & { currentPrice?: number; livePnL?: number })[] = [];
    const spotPositions: (Position & { currentPrice?: number; livePnL?: number })[] = [];
    
    filteredPositions.forEach(position => {
      // Get live price from WebSocket
      const wsSymbol = position.symbol.replace('/', '');
      const ticker = getTickerForSymbol(wsSymbol);
      const currentPrice = ticker?.price || position.mark_price;
      
      // Calculate live P&L
      const direction = position.side === 'buy' ? 1 : -1;
      const livePnL = (currentPrice - position.entry_price) * direction * position.amount;
      
      const enhancedPosition = {
        ...position,
        currentPrice,
        livePnL: ticker ? livePnL : position.pnl // Use live or fallback to static
      };
      
      if (position.position_type === 'margin') {
        marginPositions.push(enhancedPosition);
      } else {
        spotPositions.push(enhancedPosition);
      }
    });

    // Calculate totals
    const totalMarginPnL = marginPositions.reduce((sum, pos) => sum + (pos.livePnL || 0), 0);
    const totalSpotValue = spotPositions.reduce((sum, pos) => sum + (pos.amount * (pos.currentPrice || pos.mark_price)), 0);
    const totalPositions = marginPositions.length + spotPositions.length;

    const result = {
      marginPositions,
      spotPositions,
      totalMarginPnL,
      totalSpotValue,
      totalPositions
    };
    
    console.log(`✅ [Positions] Processing complete:`);
    console.log(`🎯 [Positions] Total positions: ${totalPositions}`);
    console.log(`🎯 [Positions] Margin positions: ${marginPositions.length} (PnL: $${totalMarginPnL.toFixed(2)})`);
    console.log(`🎯 [Positions] Spot holdings: ${spotPositions.length} (Value: $${totalSpotValue.toFixed(2)})`);
    console.log(`🎯 [Positions] WebSocket pricing active: ${connected}`);

    return result;
  }, [positions, symbol, showOnlySymbol, maxPositions, getTickerForSymbol, connected]);

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  const formatAmount = (amount: number, decimals = 6) => {
    return amount.toFixed(decimals);
  };

  const formatPercentage = (percentage: number) => {
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`;
  };

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Target className="w-4 h-4" />
            Active Positions {symbol && `(${symbol})`}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse flex justify-between p-3 bg-muted rounded">
                <div className="h-4 bg-muted-foreground/20 rounded w-1/3"></div>
                <div className="h-4 bg-muted-foreground/20 rounded w-1/4"></div>
                <div className="h-4 bg-muted-foreground/20 rounded w-1/4"></div>
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
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-red-500" />
            Positions Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-4">
            <p className="text-red-500 mb-2">Failed to load positions</p>
            <Button variant="outline" size="sm" onClick={() => refetch()}>
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
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <Target className="w-4 h-4" />
            Active Positions {symbol && `(${symbol})`}
          </CardTitle>
          
          <div className="flex items-center gap-1 flex-wrap">
            <Badge variant="outline" className="text-xs px-1.5 py-0.5">
              {processedPositions.totalPositions}
            </Badge>
            
            {connected ? (
              <Badge variant="default" className="bg-green-600 text-xs px-1.5 py-0.5">
                <Activity className="w-3 h-3" />
              </Badge>
            ) : (
              <Badge variant="secondary" className="text-xs px-1.5 py-0.5">
                Static
              </Badge>
            )}
            
            <Button variant="outline" size="sm" onClick={() => refetch()} className="px-2 py-1">
              <RefreshCw className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Portfolio Summary */}
        {processedPositions.totalPositions > 0 && (
          <div className="grid grid-cols-2 gap-2 p-2 bg-muted rounded-lg text-center">
            <div className="min-w-0">
              <div className="text-xs text-muted-foreground truncate">Margin P&L</div>
              <div className={`font-bold text-sm truncate ${
                processedPositions.totalMarginPnL >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatPrice(processedPositions.totalMarginPnL)}
              </div>
              <div className="text-xs text-muted-foreground">
                {processedPositions.marginPositions.length} pos
              </div>
            </div>
            
            <div className="min-w-0">
              <div className="text-xs text-muted-foreground truncate">Spot Value</div>
              <div className="font-bold text-sm truncate">
                {formatPrice(processedPositions.totalSpotValue)}
              </div>
              <div className="text-xs text-muted-foreground">
                {processedPositions.spotPositions.length} hold
              </div>
            </div>
          </div>
        )}

        {/* Margin Positions Section */}
        {processedPositions.marginPositions.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-orange-600">
              <Layers className="w-4 h-4" />
              Margin Positions ({processedPositions.marginPositions.length})
            </div>
            
            {processedPositions.marginPositions.map((position) => (
              <div 
                key={position.id}
                className={`p-3 rounded-lg border transition-colors ${
                  (position.livePnL || 0) > 0 ? 'bg-green-500/10 border-green-500/20' :
                  (position.livePnL || 0) < 0 ? 'bg-red-500/10 border-red-500/20' :
                  'bg-muted border-border'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-1 min-w-0 flex-1">
                    <Badge variant={position.side === 'buy' ? 'default' : 'destructive'} className="text-xs px-1">
                      {position.side === 'buy' ? 'L' : 'S'}
                    </Badge>
                    <span className="font-semibold text-sm truncate">{position.symbol}</span>
                    <Badge variant="outline" className="text-xs px-1">M</Badge>
                  </div>
                  
                  <div className="text-right min-w-0 flex-shrink-0">
                    <div className={`font-bold text-sm truncate ${
                      (position.livePnL || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {(position.livePnL || 0) >= 0 ? '+' : ''}{formatPrice(position.livePnL || 0)}
                    </div>
                    <div className={`text-xs ${
                      (position.pnl_percentage || 0) >= 0 ? 'text-green-600' : 'text-red-600'
                    }`}>
                      {formatPercentage(position.pnl_percentage || 0)}
                    </div>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4 text-xs">
                  <div>
                    <div className="text-muted-foreground">Amount</div>
                    <div className="font-mono">{formatAmount(position.amount, 6)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Entry</div>
                    <div className="font-mono">{formatPrice(position.entry_price)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Current</div>
                    <div className="font-mono">
                      {position.currentPrice ? formatPrice(position.currentPrice) : 'N/A'}
                      {connected && position.currentPrice && (
                        <span className="ml-1 text-green-500">●</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Spot Holdings Section */}
        {processedPositions.spotPositions.length > 0 && (
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-sm font-semibold text-blue-600">
              <Coins className="w-4 h-4" />
              Spot Holdings ({processedPositions.spotPositions.length})
            </div>
            
            {processedPositions.spotPositions.map((position) => (
              <div 
                key={position.id}
                className="p-3 rounded-lg bg-blue-500/10 border border-blue-500/20 transition-colors"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-1 min-w-0 flex-1">
                    <Badge variant={position.side === 'buy' ? 'default' : 'destructive'} className="text-xs px-1">
                      {position.side === 'buy' ? 'B' : 'S'}
                    </Badge>
                    <span className="font-semibold text-sm truncate">{position.symbol}</span>
                    <Badge variant="outline" className="text-xs px-1">S</Badge>
                  </div>
                  
                  <div className="text-right min-w-0 flex-shrink-0">
                    <div className="font-bold text-sm truncate">
                      {formatPrice((position.currentPrice || position.mark_price) * position.amount)}
                    </div>
                    <div className="text-xs text-blue-600">Value</div>
                  </div>
                </div>
                
                <div className="grid grid-cols-3 gap-4 text-xs">
                  <div>
                    <div className="text-muted-foreground">Amount</div>
                    <div className="font-mono">{formatAmount(position.amount, 6)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Avg Price</div>
                    <div className="font-mono">{formatPrice(position.entry_price)}</div>
                  </div>
                  <div>
                    <div className="text-muted-foreground">Current</div>
                    <div className="font-mono">
                      {position.currentPrice ? formatPrice(position.currentPrice) : formatPrice(position.mark_price)}
                      {connected && position.currentPrice && (
                        <span className="ml-1 text-green-500">●</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Empty State */}
        {processedPositions.totalPositions === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <Target className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p className="font-medium">No Active Positions</p>
            <p className="text-xs">Your positions will appear here when you open trades</p>
            {symbol && (
              <p className="text-xs mt-1">Showing only {symbol} positions</p>
            )}
          </div>
        )}

        {/* Status Footer */}
        <div className="flex justify-between items-center text-xs text-muted-foreground pt-2 border-t">
          <span>
            {processedPositions.marginPositions.length} margin + {processedPositions.spotPositions.length} spot
          </span>
          <span>
            {connected ? '🟢 Live pricing' : '🟡 Static pricing'}
          </span>
        </div>
      </CardContent>
    </Card>
  );
};