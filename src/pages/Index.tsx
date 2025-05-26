
import { useEffect, useState } from 'react';
import { BalanceCard } from '@/components/BalanceCard';
import { TradeTable } from '@/components/TradeTable';
import { OrderHistory } from '@/components/OrderHistory';
import { BotControl } from '@/components/BotControl';
import { PriceChart } from '@/components/PriceChart';
import { OrderBook } from '@/components/OrderBook';
import { LogViewer } from '@/components/LogViewer';
import { SettingsPanel } from '@/components/SettingsPanel';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { useWebSocket } from '@/hooks/useWebSocket';
import {
  Balance,
  Trade,
  OrderHistoryItem,
  BotStatus,
  OrderBook as OrderBookType,
  LogEntry,
  OHLCVData
} from '@/types/trading';

const Index = () => {
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

  // WebSocket for real-time updates (prepared for future use)
  const { isConnected } = useWebSocket('ws://localhost:5000/ws', (data) => {
    console.log('WebSocket data received:', data);
    // Handle real-time updates here
    if (data.type === 'orderbook') {
      setOrderBook(data.data);
    }
    if (data.type === 'status') {
      setBotStatus(data.data);
    }
  });

  // Load initial data
  useEffect(() => {
    loadAllData();
    
    // Set up periodic updates
    const interval = setInterval(() => {
      loadAllData();
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

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
          
          <div className="col-span-12 lg:col-span-6">
            <TradeTable trades={activeTrades} isLoading={isLoading} />
          </div>

          {/* Second Row - Chart and Order Book */}
          <div className="col-span-12 lg:col-span-8">
            <PriceChart 
              data={chartData} 
              symbol="BTCUSD" 
              isLoading={isLoading} 
            />
          </div>
          
          <div className="col-span-12 lg:col-span-4">
            {orderBook && (
              <OrderBook orderBook={orderBook} isLoading={isLoading} />
            )}
          </div>

          {/* Third Row - Tables */}
          <div className="col-span-12 lg:col-span-6">
            <OrderHistory orders={orderHistory} isLoading={isLoading} />
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
