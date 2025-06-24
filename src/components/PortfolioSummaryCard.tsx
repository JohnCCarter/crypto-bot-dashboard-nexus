/**
 * Portfolio Summary Card - Översikt av hela portfolion
 * 
 * Features:
 * - Asset allocation visualization
 * - Portfolio diversifiering metrics
 * - Risk/reward översikt
 * - Performance summary
 */

import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { 
  PieChart, 
  RefreshCw, 
  TrendingUp, 
  TrendingDown,
  Shield,
  Target,
  BarChart3,
  AlertTriangle,
  DollarSign
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

interface Balance {
  available: number;
  currency: string;
  total_balance: number;
}

export const PortfolioSummaryCard: React.FC = () => {
  // Fetch positions and balances
  const { data: positions = [], isLoading: positionsLoading, refetch: refetchPositions } = useQuery<Position[]>({
    queryKey: ['portfolio-positions'],
    queryFn: async () => {
      const res = await fetch('/api/positions');
      if (!res.ok) throw new Error('Failed to fetch positions');
      return await res.json();
    },
    refetchInterval: 10000,
  });

  const { data: balances = [], isLoading: balancesLoading, refetch: refetchBalances } = useQuery<Balance[]>({
    queryKey: ['portfolio-balances'],
    queryFn: api.getBalances,
    refetchInterval: 10000,
  });

  const isLoading = positionsLoading || balancesLoading;

  // Calculate portfolio metrics
  const portfolioMetrics = useMemo(() => {
    if (!positions.length && !balances.length) {
      return {
        totalValue: 0,
        totalPnL: 0,
        totalPnLPct: 0,
        assetAllocation: [],
        riskMetrics: {
          marginPositions: 0,
          spotHoldings: 0,
          diversificationScore: 0,
          riskLevel: 'LOW' as 'LOW' | 'MEDIUM' | 'HIGH'
        }
      };
    }

    // Calculate asset allocation from positions and balances
    const allocation: { asset: string; value: number; percentage: number; type: 'margin' | 'spot' | 'cash' }[] = [];
    let totalValue = 0;
    let totalPnL = 0;

    // Add positions
    positions.forEach(position => {
      const value = position.amount * position.mark_price;
      totalValue += value;
      totalPnL += position.pnl;
      
      const asset = position.symbol.split('/')[0]; // BTC från BTC/USD
      const existingAsset = allocation.find(a => a.asset === asset);
      
      if (existingAsset) {
        existingAsset.value += value;
      } else {
        allocation.push({
          asset,
          value,
          percentage: 0, // Beräknas senare
          type: position.position_type === 'margin' ? 'margin' : 'spot'
        });
      }
    });

    // Add cash balances
    balances.forEach(balance => {
      const isFiat = balance.currency.includes('USD') || balance.currency.includes('EUR');
      if (isFiat && balance.total_balance > 0) {
        totalValue += balance.total_balance;
        allocation.push({
          asset: balance.currency.replace('TEST', ''),
          value: balance.total_balance,
          percentage: 0,
          type: 'cash'
        });
      }
    });

    // Calculate percentages
    allocation.forEach(asset => {
      asset.percentage = totalValue > 0 ? (asset.value / totalValue) * 100 : 0;
    });

    // Sort by value
    allocation.sort((a, b) => b.value - a.value);

    // Calculate risk metrics
    const marginPositions = positions.filter(p => p.position_type === 'margin').length;
    const spotHoldings = positions.filter(p => p.position_type === 'spot_holding').length;
    const uniqueAssets = new Set(allocation.map(a => a.asset)).size;
    
    // Diversification score (0-100)
    const diversificationScore = Math.min(100, uniqueAssets * 20); // Max 5 assets for 100%
    
    // Risk level based on margin exposure
    let riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' = 'LOW';
    const marginValue = allocation.filter(a => a.type === 'margin').reduce((sum, a) => sum + a.value, 0);
    const marginPercentage = totalValue > 0 ? (marginValue / totalValue) * 100 : 0;
    
    if (marginPercentage > 50) riskLevel = 'HIGH';
    else if (marginPercentage > 20) riskLevel = 'MEDIUM';

    const totalPnLPct = totalValue > 0 ? (totalPnL / (totalValue - totalPnL)) * 100 : 0;

    return {
      totalValue,
      totalPnL,
      totalPnLPct,
      assetAllocation: allocation,
      riskMetrics: {
        marginPositions,
        spotHoldings,
        diversificationScore,
        riskLevel
      }
    };
  }, [positions, balances]);

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const formatPercentage = (percentage: number) => {
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(1)}%`;
  };

  const handleRefresh = () => {
    refetchPositions();
    refetchBalances();
  };

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium flex items-center gap-2">
            <PieChart className="w-4 h-4" />
            Portfolio Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="animate-pulse flex justify-between p-3 bg-muted rounded">
                <div className="h-4 bg-muted-foreground/20 rounded w-1/3"></div>
                <div className="h-4 bg-muted-foreground/20 rounded w-1/4"></div>
              </div>
            ))}
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
            <PieChart className="w-4 h-4" />
            Portfolio Summary
          </CardTitle>
          
          <div className="flex items-center gap-2">
            <Badge 
              variant={portfolioMetrics.riskMetrics.riskLevel === 'LOW' ? 'default' : 
                      portfolioMetrics.riskMetrics.riskLevel === 'MEDIUM' ? 'secondary' : 'destructive'}
              className="text-xs"
            >
              <Shield className="w-3 h-3 mr-1" />
              {portfolioMetrics.riskMetrics.riskLevel} RISK
            </Badge>
            
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="w-3 h-3" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Portfolio Value & Performance */}
        <div className="grid grid-cols-2 gap-4 p-3 bg-muted rounded-lg">
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Total Value</div>
            <div className="font-bold text-sm">
              {formatCurrency(portfolioMetrics.totalValue)}
            </div>
          </div>
          
          <div className="text-center">
            <div className="text-xs text-muted-foreground">Total P&L</div>
            <div className={`font-bold text-sm flex items-center justify-center gap-1 ${
              portfolioMetrics.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {portfolioMetrics.totalPnL >= 0 ? 
                <TrendingUp className="w-3 h-3" /> : 
                <TrendingDown className="w-3 h-3" />
              }
              {formatCurrency(Math.abs(portfolioMetrics.totalPnL))}
            </div>
            <div className={`text-xs ${
              portfolioMetrics.totalPnL >= 0 ? 'text-green-600' : 'text-red-600'
            }`}>
              {formatPercentage(portfolioMetrics.totalPnLPct)}
            </div>
          </div>
        </div>

        {/* Asset Allocation */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <BarChart3 className="w-4 h-4" />
            Asset Allocation
          </div>
          
          {portfolioMetrics.assetAllocation.length > 0 ? (
            <div className="space-y-2">
              {portfolioMetrics.assetAllocation.slice(0, 5).map((asset, index) => (
                <div key={asset.asset} className="flex justify-between items-center p-2 rounded bg-muted/50">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${
                      asset.type === 'margin' ? 'bg-orange-500' :
                      asset.type === 'spot' ? 'bg-blue-500' : 'bg-green-500'
                    }`}></div>
                    <span className="font-medium text-sm">{asset.asset}</span>
                    <Badge variant="outline" className="text-xs">
                      {asset.type.toUpperCase()}
                    </Badge>
                  </div>
                  
                  <div className="text-right">
                    <div className="font-bold text-sm">
                      {asset.percentage.toFixed(1)}%
                    </div>
                    <div className="text-xs text-muted-foreground">
                      {formatCurrency(asset.value)}
                    </div>
                  </div>
                </div>
              ))}
              
              {portfolioMetrics.assetAllocation.length > 5 && (
                <div className="text-center text-xs text-muted-foreground">
                  +{portfolioMetrics.assetAllocation.length - 5} more assets
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-4 text-muted-foreground">
              <Target className="w-6 h-6 mx-auto mb-1 opacity-50" />
              <p className="text-sm">No assets to display</p>
            </div>
          )}
        </div>

        {/* Risk & Diversification Metrics */}
        <div className="space-y-2">
          <div className="flex items-center gap-2 text-sm font-semibold">
            <Shield className="w-4 h-4" />
            Risk & Diversification
          </div>
          
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div className="p-2 bg-muted/50 rounded">
              <div className="text-muted-foreground">Positions</div>
              <div className="font-semibold">
                {portfolioMetrics.riskMetrics.marginPositions} margin + {portfolioMetrics.riskMetrics.spotHoldings} spot
              </div>
            </div>
            
            <div className="p-2 bg-muted/50 rounded">
              <div className="text-muted-foreground">Diversification</div>
              <div className="font-semibold">
                {portfolioMetrics.riskMetrics.diversificationScore}/100
              </div>
            </div>
          </div>
        </div>

        {/* Status Footer */}
        <div className="flex justify-between items-center text-xs text-muted-foreground pt-2 border-t">
          <span>
            {portfolioMetrics.assetAllocation.length} different assets
          </span>
          <span>
            Last updated: {new Date().toLocaleTimeString()}
          </span>
        </div>
      </CardContent>
    </Card>
  );
};