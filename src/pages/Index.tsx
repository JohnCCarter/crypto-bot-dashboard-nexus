import { BalanceCard } from '@/components/BalanceCard';
import { BotControl } from '@/components/BotControl';
import { LogViewer } from '@/components/LogViewer';
import { ManualTradePanel } from '@/components/ManualTradePanel';
import { OrderBook } from '@/components/OrderBook';
import { OrderHistory } from '@/components/OrderHistory';
import { PriceChart } from '@/components/PriceChart';
import ProbabilityAnalysis from '@/components/ProbabilityAnalysis';
import { SettingsPanel } from '@/components/SettingsPanel';
import { ThemeToggle } from '@/components/ThemeToggle';
import { TradeTable } from '@/components/TradeTable';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
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
import { useToast } from '@/hooks/use-toast';
import { Settings, RefreshCw } from 'lucide-react';

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
  const [refreshKey, setRefreshKey] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const { toast } = useToast();

  const loadEmaCrossover = useCallback(async () => {
    try {
      // Säkerhetskontroll: Se till att vi har chartData
      if (!chartData || chartData.length === 0) {
        console.log('❌ No chart data available for EMA crossover backtest');
        return;
      }

      console.log(`📊 loadEmaCrossover called with ${chartData.length} data points`);

      // Mock: använd chartData för att skapa data-objekt
      const data = {
        timestamp: chartData.map(d => d.timestamp),
        open: chartData.map(d => d.open),
        high: chartData.map(d => d.high),
        low: chartData.map(d => d.low),
        close: chartData.map(d => d.close),
        volume: chartData.map(d => d.volume)
      };
      
      console.log('🚀 Sending backtest data:', { dataLength: data.timestamp.length, sample: data.timestamp.slice(0, 3) });
      
      const result = await api.runBacktestEmaCrossover(data, {
        fast_period: 3,
        slow_period: 5,
        lookback: 5
      });
      setEmaFast(result.ema_fast);
      setEmaSlow(result.ema_slow);
      setSignals(result.signals);
      console.log('✅ EMA crossover loaded successfully');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('❌ Failed to load EMA crossover data:', errorMessage);
      console.error('❌ Full error object:', error);
      
      // Log detailed error information for debugging
      console.error('❌ Error details:', {
        chartDataLength: chartData?.length || 0,
        timestamp: new Date().toISOString(),
        userAgent: navigator.userAgent
      });
      
      // Reset EMA data on error to prevent stale data
      setEmaFast(undefined);
      setEmaSlow(undefined);
      setSignals(undefined);
    }
  }, [chartData]);

  // Load initial data
  useEffect(() => {
    console.log('API keys:', Object.keys(api)); // Debug: logga vilka funktioner som finns på api-objektet
    loadAllData();
    
    // Set up periodic updates
    const interval = setInterval(() => {
      loadAllData();
    }, 5000); // Update every 5 seconds

    return () => clearInterval(interval);
  }, []);

  // Load EMA crossover data when chartData is available
  useEffect(() => {
    if (chartData.length > 0) {
      loadEmaCrossover();
    }
  }, [chartData, loadEmaCrossover]);

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

      console.log(`📈 Chart data loaded: ${chartDataResponse.length} data points`);
      setBalances(balancesData);
      setActiveTrades(tradesData);
      setOrderHistory(ordersData);
      setBotStatus(statusData);
      setOrderBook(orderBookData);
      setLogs(logsData);
      setChartData(chartDataResponse);
      setIsConnected(true); // Set connected to true when API calls succeed
    } catch (error) {
      console.error('Failed to load data:', error);
      setIsConnected(false); // Set connected to false when API calls fail
    } finally {
      setIsLoading(false);
    }
  };

  const fetchBotStatus = async () => {
    console.log('🏠 [Index] Fetching bot status...');
    try {
      const status = await api.getBotStatus();
      console.log('✅ [Index] Bot status fetched:', status);
      setBotStatus(status);
    } catch (error) {
      console.error('❌ [Index] Failed to fetch bot status:', error);
      toast({
        title: "Status Error",
        description: "Failed to fetch bot status",
        variant: "destructive",
      });
    }
  };

  const handleRefresh = () => {
    console.log('🏠 [Index] Manual refresh triggered');
    setRefreshKey(prev => prev + 1);
    fetchBotStatus();
  };

  useEffect(() => {
    console.log('🏠 [Index] Component mounted, fetching initial bot status');
    fetchBotStatus();
    
    // Set up periodic status updates
    const interval = setInterval(() => {
      console.log('🏠 [Index] Periodic status update');
      fetchBotStatus();
    }, 30000); // Update every 30 seconds

    return () => {
      console.log('🏠 [Index] Component unmounting, clearing interval');
      clearInterval(interval);
    };
  }, []);

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
                onClick={handleRefresh}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh
              </Button>
              <Button 
                variant="outline" 
                size="sm"
                onClick={() => setIsSettingsOpen(true)}
              >
                <Settings className="w-4 h-4 mr-2" />
                ⚙️ Settings
              </Button>
              <ThemeToggle />
            </div>
          </div>
        </div>
      </header>

      {/* Main Dashboard */}
      <main className="container mx-auto px-6 py-6">
        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="dashboard">Trading Dashboard</TabsTrigger>
            <TabsTrigger value="analysis">Probability Analysis</TabsTrigger>
          </TabsList>
          
          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid grid-cols-12 gap-6">
              {/* Top Row - Key Metrics */}
              <div className="col-span-12 lg:col-span-3">
                <BalanceCard balances={balances} isLoading={isLoading} />
              </div>
              
              <div className="col-span-12 lg:col-span-3">
                <BotControl status={botStatus} onStatusChange={fetchBotStatus} />
              </div>
              
              <div className="col-span-12 lg:col-span-3">
                <ManualTradePanel onOrderPlaced={handleRefresh} />
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
                <OrderHistory orders={orderHistory} isLoading={isLoading} onOrderCancelled={handleRefresh} />
              </div>
              
              <div className="col-span-12 lg:col-span-6">
                <LogViewer logs={logs} isLoading={isLoading} />
              </div>
            </div>
          </TabsContent>
          
          <TabsContent value="analysis" className="space-y-6">
            <ProbabilityAnalysis />
          </TabsContent>
        </Tabs>
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
