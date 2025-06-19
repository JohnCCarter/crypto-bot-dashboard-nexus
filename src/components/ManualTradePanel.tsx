import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api';
import React, { useState } from 'react';

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

  const handleSubmitOrder = async (side: 'buy' | 'sell') => {
    console.log(`📈 [ManualTrade] User initiated ${side.toUpperCase()} order`);
    console.log(`📈 [ManualTrade] Order parameters:`, { symbol, orderType, amount, price, side });
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

    if (orderType === 'limit' && (!price || parseFloat(price) <= 0)) {
      console.error(`❌ [ManualTrade] Validation failed: Invalid price "${price}" for limit order`);
      toast({
        title: 'Invalid Price',
        description: 'Please enter a valid price for limit orders.',
        variant: 'destructive'
      });
      return;
    }

    const orderData: OrderData = {
      symbol,
      order_type: orderType,
      side,
      amount: parseFloat(amount),
      ...(orderType === 'limit' && { price: parseFloat(price) })
    };

    console.log(`📈 [ManualTrade] Order data prepared:`, orderData);
    setIsSubmitting(true);

    try {
      console.log(`📈 [ManualTrade] Calling api.placeOrder()...`);
      
      const result = await api.placeOrder(orderData);
      
      console.log(`✅ [ManualTrade] Order submitted successfully:`, result);
      console.log(`✅ [ManualTrade] Order ID: ${(result as any).order?.id || result.message || 'N/A'}`);
      
      toast({
        title: 'Order Submitted',
        description: `${side.toUpperCase()} order for ${amount} ${symbol} has been placed successfully.`,
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
        <CardTitle className="text-lg font-semibold">Manual Trade</CardTitle>
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

        {/* Price (for limit orders) */}
        {orderType === 'limit' && (
          <div className="space-y-2">
            <Label htmlFor="price">Price</Label>
            <Input
              id="price"
              type="number"
              step="0.01"
              min="0"
              placeholder="Enter price"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
            />
          </div>
        )}

        {/* Buy/Sell Buttons */}
        <div className="grid grid-cols-2 gap-3 pt-2">
          <Button
            onClick={() => handleSubmitOrder('buy')}
            disabled={isSubmitting}
            className="bg-green-600 hover:bg-green-700 text-white"
          >
            {isSubmitting ? 'Submitting...' : 'Buy'}
          </Button>
          <Button
            onClick={() => handleSubmitOrder('sell')}
            disabled={isSubmitting}
            variant="destructive"
          >
            {isSubmitting ? 'Submitting...' : 'Sell'}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
};
