/**
 * Manual Trade Panel - Optimerad version utan excessive polling
 * 
 * Features:
 * - Centraliserad data via useOptimizedMarketData
 * - Eliminerade redundanta API-anrop
 * - Smart price auto-fill from live ticker
 * - Real-time market capacity och risk warnings
 * - Enhanced order validation med live spread checks
 */

import React, { useState, useMemo, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useOptimizedMarketData } from '@/hooks/useOptimizedMarketData';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  AlertTriangle, 
  CheckCircle, 
  Wifi,
  Activity,
  Zap,
  Target
} from 'lucide-react';

type OrderType = 'market' | 'limit';
type OrderSide = 'buy' | 'sell';

interface ManualTradePanelProps {
  symbol: string; // Make symbol required to prevent hardcoding
  onOrderPlaced?: () => void;
}

export const ManualTradePanel: React.FC<ManualTradePanelProps> = ({ 
  symbol,
  onOrderPlaced
}) => {
  const [orderType, setOrderType] = useState<OrderType>('market');
  const [side, setSide] = useState<OrderSide>('buy');
  const [amount, setAmount] = useState('');
  const [price, setPrice] = useState('');
  
  // Anti-spam protection for insufficient balance logging
  const lastInsufficientBalanceLog = useRef<Record<string, number>>({});

  const queryClient = useQueryClient();

  // Use centralized optimized data
  const { 
    balances,
    ticker,
    orderbook,
    connected,
    error,
    refreshData
  } = useOptimizedMarketData(symbol);

  // Order submission mutation
  const submitOrderMutation = useMutation({
    mutationFn: (orderData: {
      symbol: string;
      type: OrderType;
      side: OrderSide;
      amount: number;
      price?: number;
    }) => api.placeOrder({
      symbol: orderData.symbol,
      order_type: orderData.type,
      side: orderData.side,
      amount: orderData.amount,
      ...(orderData.price && { price: orderData.price })
    }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['balances'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      
      // Refresh centralized data
      refreshData(true);
      
      // Reset form
      setAmount('');
      setPrice('');
      
      // Notify parent component
      onOrderPlaced?.();
    }
  });

  // Calculate live market info
  const marketInfo = useMemo(() => {
    if (!ticker || !orderbook) {
      return {
        currentPrice: 0,
        bestBid: 0,
        bestAsk: 0,
        spread: 0,
        spreadPct: 0,
        priceDeviation: 0,
        liquidityWarning: false
      };
    }

    const currentPrice = ticker.price;
    const bestBid = orderbook.bids[0]?.price || 0;
    const bestAsk = orderbook.asks[0]?.price || 0;
    const spread = bestAsk - bestBid;
    const spreadPct = currentPrice > 0 ? (spread / currentPrice) * 100 : 0;
    
    // Calculate price deviation if limit order
    const limitPrice = parseFloat(price) || 0;
    const priceDeviation = limitPrice > 0 && currentPrice > 0 
      ? ((limitPrice - currentPrice) / currentPrice) * 100 
      : 0;

    // Liquidity warning för stora orders
    const orderAmount = parseFloat(amount) || 0;
    const relevantSide = side === 'buy' ? orderbook.asks : orderbook.bids;
    const top5Liquidity = relevantSide.slice(0, 5).reduce((sum, level) => sum + level.amount, 0);
    const liquidityWarning = orderAmount > top5Liquidity * 0.1; // Warning if order > 10% of top 5 levels

    return {
      currentPrice,
      bestBid,
      bestAsk,
      spread,
      spreadPct,
      priceDeviation,
      liquidityWarning
    };
  }, [ticker, orderbook, price, amount, side]);

  // Trading capacity calculation
  const tradingCapacity = useMemo(() => {
    const usdBalance = balances.find(b => b.currency === 'USD')?.available || 0;
    const btcBalance = balances.find(b => b.currency === 'BTC')?.available || 0;
    
    const maxBuyUSD = usdBalance;
    const maxSellBTC = btcBalance;
    const currentPrice = ticker?.price || 0;
    
    return {
      maxBuyUSD,
      maxSellBTC,
      maxBuyBTC: currentPrice > 0 ? maxBuyUSD / currentPrice : 0,
      maxSellUSD: maxSellBTC * currentPrice,
      hasCapacity: side === 'buy' ? maxBuyUSD > 0 : maxSellBTC > 0
    };
  }, [balances, ticker, side]);

  // Auto-fill functions
  const fillMarketPrice = () => {
    if (!ticker) return;
    
    if (orderType === 'limit') {
      // Use best bid/ask for better execution probability
      const targetPrice = side === 'buy' ? marketInfo.bestBid : marketInfo.bestAsk;
      setPrice(targetPrice.toFixed(2));
    }
  };

  const fillMaxAmount = () => {
    if (side === 'buy') {
      const maxBTC = tradingCapacity.maxBuyBTC;
      setAmount(maxBTC.toFixed(6));
    } else {
      setAmount(tradingCapacity.maxSellBTC.toFixed(6));
    }
  };

  // Validation
  const canSubmit = useMemo(() => {
    const amountNum = parseFloat(amount);
    const priceNum = parseFloat(price);
    
    if (!amountNum || amountNum <= 0) return false;
    if (orderType === 'limit' && (!priceNum || priceNum <= 0)) return false;
    if (!tradingCapacity.hasCapacity) return false;
    
    return true;
  }, [amount, price, orderType, tradingCapacity.hasCapacity]);

  const handleSubmit = () => {
    if (!canSubmit) return;

    const orderData = {
      symbol: symbol,
      type: orderType,
      side,
      amount: parseFloat(amount),
      ...(orderType === 'limit' && { price: parseFloat(price) })
    };

    submitOrderMutation.mutate(orderData);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatCrypto = (value: number, decimals = 6) => {
    return value.toFixed(decimals);
  };

  return (
    <Card className="bg-card border-border">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-sm font-medium">
            <DollarSign className="w-4 h-4" />
            Manual Trading ({symbol})
          </CardTitle>
          
          <div className="flex items-center gap-2">
            {connected ? (
              <Badge variant="default" className="bg-green-500">
                <Wifi className="w-3 h-3 mr-1" />
                Connected
              </Badge>
            ) : (
              <Badge variant="secondary">
                <Activity className="w-3 h-3 mr-1" />
                Offline
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Live Market Info */}
        {ticker && (
          <div className="p-3 bg-muted rounded-lg">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-muted-foreground">Live Market Price</span>
              <Badge variant="outline" className="text-xs">
                <Zap className="w-3 h-3 mr-1" />
                Real-time
              </Badge>
            </div>
            
            <div className="text-xl font-bold">
              {formatCurrency(marketInfo.currentPrice)}
            </div>
            
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>Bid: {formatCurrency(marketInfo.bestBid)}</span>
              <span>Ask: {formatCurrency(marketInfo.bestAsk)}</span>
            </div>
            
            <div className="text-xs text-muted-foreground text-center mt-1">
              Spread: {formatCurrency(marketInfo.spread)} ({marketInfo.spreadPct.toFixed(3)}%)
            </div>
          </div>
        )}

        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Data error: {error}
            </AlertDescription>
          </Alert>
        )}

        {/* Order Configuration */}
        <div className="grid grid-cols-2 gap-4">
          {/* Order Type */}
          <div className="space-y-2">
            <Label htmlFor="orderType">Order Type</Label>
            <Select value={orderType} onValueChange={(value: OrderType) => setOrderType(value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="market">Market Order</SelectItem>
                <SelectItem value="limit">Limit Order</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Side */}
          <div className="space-y-2">
            <Label htmlFor="side">Side</Label>
            <Select value={side} onValueChange={(value: OrderSide) => setSide(value)}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="buy">
                  <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-green-600" />
                    Buy
                  </div>
                </SelectItem>
                <SelectItem value="sell">
                  <div className="flex items-center gap-2">
                    <TrendingDown className="w-4 h-4 text-red-600" />
                    Sell
                  </div>
                </SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Amount Input */}
        <div className="space-y-2">
          <div className="flex justify-between items-center">
            <Label htmlFor="amount">Amount (BTC)</Label>
            <Button 
              variant="outline" 
              size="sm" 
              onClick={fillMaxAmount}
              disabled={!tradingCapacity.hasCapacity}
            >
              <Target className="w-3 h-3 mr-1" />
              Max
            </Button>
          </div>
          <Input
            id="amount"
            type="number"
            step="0.000001"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.001000"
          />
          
          {/* Trading Capacity Info */}
          <div className="text-xs text-muted-foreground">
            Available: {side === 'buy' 
              ? `${formatCurrency(tradingCapacity.maxBuyUSD)} (≈${formatCrypto(tradingCapacity.maxBuyBTC)} BTC)`
              : `${formatCrypto(tradingCapacity.maxSellBTC)} BTC (≈${formatCurrency(tradingCapacity.maxSellUSD)})`
            }
          </div>
        </div>

        {/* Price Input (Limit Orders Only) */}
        {orderType === 'limit' && (
          <div className="space-y-2">
            <div className="flex justify-between items-center">
              <Label htmlFor="price">Price (USD)</Label>
              <Button 
                variant="outline" 
                size="sm" 
                onClick={fillMarketPrice}
                disabled={!ticker}
              >
                <Zap className="w-3 h-3 mr-1" />
                Market
              </Button>
            </div>
            <Input
              id="price"
              type="number"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="0.00"
            />
            
            {/* Price Deviation Warning */}
            {marketInfo.priceDeviation !== 0 && (
              <div className={`text-xs ${
                Math.abs(marketInfo.priceDeviation) > 2 ? 'text-orange-600' : 'text-muted-foreground'
              }`}>
                {marketInfo.priceDeviation > 0 ? '▲' : '▼'} {Math.abs(marketInfo.priceDeviation).toFixed(2)}% from market price
              </div>
            )}
          </div>
        )}

        {/* Warnings and Alerts */}
        {marketInfo.liquidityWarning && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Large order detected. This may impact market price significantly.
            </AlertDescription>
          </Alert>
        )}

        {!tradingCapacity.hasCapacity && (() => {
          // Anti-spam protection: Only log if amount > 0 and not logged recently
          const currentTime = Date.now();
          const logKey = `${side}-${symbol}-${tradingCapacity.maxBuyUSD.toFixed(2)}`;
          const lastLogTime = lastInsufficientBalanceLog.current[logKey] || 0;
          const timeSinceLastLog = currentTime - lastLogTime;
          
          // Only log if: 1) amount > 0, 2) not logged same scenario in last 10 seconds
          if (parseFloat(amount || '0') > 0 && timeSinceLastLog > 10000) {
            console.warn(`⚠️ [ManualTradePanel] INSUFFICIENT BALANCE WARNING: User attempted ${side} order for ${amount} ${symbol} but lacks sufficient balance. Available: ${side === 'buy' ? `$${tradingCapacity.maxBuyUSD.toFixed(2)} USD` : `${tradingCapacity.maxSellBTC.toFixed(6)} BTC`}`);
            
            // Track this log to prevent spam
            lastInsufficientBalanceLog.current[logKey] = currentTime;
          }
          
          return (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Insufficient balance for {side} order. Please check your account balance.
              </AlertDescription>
            </Alert>
          );
        })()}

        {/* Submit Button */}
        <Button
          onClick={handleSubmit}
          disabled={!canSubmit || submitOrderMutation.isPending}
          className={`w-full ${
            side === 'buy' 
              ? 'bg-green-600 hover:bg-green-700' 
              : 'bg-red-600 hover:bg-red-700'
          }`}
        >
          {submitOrderMutation.isPending ? (
            'Submitting...'
          ) : (
            <div className="flex items-center gap-2">
              {side === 'buy' ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
              {side === 'buy' ? 'Buy' : 'Sell'} {amount && `${amount} BTC`}
              {orderType === 'market' && ticker && amount && 
                ` ≈ ${formatCurrency(parseFloat(amount) * marketInfo.currentPrice)}`
              }
            </div>
          )}
        </Button>

        {/* Success/Error Messages */}
        {submitOrderMutation.isSuccess && (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              Order submitted successfully!
            </AlertDescription>
          </Alert>
        )}

        {submitOrderMutation.isError && (() => {
          const errorMessage = submitOrderMutation.error?.message || 'Unknown error';
          
          // Anti-spam protection for order submission errors
          const currentTime = Date.now();
          const errorLogKey = `error-${side}-${symbol}-${errorMessage.substring(0, 20)}`;
          const lastErrorLogTime = lastInsufficientBalanceLog.current[errorLogKey] || 0;
          const timeSinceLastErrorLog = currentTime - lastErrorLogTime;
          
          // Only log if not logged same error in last 5 seconds (shorter for errors)
          if (timeSinceLastErrorLog > 5000) {
            if (errorMessage.toLowerCase().includes('insufficient balance') || 
                errorMessage.toLowerCase().includes('insufficient position') ||
                errorMessage.toLowerCase().includes('balance')) {
              console.error(`🚨 [ManualTradePanel] ORDER REJECTED - INSUFFICIENT BALANCE: ${side} ${amount} ${symbol} failed. Server error: "${errorMessage}". User balances should be checked.`);
            } else {
              console.error(`❌ [ManualTradePanel] ORDER SUBMISSION FAILED: ${side} ${amount} ${symbol}. Error: "${errorMessage}"`);
            }
            
            // Track this error log to prevent spam
            lastInsufficientBalanceLog.current[errorLogKey] = currentTime;
          }
          
          return (
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                Failed to submit order: {errorMessage}
              </AlertDescription>
            </Alert>
          );
        })()}

        {/* Live Data Status */}
        <div className="text-xs text-muted-foreground text-center pt-2 border-t">
          {connected && ticker ? '🟢 Optimized live data' : '🟡 Offline mode'}
        </div>
      </CardContent>
    </Card>
  );
};
