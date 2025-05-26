
import { Trade } from '@/types/trading';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface TradeTableProps {
  trades: Trade[];
  isLoading?: boolean;
}

export function TradeTable({ trades, isLoading = false }: TradeTableProps) {
  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Active Trades</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse flex justify-between">
                <div className="h-4 bg-muted rounded w-1/4"></div>
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

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Active Trades ({trades.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        {trades.length === 0 ? (
          <p className="text-muted-foreground text-center py-4">No active trades</p>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-5 gap-4 text-xs font-medium text-muted-foreground border-b pb-2">
              <span>Symbol</span>
              <span>Side</span>
              <span>Amount</span>
              <span>Entry Price</span>
              <span>P&L</span>
            </div>
            {trades.map((trade) => (
              <div key={trade.id} className="grid grid-cols-5 gap-4 items-center">
                <span className="font-medium">{trade.symbol}</span>
                <Badge variant={trade.side === 'buy' ? 'default' : 'destructive'} className="w-fit">
                  {trade.side.toUpperCase()}
                </Badge>
                <span>{trade.amount}</span>
                <span>${trade.entry_price.toLocaleString()}</span>
                <span className={trade.pnl >= 0 ? 'text-green-500' : 'text-red-500'}>
                  ${trade.pnl.toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
