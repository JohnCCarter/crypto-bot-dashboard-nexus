
import { OrderBook as OrderBookType } from '@/types/trading';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface OrderBookProps {
  orderBook: OrderBookType;
  isLoading?: boolean;
}

export function OrderBook({ orderBook, isLoading = false }: OrderBookProps) {
  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Order Book</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse flex justify-between">
                <div className="h-4 bg-muted rounded w-1/3"></div>
                <div className="h-4 bg-muted rounded w-1/3"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Order Book - {orderBook.symbol}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {/* Asks (Sell Orders) */}
          <div>
            <h4 className="text-xs font-medium text-red-500 mb-2">ASKS (SELL)</h4>
            <div className="space-y-1">
              {orderBook.asks.slice(0, 5).reverse().map((ask, index) => (
                <div key={index} className="flex justify-between text-sm">
                  <span className="text-red-500">${ask.price.toLocaleString()}</span>
                  <span className="text-muted-foreground">{ask.amount.toFixed(4)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Spread */}
          <div className="border-t border-b py-2 text-center">
            <span className="text-xs text-muted-foreground">
              Spread: ${(orderBook.asks[0].price - orderBook.bids[0].price).toFixed(2)}
            </span>
          </div>

          {/* Bids (Buy Orders) */}
          <div>
            <h4 className="text-xs font-medium text-green-500 mb-2">BIDS (BUY)</h4>
            <div className="space-y-1">
              {orderBook.bids.slice(0, 5).map((bid, index) => (
                <div key={index} className="flex justify-between text-sm">
                  <span className="text-green-500">${bid.price.toLocaleString()}</span>
                  <span className="text-muted-foreground">{bid.amount.toFixed(4)}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
