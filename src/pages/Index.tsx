import { BalanceCard } from '@/components/BalanceCard';
import { BotControl } from '@/components/BotControl';
import { LogViewer } from '@/components/LogViewer';
import { ManualTradePanel } from '@/components/ManualTradePanel';
import { OrderBook } from '@/components/OrderBook';
import { OrderHistory } from '@/components/OrderHistory';
import { PriceChart } from '@/components/PriceChart';
import { SettingsPanel } from '@/components/SettingsPanel';
import { ThemeToggle } from '@/components/ThemeToggle';
import { TradeTable } from '@/components/TradeTable';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useWebSocket } from '@/hooks/useWebSocket';
import { api } from '@/lib/api';
import {
  Balance,
  BotStatus,
  EmaCrossoverBacktestResult,
  LogEntry,
  OHLCVData,
  OrderBook as OrderBookType,
  OrderHistoryItem,
  Trade
} from '@/types/trading';
import { useCallback, useEffect, useState, type FC } from 'react';

/**
 * Main dashboard page for the crypto trading application.
 * Displays balances, active trades, order history, charts, and control panels.
 */
const Index: FC = () => {
  // State management
  const [balances, setBalances] = useState<Balance[]>([]);
  const [activeTrades, setActiveTrades] = useState<Trade[]>([]);
  const [orderHistory, setOrderHistory] = useState<OrderHistoryItem[]>([]);
  const [botStatus, setBotStatus] = useState<BotStatus>({
    status: 'stopped',
    uptime: 0,
    last_update: new Date().toISOString()
  });
  const [orderBook, setOrderBook] = useState<OrderBookType | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [chartData, setChartData] = useState<OHLCVData[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [emaFast, setEmaFast] = useState<number[] | undefined>(undefined);
  const [emaSlow, setEmaSlow] = useState<number[] | undefined>(undefined);
  const [signals, setSignals] = useState<EmaCrossoverBacktestResult["signals"] | undefined>(undefined);

  const loadEmaCrossover = useCallback(async () => {
    try {
      // Mock: använd chartData för att skapa data-objekt
      const data = {
        timestamp: chartData.map(d => d.timestamp),
        open: chartData.map(d => d.open),
        high: chartData.map(d => d.high),
        low: chartData.map(d => d.low),
        close: chartData.map(d => d.close),
        volume: chartData.map(d => d.volume)
      };
      const result = await api.runBacktestEmaCrossover(data, {
        fast_period: 3,
        slow_period: 5,
        lookback: 5
      });
      setEmaFast(result.ema_fast);
      setEmaSlow(result.ema_slow);
      setSignals(result.signals);
    } catch (error) {
      console.error('Failed to load EMA crossover data:', error);
    }
  }, [chartData]);

  // WebSocket for real-time updates (prepared for future use)
  const { isConnected } = useWebSocket('ws://localhost:5000/ws', (data: unknown) => {
    console.log('WebSocket data received:', data);
    // Type guard for expected data shape
    if (typeof data === 'object' && data !== null && 'type' in data && 'data' in data) {
      const d = data as { type: string; data: OrderBookType | BotStatus };
      if (d.type === 'orderbook') {
        setOrderBook(d.data as OrderBookType);
      }
      if (d.type === 'status') {
        setBotStatus(d.data as BotStatus);
      }
    }
  });

  // Load initial data
  useEffect(() => {
    console.log('API keys:', Object.keys(api)); // Debug: logga vilka funktioner som finns på api-objektet
    loadAllData();
    loadEmaCrossover();
    
    // Set up periodic updates
    const interval = setInterval(() => {
      loadAllData();
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, [loadEmaCrossover]);

  const loadAllData = async () => {
    try {
      const [
        balancesData,
        tradesData,
        ordersData,
        statusData,
        orderBookData,
        logsData,
        chartDataResponse
      ] = await Promise.all([
        api.getBalances(),
        api.getActiveTrades(),
        api.getOrderHistory(),
        api.getBotStatus(),
        api.getOrderBook('BTCUSD'),
        api.getLogs(),
        api.getChartData('BTCUSD')
      ]);

      setBalances(balancesData);
      setActiveTrades(tradesData);
      setOrderHistory(ordersData);
      setBotStatus(statusData);
      setOrderBook(orderBookData);
      setLogs(logsData);
      setChartData(chartDataResponse);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold">Crypto Trading Dashboard</h1>
              <Badge variant="outline" className="text-xs">
                {isConnected ? '🟢 Connected' : '🔴 Offline'}
              </Badge>
            </div>
            <div className="flex items-center space-x-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setIsSettingsOpen(true)}
              >
                ⚙️ Settings
              </Button>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Dashboard */}
      <main className="container mx-auto px-6 py-6">
        <div className="grid grid-cols-12 gap-6">
          {/* Top Row - Key Metrics */}
          <div className="col-span-12 lg:col-span-3">
            <BalanceCard balances={balances} isLoading={isLoading} />
          </div>
          
          <div className="col-span-12 lg:col-span-3">
            <BotControl status={botStatus} onStatusChange={loadAllData} />
          </div>
          
          <div className="col-span-12 lg:col-span-3">
            <ManualTradePanel onOrderPlaced={loadAllData} />
          </div>
          
          <div className="col-span-12 lg:col-span-3">
            <TradeTable trades={activeTrades} isLoading={isLoading} />
          </div>

          {/* Second Row - Chart and Order Book */}
          <div className="col-span-12 lg:col-span-8">
            <PriceChart 
              data={chartData} 
              symbol="BTCUSD" 
              isLoading={isLoading} 
              emaFast={emaFast}
              emaSlow={emaSlow}
              signals={signals}
            />
          </div>
          
          <div className="col-span-12 lg:col-span-4">
            {orderBook && (
              <OrderBook orderBook={orderBook} isLoading={isLoading} />
            )}
          </div>

          {/* Third Row - Tables */}
          <div className="col-span-12 lg:col-span-6">
            <OrderHistory orders={orderHistory} isLoading={isLoading} onOrderCancelled={loadAllData} />
          </div>
          
          <div className="col-span-12 lg:col-span-6">
            <LogViewer logs={logs} isLoading={isLoading} />
          </div>
        </div>
      </main>

      {/* Settings Panel */}
      <SettingsPanel 
        isOpen={isSettingsOpen} 
        onClose={() => setIsSettingsOpen(false)} 
      />
    </div>
  );
};

export default Index;
