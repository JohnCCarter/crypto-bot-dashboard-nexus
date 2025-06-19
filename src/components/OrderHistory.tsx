import { OrderHistoryItem } from '@/types/trading';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface OrderHistoryProps {
  orders: OrderHistoryItem[];
  isLoading?: boolean;
  onOrderCancelled?: () => void;
}

export function OrderHistory({ orders, isLoading = false, onOrderCancelled }: OrderHistoryProps) {
  const { toast } = useToast();

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Order History</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex justify-between">
                <div className="h-4 bg-muted rounded w-1/5"></div>
                <div className="h-4 bg-muted rounded w-1/6"></div>
                <div className="h-4 bg-muted rounded w-1/6"></div>
                <div className="h-4 bg-muted rounded w-1/6"></div>
                <div className="h-4 bg-muted rounded w-1/6"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'filled': return 'bg-green-500';
      case 'cancelled': return 'bg-red-500';
      case 'pending': return 'bg-yellow-500';
      default: return 'bg-gray-500';
    }
  };

  const handleCancelOrder = async (orderId: string) => {
    try {
      await api.cancelOrder(orderId);
      toast({
        title: 'Order Cancelled',
        description: `Order ${orderId} cancelled successfully.`
      });
      if (typeof onOrderCancelled === 'function') {
        onOrderCancelled();
      }
    } catch (error) {
      toast({
        title: 'Cancellation Failed',
        description: 'Failed to cancel order. Please try again.',
        variant: 'destructive'
      });
    }
  };

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Order History ({orders.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[300px]">
          {orders.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">No order history</p>
          ) : (
            <div className="space-y-4">
              <div className="grid grid-cols-7 gap-2 text-xs font-medium text-muted-foreground border-b pb-2">
                <span>Symbol</span>
                <span>Type</span>
                <span>Side</span>
                <span>Amount</span>
                <span>Price</span>
                <span>Fee</span>
                <span>Status</span>
              </div>
              {orders.map((order) => (
                <div key={order.id} className="grid grid-cols-7 gap-2 items-center text-sm">
                  <span className="font-medium">{order.symbol}</span>
                  <span className="capitalize">{order.order_type}</span>
                  <Badge variant={order.side === 'buy' ? 'default' : 'destructive'} className="w-fit text-xs">
                    {order.side.toUpperCase()}
                  </Badge>
                  <span>{order.amount}</span>
                  <span>${order.price.toLocaleString()}</span>
                  <span>${order.fee.toFixed(2)}</span>
                  <div className="flex items-center gap-2">
                    <Badge className={`w-fit text-xs ${getStatusColor(order.status)}`}>{order.status}</Badge>
                    {order.status === 'pending' && (
                      <Button
                        variant="destructive"
                        size="sm"
                        className="ml-2"
                        onClick={() => handleCancelOrder(order.id)}
                      >
                        Avbryt
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
