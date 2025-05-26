
import { Balance } from '@/types/trading';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';

interface BalanceCardProps {
  balances: Balance[];
  isLoading?: boolean;
}

export function BalanceCard({ balances, isLoading = false }: BalanceCardProps) {
  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Account Balance</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-muted rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-muted rounded w-1/2"></div>
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
        <CardTitle className="text-sm font-medium">Account Balance</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {balances.map((balance) => (
            <div key={balance.currency} className="flex justify-between items-center">
              <div>
                <p className="font-semibold text-foreground">{balance.currency}</p>
                <p className="text-xs text-muted-foreground">
                  Available: {balance.available.toLocaleString()}
                </p>
              </div>
              <div className="text-right">
                <p className="font-bold text-lg">
                  {balance.total_balance.toLocaleString()}
                </p>
                <p className="text-xs text-muted-foreground">
                  {((balance.available / balance.total_balance) * 100).toFixed(1)}% available
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
