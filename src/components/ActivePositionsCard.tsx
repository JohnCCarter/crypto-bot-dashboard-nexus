/**
 * Active Positions Card - Dedikerad komponent för aktiva positioner
 * 
 * Features:
 * - Live positions från /api/positions endpoint
 * - Tydlig separation mellan MARGIN och SPOT positioner
 * - Real-time P&L calculation med WebSocket priser
 * - Klar visuell hierarki och UX
 */

import React, { useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useGlobalWebSocketMarket } from '@/contexts/WebSocketMarketProvider';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { 
  TrendingUp, 
  TrendingDown, 
  RefreshCw, 
  DollarSign, 
  Target,
  Layers,
  Coins,
  Activity,
  AlertTriangle
} from 'lucide-react';

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
    if (symbol) {
      subscribeToSymbol(symbol);
    } else {
      // Subscribe to common symbols for portfolio-wide pricing
      ['BTCUSD', 'ETHUSD', 'LTCUSD'].forEach(s => subscribeToSymbol(s));
    }
  }, [symbol, subscribeToSymbol]);
  
  // Fetch active positions from correct API endpoint
  const { data: positions = [], isLoading, error, refetch } = useQuery<Position[]>({
    queryKey: ['active-positions'],
    queryFn: async () => {
      const res = await fetch('/api/positions');
      if (!res.ok) throw new Error('Failed to fetch positions');
      return await res.json();
    },
    refetchInterval: connected ? 10000 : 5000, // More frequent updates
    staleTime: 2000
  });

  // Process positions med live pricing
  const processedPositions = useMemo(() => {
    if (!positions || positions.length === 0) {
      return {
        marginPositions: [],
        spotPositions: [],
        totalMarginPnL: 0,
        totalSpotValue: 0,
        totalPositions: 0
      };
    }

    let filteredPositions = positions;
    
    // Filter by symbol if specified
    if (showOnlySymbol && symbol) {
      const symbolFilter = symbol.replace('USD', '/USD');
      filteredPositions = positions.filter(pos => pos.symbol === symbolFilter);
    }

    // Limit number of positions
    if (maxPositions) {
      filteredPositions = filteredPositions.slice(0, maxPositions);
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

    return {
      marginPositions,
      spotPositions,
      totalMarginPnL,
      totalSpotValue,
      totalPositions
    };
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
          
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {processedPositions.totalPositions} total
            </Badge>
            
            {connected ? (
              <Badge variant="default" className="bg-green-500 text-white">
                <Activity className="w-3 h-3 mr-1" />
                Live P&L
              </Badge>
            ) : (
              <Badge variant="secondary">Static P&L</Badge>
            )}
            
            <Button variant="outline" size="sm" onClick={() => refetch()}>
              <RefreshCw className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Portfolio Summary */}
        {processedPositions.totalPositions > 0 && (
          <div className="grid grid-cols-2 gap-4 p-3 bg-muted rounded-lg">
            <div className="text-center">
              <div className="text-xs text-muted-foreground">Margin P&L</div>
              <div className={`font-bold text-sm ${
                processedPositions.totalMarginPnL >= 0 ? 'text-green-600' : 'text-red-600'
              }`}>
                {formatPrice(processedPositions.totalMarginPnL)}
              </div>
              <div className="text-xs text-muted-foreground">
                {processedPositions.marginPositions.length} positions
              </div>
            </div>
            
            <div className="text-center">
              <div className="text-xs text-muted-foreground">Spot Value</div>
              <div className="font-bold text-sm">
                {formatPrice(processedPositions.totalSpotValue)}
              </div>
              <div className="text-xs text-muted-foreground">
                {processedPositions.spotPositions.length} holdings
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
                  (position.livePnL || 0) > 0 ? 'bg-green-50 border-green-200' :
                  (position.livePnL || 0) < 0 ? 'bg-red-50 border-red-200' :
                  'bg-muted border-border'
                }`}
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={position.side === 'buy' ? 'default' : 'destructive'} className="text-xs">
                      {position.side.toUpperCase()}
                    </Badge>
                    <span className="font-semibold text-sm">{position.symbol}</span>
                    <Badge variant="outline" className="text-xs">MARGIN</Badge>
                  </div>
                  
                  <div className="text-right">
                    <div className={`font-bold text-sm ${
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
                className="p-3 rounded-lg bg-blue-50 border border-blue-200 transition-colors"
              >
                <div className="flex justify-between items-start mb-2">
                  <div className="flex items-center gap-2">
                    <Badge variant={position.side === 'buy' ? 'default' : 'destructive'} className="text-xs">
                      {position.side.toUpperCase()}
                    </Badge>
                    <span className="font-semibold text-sm">{position.symbol}</span>
                    <Badge variant="outline" className="text-xs bg-blue-500 text-white border-blue-500">SPOT</Badge>
                  </div>
                  
                  <div className="text-right">
                    <div className="font-bold text-sm">
                      {formatPrice((position.currentPrice || position.mark_price) * position.amount)}
                    </div>
                    <div className="text-xs text-blue-600">Market Value</div>
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