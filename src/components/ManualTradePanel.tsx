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
import { logger } from '@/utils/logger';

interface ManualTradePanelProps {
  className?: string;
  onOrderPlaced?: () => void;
  symbol?: string;
}

interface OrderData {
  symbol: string;
  order_type: 'market' | 'limit';
  side: 'buy' | 'sell';
  amount: number;
  price?: number;
}

export const ManualTradePanel: React.FC<ManualTradePanelProps> = ({ className, onOrderPlaced, symbol }) => {
  const currentSymbol = symbol || 'BTCUSD';
  const [orderType, setOrderType] = useState<'market' | 'limit'>('market');
  const [amount, setAmount] = useState<string>('');
  const [price, setPrice] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { toast } = useToast();

  // 🚀 LIVE WEBSOCKET DATA INTEGRATION
  const wsData = useWebSocketMarket(currentSymbol);
  
  // Auto-update price when switching symbols or when market data updates
  useEffect(() => {
    if (wsData.ticker?.price && orderType === 'limit') {
      // Auto-fill with current market price for limit orders
      setPrice(wsData.ticker.price.toString());
    }
  }, [wsData.ticker?.price, currentSymbol, orderType]);

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
    if (!amount || parseFloat(amount) <= 0) {
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
      symbol: currentSymbol,
      order_type: orderType,
      side,
      amount: parseFloat(amount),
      ...(orderType === 'limit' && { price: parseFloat(price) })
    };
    
    setIsSubmitting(true);

    try {
      const result = await api.placeOrder(orderData);
      
      // Log successful trade using trading logger
      if (side === 'buy') {
        logger.buyApproved(currentSymbol, parseFloat(amount), orderType === 'limit' ? parseFloat(price) : undefined);
      } else {
        logger.sellApproved(currentSymbol, parseFloat(amount), orderType === 'limit' ? parseFloat(price) : undefined);
      }
      
      toast({
        title: 'Order Submitted',
        description: `${side.toUpperCase()} order for ${amount} ${currentSymbol} has been placed successfully at ${orderType === 'market' ? 'market price' : `$${price}`}.`,
      });
      
      // Uppdatera orderhistorik i parent om prop finns
      if (typeof onOrderPlaced === 'function') {
        onOrderPlaced();
      }
      
      // Reset form after successful submission
      setAmount('');
      if (orderType === 'limit') {
        setPrice('');
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      
      // Log trade error using trading logger
      logger.tradeError(side, currentSymbol, errorMessage);
      
      toast({
        title: 'Order Failed',
        description: `Failed to submit ${side} order: ${errorMessage}`,
        variant: 'destructive'
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-semibold">Manual Trade - {currentSymbol}</CardTitle>
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
