/**
 * Manual Trade Panel - Live WebSocket-enhanced trading interface
 * 
 * Features:
 * - Live market data via WebSocket för immediate price feedback
 * - Smart price auto-fill from live ticker
 * - Real-time market capacity och risk warnings
 * - Enhanced order validation med live spread checks
 */

import React, { useState, useMemo, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useGlobalWebSocketMarket } from '@/contexts/WebSocketMarketProvider';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
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
  defaultSymbol?: string;
}

export const ManualTradePanel: React.FC<ManualTradePanelProps> = ({ 
  defaultSymbol = 'BTCUSD' 
}) => {
  const [orderType, setOrderType] = useState<OrderType>('market');
  const [side, setSide] = useState<OrderSide>('buy');
  const [amount, setAmount] = useState('');
  const [price, setPrice] = useState('');
  const [currentSymbol] = useState(defaultSymbol);

  const queryClient = useQueryClient();

  // Get global WebSocket data (shared single connection)
  const { 
    connected, 
    getTickerForSymbol, 
    getOrderbookForSymbol,
    subscribeToSymbol,
    platformStatus
  } = useGlobalWebSocketMarket();
  
  // Subscribe to symbol on mount
  useEffect(() => {
    subscribeToSymbol(currentSymbol);
    
    return () => {
      // Note: Don't unsubscribe automatically as other components might use the same symbol
      // unsubscribeFromSymbol(currentSymbol);
    };
  }, [currentSymbol, subscribeToSymbol]);
  
  // Get live market data for this symbol
  const ticker = getTickerForSymbol(currentSymbol);
  const orderbook = getOrderbookForSymbol(currentSymbol);

  // Get balance data for trading capacity
  const { data: balances = [] } = useQuery({
    queryKey: ['balances'],
    queryFn: api.getBalances,
    refetchInterval: 5000
  });

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
      
      // Reset form
      setAmount('');
      setPrice('');
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
      symbol: currentSymbol,
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
            Manual Trading ({currentSymbol})
          </CardTitle>
          
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

        {!tradingCapacity.hasCapacity && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Insufficient balance for {side} order. Please check your account balance.
            </AlertDescription>
          </Alert>
        )}

        {platformStatus === 'maintenance' && (
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Platform is in maintenance mode. Trading may be limited.
            </AlertDescription>
          </Alert>
        )}

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

        {submitOrderMutation.isError && (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Failed to submit order: {submitOrderMutation.error?.message || 'Unknown error'}
            </AlertDescription>
          </Alert>
        )}

        {/* Live Data Status */}
        <div className="text-xs text-muted-foreground text-center pt-2 border-t">
          {connected && ticker ? '🟢 Live market data active' : '🟡 Using REST API data'}
        </div>
      </CardContent>
    </Card>
  );
};
