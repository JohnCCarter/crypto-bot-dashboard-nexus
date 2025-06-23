/**
 * Hybrid Price Chart - Optimerad version utan excessive polling
 * 
 * Funktioner:
 * - Centraliserad data via useOptimizedMarketData  
 * - Reducerade API-anrop
 * - Live price updates på senaste candlestick
 */

import React, { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { useOptimizedMarketData } from '@/hooks/useOptimizedMarketData';
import { RefreshCw, Wifi, Activity } from 'lucide-react';

interface HybridPriceChartProps {
  symbol?: string;
  height?: number;
  showControls?: boolean;
}

export const HybridPriceChart: React.FC<HybridPriceChartProps> = ({ 
  symbol = 'BTCUSD', 
  height = 400,
  showControls = true 
}) => {
  const { 
    ticker, 
    chartData, 
    connected, 
    error,
    refreshData
  } = useOptimizedMarketData(symbol);

  // Format chart data för Recharts
  const formattedChartData = useMemo(() => {
    return chartData.map((candle, index) => ({
      index,
      timestamp: new Date(candle.timestamp).toLocaleTimeString(),
      price: candle.close,
      high: candle.high,
      low: candle.low,
      volume: candle.volume,
      // Highlighta senaste punkt 
      isLive: index === chartData.length - 1
    }));
  }, [chartData]);

  // Connection status styling - simplified
  const getConnectionBadge = () => {
    if (connected) {
      return (
        <Badge variant="default" className="bg-green-500">
          <Wifi className="w-3 h-3 mr-1" />
          Connected
        </Badge>
      );
    } else {
      return (
        <Badge variant="outline">
          <Activity className="w-3 h-3 mr-1" />
          Offline
        </Badge>
      );
    }
  };

  // Live price formatting
  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(price);
  };

  // Custom tooltip för chart
  const CustomTooltip = ({ active, payload, label }: {
    active?: boolean;
    payload?: Array<{
      payload: {
        price: number;
        high: number;
        low: number;
        volume: number;
        isLive: boolean;
      };
    }>;
    label?: string;
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border rounded shadow-lg">
          <p className="font-semibold">{label}</p>
          <p className="text-green-600">
            Price: {formatPrice(data.price)}
          </p>
          <p className="text-blue-600">
            High: {formatPrice(data.high)}
          </p>
          <p className="text-red-600">
            Low: {formatPrice(data.low)}
          </p>
          <p className="text-gray-600">
            Volume: {data.volume.toFixed(2)}
          </p>
        </div>
      );
    }
    return null;
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-2">
          <CardTitle className="text-2xl font-bold">
            {symbol} Price Chart
          </CardTitle>
          {getConnectionBadge()}
        </div>
        
        <div className="flex items-center space-x-2">
          {/* Live Price Display */}
          {ticker && (
            <div className="text-right">
              <div className="text-2xl font-bold text-green-600">
                {formatPrice(ticker.price)}
              </div>
              <div className="text-sm text-gray-500">
                Bid: {ticker.bid ? formatPrice(ticker.bid) : 'N/A'} | 
                Ask: {ticker.ask ? formatPrice(ticker.ask) : 'N/A'}
              </div>
            </div>
          )}
          
          {/* Control Buttons - simplified */}
          {showControls && (
            <Button
              variant="outline"
              size="sm"
              onClick={() => refreshData(true)}
            >
              <RefreshCw className="w-4 h-4" />
            </Button>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-300 rounded text-red-700">
            Error: {error}
          </div>
        )}

        {formattedChartData.length > 0 ? (
          <ResponsiveContainer width="100%" height={height}>
            <LineChart data={formattedChartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="timestamp" 
                tick={{ fontSize: 12 }}
              />
              <YAxis 
                domain={['dataMin - 100', 'dataMax + 100']}
                tick={{ fontSize: 12 }}
                tickFormatter={(value) => `$${value.toFixed(0)}`}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="price"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
                activeDot={{ 
                  r: 4, 
                  fill: connected ? '#10b981' : '#f59e0b',
                  stroke: '#fff',
                  strokeWidth: 2
                }}
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">
                Loading chart data...
              </p>
            </div>
          </div>
        )}

        {/* Data Source Info - simplified */}
        <div className="mt-4 flex justify-between items-center text-sm text-gray-500">
          <div>
            Data points: {chartData.length} | 
            Last update: {ticker ? new Date(ticker.timestamp).toLocaleTimeString() : 'N/A'}
          </div>
          
          <div className="flex items-center space-x-2">
            {connected && (
              <div className="flex items-center text-green-600">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse mr-1"></div>
                Optimized Updates
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};