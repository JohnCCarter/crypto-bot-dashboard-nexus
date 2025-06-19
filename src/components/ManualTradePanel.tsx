import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api';
import { useWebSocketMarket } from '@/hooks/useWebSocketMarket';
import React, { useState, useEffect } from 'react';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, Wifi, Activity } from 'lucide-react';

interface ManualTradePanelProps {
  className?: string;
  onOrderPlaced?: () => void;
}

interface OrderData {
  symbol: string;
  order_type: 'market' | 'limit';
  side: 'buy' | 'sell';
  amount: number;
  price?: number;
}

const symbols = ['BTCUSD', 'ETHUSD', 'LTCUSD', 'XRPUSD', 'ADAUSD'];

export const ManualTradePanel: React.FC<ManualTradePanelProps> = ({ className, onOrderPlaced }) => {
  const [symbol, setSymbol] = useState<string>('BTCUSD');
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [amount, setAmount] = useState<string>('');
  const [price, setPrice] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  // 🚀 LIVE WEBSOCKET DATA INTEGRATION
  const wsData = useWebSocketMarket(symbol);
  
  // Auto-update price when switching symbols or when market data updates
  useEffect(() => {
    if (wsData.ticker?.price && orderType === 'limit') {
      // Auto-fill with current market price for limit orders
      setPrice(wsData.ticker.price.toString());
    }
  }, [wsData.ticker?.price, symbol, orderType]);

  // Calculate live spread and market info
  const marketInfo = React.useMemo(() => {
    if (!wsData.orderbook || !wsData.ticker) return null;
    
    const bestBid = wsData.orderbook.bids[0]?.price || 0;
    const bestAsk = wsData.orderbook.asks[0]?.price || 0;
    const spread = bestAsk - bestBid;
    const spreadPct = bestBid > 0 ? (spread / bestBid) * 100 : 0;
    
    return {
      currentPrice: wsData.ticker.price,
      bestBid,
      bestAsk,
      spread,
      spreadPct,
      volume24h: wsData.ticker.volume
    };
  }, [wsData.orderbook, wsData.ticker]);

  // Auto-fill market price for better UX
  const fillMarketPrice = (side: 'buy' | 'sell') => {
    if (!marketInfo) return;
    
    if (side === 'buy' && marketInfo.bestAsk > 0) {
      setPrice(marketInfo.bestAsk.toString());
    } else if (side === 'sell' && marketInfo.bestBid > 0) {
      setPrice(marketInfo.bestBid.toString());
    }
  };

  const handleSubmitOrder = async (side: 'buy' | 'sell') => {
    console.log(`📈 [ManualTrade] User initiated ${side.toUpperCase()} order`);
    console.log(`📈 [ManualTrade] Live market data:`, marketInfo);
    console.log(`📈 [ManualTrade] Order parameters:`, { symbol, orderType, amount, price, side });
    console.log(`📈 [ManualTrade] WebSocket connected:`, wsData.connected);
    console.log(`📈 [ManualTrade] Timestamp: ${new Date().toISOString()}`);
    
    if (!amount || parseFloat(amount) <= 0) {
      console.error(`❌ [ManualTrade] Validation failed: Invalid amount "${amount}"`);
      toast({
        title: 'Invalid Amount',
        description: 'Please enter a valid amount.',
        variant: 'destructive'
      });
      return;
    }

    // Enhanced validation with live market data
    if (orderType === 'limit') {
      if (!price || parseFloat(price) <= 0) {
        console.error(`❌ [ManualTrade] Validation failed: Invalid price "${price}" for limit order`);
        toast({
          title: 'Invalid Price',
          description: 'Please enter a valid price for limit orders.',
          variant: 'destructive'
        });
        return;
      }
      
      // Warn about significant price deviation from market
      if (marketInfo?.currentPrice) {
        const priceNum = parseFloat(price);
        const deviation = Math.abs(priceNum - marketInfo.currentPrice) / marketInfo.currentPrice;
        
        if (deviation > 0.05) { // 5% deviation warning
          const confirmed = window.confirm(
            `Warning: Your limit price (${priceNum}) is ${(deviation * 100).toFixed(1)}% away from current market price (${marketInfo.currentPrice}). Continue?`
          );
          if (!confirmed) return;
        }
      }
    }

    // Use live market price for market orders
    const finalPrice = orderType === 'market' ? 
      (marketInfo && side === 'buy' ? marketInfo.bestAsk : marketInfo?.bestBid) : 
      parseFloat(price);

    const orderData: OrderData = {
      symbol,
      order_type: orderType,
      side,
      amount: parseFloat(amount),
      ...(orderType === 'limit' && { price: parseFloat(price) })
    };

    console.log(`📈 [ManualTrade] Order data prepared (with live pricing):`, orderData);
    console.log(`📈 [ManualTrade] Market context:`, {
      currentPrice: marketInfo?.currentPrice,
      bestBid: marketInfo?.bestBid,
      bestAsk: marketInfo?.bestAsk,
      spread: marketInfo?.spread,
      finalPrice
    });
    
    setIsSubmitting(true);

    try {
      console.log(`📈 [ManualTrade] Calling api.placeOrder() with live market context...`);
      
      const result = await api.placeOrder(orderData);
      
      console.log(`✅ [ManualTrade] Order submitted successfully:`, result);
      console.log(`✅ [ManualTrade] Order ID: ${(result as any).order?.id || result.message || 'N/A'}`);
      
      toast({
        title: 'Order Submitted',
        description: `${side.toUpperCase()} order for ${amount} ${symbol} has been placed successfully at ${orderType === 'market' ? 'market price' : `$${price}`}.`,
      });
      
      // Uppdatera orderhistorik i parent om prop finns
      if (typeof onOrderPlaced === 'function') {
        console.log(`📈 [ManualTrade] Calling onOrderPlaced callback`);
        onOrderPlaced();
      }
      
      // Reset form after successful submission
      console.log(`📈 [ManualTrade] Resetting form fields`);
      setAmount('');
      if (orderType === 'limit') {
        setPrice('');
      }
    } catch (error) {
      console.error(`❌ [ManualTrade] Order submission failed:`, error);
      console.error(`❌ [ManualTrade] Error type: ${error instanceof Error ? error.constructor.name : typeof error}`);
      console.error(`❌ [ManualTrade] Error message: ${error instanceof Error ? error.message : String(error)}`);
      console.error(`❌ [ManualTrade] Stack trace:`, error instanceof Error ? error.stack : 'No stack trace');
      console.error(`❌ [ManualTrade] Failed order data:`, orderData);
      console.error(`❌ [ManualTrade] Market context at failure:`, marketInfo);
      
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      
      toast({
        title: 'Order Failed',
        description: `Failed to submit ${side} order: ${errorMessage}`,
        variant: 'destructive'
      });
    } finally {
      setIsSubmitting(false);
      console.log(`📈 [ManualTrade] Order submission process completed`);
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">Manual Trade</CardTitle>
          {/* Live connection status */}
          <div className="flex items-center gap-2">
            {wsData.connected ? (
              <Badge variant="default" className="bg-green-500">
                <Wifi className="w-3 h-3 mr-1" />
                Live
              </Badge>
            ) : (
              <Badge variant="secondary">
                <Activity className="w-3 h-3 mr-1" />
                Connecting...
              </Badge>
            )}
          </div>
        </div>
        
        {/* Live Market Info Display */}
        {marketInfo && (
          <div className="mt-3 p-3 bg-muted rounded-lg space-y-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium">Current Price:</span>
              <span className="text-sm font-mono">${marketInfo.currentPrice.toFixed(2)}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Best Bid/Ask:</span>
              <span className="text-sm font-mono">
                ${marketInfo.bestBid.toFixed(2)} / ${marketInfo.bestAsk.toFixed(2)}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-muted-foreground">Spread:</span>
              <span className="text-sm font-mono">
                ${marketInfo.spread.toFixed(2)} ({marketInfo.spreadPct.toFixed(3)}%)
              </span>
            </div>
            {wsData.latency && (
              <div className="flex justify-between items-center">
                <span className="text-sm text-muted-foreground">Latency:</span>
                <span className="text-sm font-mono">{wsData.latency}ms</span>
              </div>
            )}
          </div>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Symbol Selection */}
        <div className="space-y-2">
          <Label htmlFor="symbol">Symbol</Label>
          <Select value={symbol} onValueChange={setSymbol}>
            <SelectTrigger>
              <SelectValue placeholder="Select symbol" />
            </SelectTrigger>
            <SelectContent>
              {symbols.map((sym) => (
                <SelectItem key={sym} value={sym}>
                  {sym}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Order Type */}
        <div className="space-y-2">
          <Label htmlFor="orderType">Order Type</Label>
          <Select value={orderType} onValueChange={(value: 'market' | 'limit') => setOrderType(value)}>
            <SelectTrigger>
              <SelectValue placeholder="Select order type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="market">Market</SelectItem>
              <SelectItem value="limit">Limit</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Amount */}
        <div className="space-y-2">
          <Label htmlFor="amount">Amount</Label>
          <Input
            id="amount"
            type="number"
            step="0.001"
            min="0"
            placeholder="0.001"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
          />
        </div>

        {/* Price (for limit orders) with live market helpers */}
        {orderType === 'limit' && (
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="price">Price</Label>
              <div className="flex gap-1">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-6 px-2 text-xs text-green-600"
                  onClick={() => fillMarketPrice('buy')}
                  disabled={!marketInfo}
                >
                  Use Ask
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="h-6 px-2 text-xs text-red-600"
                  onClick={() => fillMarketPrice('sell')}
                  disabled={!marketInfo}
                >
                  Use Bid
                </Button>
              </div>
            </div>
            <Input
              id="price"
              type="number"
              step="0.01"
              min="0"
              placeholder={marketInfo ? `Market: $${marketInfo.currentPrice.toFixed(2)}` : "Enter price"}
              value={price}
              onChange={(e) => setPrice(e.target.value)}
            />
          </div>
        )}

        {/* Enhanced Buy/Sell Buttons with live pricing info */}
        <div className="grid grid-cols-2 gap-3 pt-2">
          <Button
            onClick={() => handleSubmitOrder('buy')}
            disabled={isSubmitting || !wsData.connected}
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            <div className="flex flex-col items-center">
              <span>{isSubmitting ? 'Submitting...' : 'Buy'}</span>
              {marketInfo && orderType === 'market' && (
                <span className="text-xs opacity-75">@ ${marketInfo.bestAsk.toFixed(2)}</span>
              )}
            </div>
          </Button>
          <Button
            onClick={() => handleSubmitOrder('sell')}
            disabled={isSubmitting || !wsData.connected}
            variant="destructive"
          >
            <div className="flex flex-col items-center">
              <span>{isSubmitting ? 'Submitting...' : 'Sell'}</span>
              {marketInfo && orderType === 'market' && (
                <span className="text-xs opacity-75">@ ${marketInfo.bestBid.toFixed(2)}</span>
              )}
            </div>
          </Button>
        </div>
        
        {/* Connection warning */}
        {!wsData.connected && (
          <div className="text-center text-sm text-muted-foreground">
            ⚠️ Waiting for live market data connection...
          </div>
        )}
      </CardContent>
    </Card>
  );
};
