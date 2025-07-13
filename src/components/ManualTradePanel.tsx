/**
 * Manual Trade Panel - Live WebSocket-enhanced trading interface
 * 
 * Features:
 * - Live market data via WebSocket för immediate price feedback
 * - Smart price auto-fill from live ticker
 * - Real-time market capacity och risk warnings
 * - Enhanced order validation med live spread checks
 */

import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useGlobalWebSocketMarket } from '@/contexts/WebSocketMarketProvider';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Activity,
  AlertTriangle,
  CheckCircle,
  Coins,
  DollarSign,
  Layers,
  Target,
  TrendingDown,
  TrendingUp,
  Wifi,
  Zap
} from 'lucide-react';
import React, { useEffect, useMemo, useState } from 'react';

type OrderType = 'market' | 'limit';
type OrderSide = 'buy' | 'sell';
type PositionType = 'margin' | 'spot';

interface ManualTradePanelProps {
  symbol?: string; // Current global symbol (from main page)
  onOrderPlaced?: () => void; // Callback when order is placed
}

// Available trading pairs
const AVAILABLE_SYMBOLS = [
  { value: 'TESTBTC/TESTUSD', label: 'BTC/USD', currency: 'TESTBTC' },
  { value: 'TESTETH/TESTUSD', label: 'ETH/USD', currency: 'TESTETH' },
  { value: 'TESTLTC/TESTUSD', label: 'LTC/USD', currency: 'TESTLTC' },
];

export const ManualTradePanel: React.FC<ManualTradePanelProps> = ({ 
  symbol,
  onOrderPlaced
}) => {
  const [orderType, setOrderType] = useState<OrderType>('market');
  const [side, setSide] = useState<OrderSide>('buy');
  const [positionType, setPositionType] = useState<PositionType>('spot');
  const [amount, setAmount] = useState('');
  const [price, setPrice] = useState('');
  const [currentSymbol, setCurrentSymbol] = useState(
    AVAILABLE_SYMBOLS.find(s => s.value.includes(symbol?.replace('USD', '')))?.value || 'TESTBTC/TESTUSD'
  );

  const { toast } = useToast();

  // Get global WebSocket data (shared single connection)
  const { 
    connected, 
    getTickerForSymbol, 
    getOrderbookForSymbol,
    subscribeToSymbol,
    platformStatus
  } = useGlobalWebSocketMarket();
  
  const queryClient = useQueryClient();
  
  // Subscribe to symbol on mount
  useEffect(() => {
    console.log(`📈 [ManualTrade] Component mounted - subscribing to ${currentSymbol}`);
    console.log(`📈 [ManualTrade] WebSocket connected: ${connected}`);
    subscribeToSymbol(currentSymbol);
    
    return () => {
      console.log(`📈 [ManualTrade] Component unmounting from ${currentSymbol}`);
      // Note: Don't unsubscribe automatically as other components might use the same symbol
      // unsubscribeFromSymbol(currentSymbol);
    };
  }, [currentSymbol, subscribeToSymbol, connected]);
  
  // Get live market data for this symbol
  const ticker = getTickerForSymbol(currentSymbol);
  const orderbook = getOrderbookForSymbol(currentSymbol);

  // Get balance data for trading capacity
  const { data: balances = [] } = useQuery({
    queryKey: ['balances'],
    queryFn: api.getBalances,
    refetchInterval: 5000
  });

  // Trading capacity calculation (dynamic based on selected symbol and position type)
  const tradingCapacity = useMemo(() => {
    const symbolInfo = AVAILABLE_SYMBOLS.find(s => s.value === currentSymbol);
    const baseCurrency = symbolInfo?.currency || 'TESTBTC';
    
    // Ensure balances is an array and add null safety
    const balancesArray = Array.isArray(balances) ? balances : [];
    const usdBalance = balancesArray.find(b => b.currency === 'TESTUSD')?.available || 0;
    const cryptoBalance = balancesArray.find(b => b.currency === baseCurrency)?.available || 0;
    
    // For margin trading, we could potentially have higher leverage
    // For now, treating both the same but marking for future enhancement
    const leverageMultiplier = positionType === 'margin' ? 1 : 1; // Future: could be 2-10x for margin
    
    const maxBuyUSD = usdBalance * leverageMultiplier;
    const maxSellCrypto = cryptoBalance;
    const currentPrice = ticker?.price || 0;
    
    return {
      baseCurrency,
      positionType,
      leverageMultiplier,
      maxBuyUSD,
      maxSellCrypto,
      maxBuyCrypto: currentPrice > 0 ? maxBuyUSD / currentPrice : 0,
      maxSellUSD: maxSellCrypto * currentPrice,
      hasCapacity: side === 'buy' ? maxBuyUSD > 0 : maxSellCrypto > 0,
      marginNote: positionType === 'margin' ? 'Margin trading (1:1 leverage)' : 'Spot trading'
    };
  }, [balances, ticker, side, currentSymbol, positionType]);

  // Order submission mutation
  const submitOrderMutation = useMutation({
    mutationFn: (orderData: {
      symbol: string;
      type: OrderType;
      side: OrderSide;
      amount: number;
      price?: number;
      positionType?: PositionType;
    }) => api.placeOrder({
      symbol: orderData.symbol,
      order_type: orderData.type,
      side: orderData.side,
      amount: orderData.amount,
      ...(orderData.price && { price: orderData.price }),
      // Note: Backend may not support position_type yet, but we include it for future enhancement
      ...(orderData.positionType && { position_type: orderData.positionType })
    }),
    onSuccess: (data, variables) => {
      console.log(`✅ [ManualTrade] Order submitted successfully!`);
      console.log(`✅ [ManualTrade] API Response:`, data);
      console.log(`✅ [ManualTrade] Order was: ${variables.side} ${variables.amount} ${variables.symbol} @ ${variables.type}`);
      console.log(`✅ [ManualTrade] Refreshing portfolio data...`);
      
      toast({
        title: 'Order Submitted',
        description: `${variables.side.toUpperCase()} order for ${variables.amount} ${variables.symbol} submitted successfully.`
      });
      
      queryClient.invalidateQueries({ queryKey: ['balances'] });
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['positions'] });
      queryClient.invalidateQueries({ queryKey: ['active-positions'] });
      
      // Reset form
      setAmount('');
      setPrice('');
      
      console.log(`✅ [ManualTrade] Form reset completed`);
      
      // Call callback if provided
      onOrderPlaced?.();
    },
    onError: (error, variables) => {
      console.error(`❌ [ManualTrade] Order submission failed!`);
      console.error(`❌ [ManualTrade] Error:`, error);
      console.error(`❌ [ManualTrade] Failed order was: ${variables.side} ${variables.amount} ${variables.symbol} @ ${variables.type}`);
      console.error(`❌ [ManualTrade] Error type: ${error instanceof Error ? error.constructor.name : typeof error}`);
      console.error(`❌ [ManualTrade] Error message: ${error instanceof Error ? error.message : String(error)}`);
      console.error(`❌ [ManualTrade] Timestamp: ${new Date().toISOString()}`);
      
      toast({
        title: 'Order Failed',
        description: `Failed to submit ${variables.side} order. Please try again.`,
        variant: 'destructive'
      });
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

  // Auto-fill functions
  const fillMarketPrice = () => {
    console.log(`📈 [ManualTrade] User clicked 'Fill Market Price' button`);
    
    if (!ticker) {
      console.warn(`⚠️ [ManualTrade] Cannot fill price - no ticker data available`);
      return;
    }
    
    if (orderType === 'limit') {
      // Use best bid/ask for better execution probability
      const targetPrice = side === 'buy' ? marketInfo.bestBid : marketInfo.bestAsk;
      const formattedPrice = targetPrice.toFixed(2);
      
      console.log(`📈 [ManualTrade] Auto-filling price: ${formattedPrice} (${side === 'buy' ? 'best bid' : 'best ask'})`);
      setPrice(formattedPrice);
    } else {
      console.log(`📈 [ManualTrade] Price auto-fill not applicable for market orders`);
    }
  };

  const fillMaxAmount = () => {
    console.log(`📈 [ManualTrade] User clicked 'Max Amount' button`);
    console.log(`📈 [ManualTrade] Trading capacity: ${side === 'buy' ? tradingCapacity.maxBuyCrypto : tradingCapacity.maxSellCrypto} ${tradingCapacity.baseCurrency}`);
    
    if (side === 'buy') {
      const maxCrypto = tradingCapacity.maxBuyCrypto;
      const formattedAmount = maxCrypto.toFixed(6);
      console.log(`📈 [ManualTrade] Auto-filling max buy amount: ${formattedAmount} ${tradingCapacity.baseCurrency}`);
      setAmount(formattedAmount);
    } else {
      const formattedAmount = tradingCapacity.maxSellCrypto.toFixed(6);
      console.log(`📈 [ManualTrade] Auto-filling max sell amount: ${formattedAmount} ${tradingCapacity.baseCurrency}`);
      setAmount(formattedAmount);
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
    console.log(`📈 [ManualTrade] User initiated ${side.toUpperCase()} order for ${currentSymbol}`);
    console.log(`📈 [ManualTrade] Order details: ${orderType} ${side} ${amount} ${currentSymbol.split('/')[0]} @ ${orderType === 'limit' ? price : 'market price'}`);
    console.log(`📈 [ManualTrade] Position type: ${positionType}`);
    console.log(`📈 [ManualTrade] Timestamp: ${new Date().toISOString()}`);
    
    if (!canSubmit) {
      console.warn(`⚠️ [ManualTrade] Order blocked - validation failed`);
      console.warn(`⚠️ [ManualTrade] Current validation state: canSubmit=${canSubmit}`);
      return;
    }

    const orderData = {
      symbol: currentSymbol,
      type: orderType,
      side,
      amount: parseFloat(amount),
      positionType,
      ...(orderType === 'limit' && { price: parseFloat(price) })
    };

    console.log(`📈 [ManualTrade] Order validation passed - submitting to API`);
    console.log(`📈 [ManualTrade] Final order data:`, orderData);

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

        {/* Trading Pair Selection */}
        <div className="space-y-2">
          <Label htmlFor="symbol">Trading Pair</Label>
          <Select value={currentSymbol} onValueChange={(value: string) => {
            setCurrentSymbol(value);
            setAmount(''); // Reset amount when changing pairs
            setPrice(''); // Reset price when changing pairs
          }}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {AVAILABLE_SYMBOLS.map((symbolOption) => (
                <SelectItem key={symbolOption.value} value={symbolOption.value}>
                  <div className="flex items-center gap-2">
                    <Target className="w-4 h-4" />
                    {symbolOption.label}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Position Type Selection */}
        <div className="space-y-2">
          <Label htmlFor="positionType">Position Type</Label>
          <Select value={positionType} onValueChange={(value: PositionType) => setPositionType(value)}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="spot">
                <div className="flex items-center gap-2">
                  <Coins className="w-4 h-4 text-blue-600" />
                  <div>
                    <div>Spot Trading</div>
                    <div className="text-xs text-muted-foreground">Own the asset directly</div>
                  </div>
                </div>
              </SelectItem>
              <SelectItem value="margin">
                <div className="flex items-center gap-2">
                  <Layers className="w-4 h-4 text-orange-600" />
                  <div>
                    <div className="flex items-center gap-2">
                      Margin Trading
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Leveraged position (Future: 2-10x)
                    </div>
                  </div>
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

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
            <Label htmlFor="amount">Amount ({tradingCapacity.baseCurrency.replace('TEST', '')})</Label>
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
          <div className="text-xs space-y-1">
            <div className="text-muted-foreground">
              Available: {side === 'buy' 
                ? `${formatCurrency(tradingCapacity.maxBuyUSD)} (≈${formatCrypto(tradingCapacity.maxBuyCrypto)} ${tradingCapacity.baseCurrency.replace('TEST', '')})`
                : `${formatCrypto(tradingCapacity.maxSellCrypto)} ${tradingCapacity.baseCurrency.replace('TEST', '')} (≈${formatCurrency(tradingCapacity.maxSellUSD)})`
              }
            </div>
            <div className={`flex items-center gap-1 ${
              positionType === 'margin' ? 'text-orange-600' : 'text-blue-600'
            }`}>
              {positionType === 'margin' ? <Layers className="w-3 h-3" /> : <Coins className="w-3 h-3" />}
              {tradingCapacity.marginNote}
            </div>
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
              {positionType === 'margin' ? <Layers className="w-4 h-4" /> : <Coins className="w-4 h-4" />}
              {side === 'buy' ? 'Buy' : 'Sell'} {amount && `${amount} ${tradingCapacity.baseCurrency.replace('TEST', '')}`}
              <Badge variant={positionType === 'margin' ? 'default' : 'outline'} className="text-xs">
                {positionType.toUpperCase()}
              </Badge>
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
