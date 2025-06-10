import { useEffect, useRef } from 'react';
import { OHLCVData, EmaCrossoverSignal } from '@/types/trading';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

interface PriceChartProps {
  data: OHLCVData[];
  symbol: string;
  isLoading?: boolean;
  emaFast?: number[];
  emaSlow?: number[];
  signals?: EmaCrossoverSignal[];
}

export function PriceChart({ data, symbol, isLoading = false, emaFast, emaSlow, signals }: PriceChartProps) {
  const chartData = data.map((item, i) => ({
    time: new Date(item.timestamp).toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    }),
    price: item.close,
    volume: item.volume,
    emaFast: emaFast ? emaFast[i] : undefined,
    emaSlow: emaSlow ? emaSlow[i] : undefined,
    signal: signals?.find(s => s.index === i)?.type || null
  }));

  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Price Chart - {symbol}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="h-[300px] flex items-center justify-center">
            <div className="animate-pulse text-muted-foreground">Loading chart data...</div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm font-medium flex items-center justify-between">
          <span>Price Chart - {symbol}</span>
          <span className="text-lg font-bold">
            ${data[data.length - 1]?.close.toLocaleString() || 'N/A'}
          </span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
              <XAxis 
                dataKey="time" 
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                interval="preserveStartEnd"
              />
              <YAxis 
                stroke="hsl(var(--muted-foreground))"
                fontSize={12}
                domain={['dataMin - 100', 'dataMax + 100']}
              />
              <Tooltip 
                contentStyle={{
                  backgroundColor: 'hsl(var(--card))',
                  border: '1px solid hsl(var(--border))',
                  borderRadius: '6px'
                }}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
              />
              <Line 
                type="monotone" 
                dataKey="price" 
                stroke="#3b82f6" 
                strokeWidth={2}
                dot={false}
                activeDot={{ r: 4, stroke: '#3b82f6', strokeWidth: 2 }}
              />
              {emaFast && (
                <Line
                  type="monotone"
                  dataKey="emaFast"
                  stroke="#f59e42"
                  strokeWidth={1.5}
                  dot={false}
                  name="EMA Fast"
                />
              )}
              {emaSlow && (
                <Line
                  type="monotone"
                  dataKey="emaSlow"
                  stroke="#10b981"
                  strokeWidth={1.5}
                  dot={false}
                  name="EMA Slow"
                />
              )}
              {signals && signals.length > 0 && (
                <Line
                  dataKey="signal"
                  stroke="none"
                  dot={({ cx, cy, payload }) => {
                    if (payload.signal === 'buy') {
                      return <circle cx={cx} cy={cy} r={6} fill="#22c55e" stroke="#fff" strokeWidth={2} />;
                    }
                    if (payload.signal === 'sell') {
                      return <circle cx={cx} cy={cy} r={6} fill="#ef4444" stroke="#fff" strokeWidth={2} />;
                    }
                    return null;
                  }}
                  legendType="none"
                />
              )}
            </LineChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  );
}
