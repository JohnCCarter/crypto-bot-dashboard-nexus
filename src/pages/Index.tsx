import { ActivePositionsCard } from '@/components/ActivePositionsCard';
import { BotControl } from '@/components/BotControl';
import { HybridBalanceCard } from '@/components/HybridBalanceCard';
import { HybridOrderBook } from '@/components/HybridOrderBook';
import { HybridPriceChart } from '@/components/HybridPriceChart';
import { LogViewer } from '@/components/LogViewer';
import { ManualTradePanel } from '@/components/ManualTradePanel';
import { OrderHistory } from '@/components/OrderHistory';
import { PortfolioSummaryCard } from '@/components/PortfolioSummaryCard';
import ProbabilityAnalysis from '@/components/ProbabilityAnalysis';
import { SettingsPanel } from '@/components/SettingsPanel';
import { ThemeToggle } from '@/components/ThemeToggle';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api';
import {
  LogEntry,
  OHLCVData,
  OrderHistoryItem
} from '@/types/trading';
import { RefreshCw, Settings, TrendingUp, Zap } from 'lucide-react';
import { useCallback, useEffect, useState, type FC } from 'react';
import { Link } from 'react-router-dom';

/**
 * Main dashboard page for the crypto trading application.
 * Displays balances, active trades, order history, charts, and control panels.
 */
const Index: FC = () => {
  // State management
  const [botStatus, setBotStatus] = useState<{ status: string; uptime: number; last_update: string }>({
    status: 'stopped',
    uptime: 0,
    last_update: new Date().toISOString()
  });
  const [orderHistory, setOrderHistory] = useState<OrderHistoryItem[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [chartData, setChartData] = useState<OHLCVData[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isConnected, setIsConnected] = useState(false);
  const { toast } = useToast();

  // Global symbol selection state
  const [selectedSymbol, setSelectedSymbol] = useState<string>('BTCUSD');

  // Refresh key for manual refresh
  const [refreshKey, setRefreshKey] = useState(0);

  // Available trading symbols
  const SYMBOLS = ['BTCUSD', 'ETHUSD', 'LTCUSD', 'XRPUSD', 'ADAUSD'];

  const loadEmaCrossover = useCallback(async () => {
    try {
      // Säkerhetskontroll: Se till att vi har chartData
      if (!chartData || chartData.length === 0) {
        return;
      }

      // Mock: använd chartData för att skapa data-objekt
      const data = {
        timestamp: chartData.map(d => d.timestamp),
        open: chartData.map(d => d.open),
        high: chartData.map(d => d.high),
        low: chartData.map(d => d.low),
        close: chartData.map(d => d.close),
        volume: chartData.map(d => d.volume)
      };
      
      await api.runBacktestEmaCrossover(data, {
        fast_period: 3,
        slow_period: 5,
        lookback: 5
      });
    } catch {
      // Reset EMA data on error to prevent stale data
    }
  }, [chartData]);

  // Load initial data
  useEffect(() => {
    loadAllData();
    
    // OPTIMIZED: Längre intervall för att minska nonce consumption
    // Tidigare: 15s med 7 parallella calls = race conditions
    // Nu: 30s med sekventiella calls = nonce-safe
    const interval = setInterval(() => {
      loadAllDataSequentially();
    }, 30000); // Ökat från 15s till 30s för nonce-säkerhet

    return () => clearInterval(interval);
  }, [selectedSymbol]);

  // Load EMA crossover data when chartData is available
  useEffect(() => {
    if (chartData.length > 0) {
      loadEmaCrossover();
    }
  }, [chartData, loadEmaCrossover]);

  // OPTIMIZED: Sekventiell data loading för att förhindra nonce conflicts
  const loadAllDataSequentially = async () => {
    try {
      // STEG 1: Kritisk data först (mest sannolikt cached)
      const statusData = await api.getBotStatus();
      setBotStatus(statusData);
      
      // STEG 2: Balances (ofta cached i 90s)
      await new Promise(resolve => setTimeout(resolve, 200)); // 200ms delay mellan calls
      await api.getBalances();
      
      // STEG 3: Positions och trades
      await new Promise(resolve => setTimeout(resolve, 200));
      await api.getActiveTrades();
      
      // STEG 4: Order history (låg prioritet, kan vara cached längre)
      await new Promise(resolve => setTimeout(resolve, 200));
      const ordersData = await api.getOrderHistory();
      setOrderHistory(ordersData);
      
      // STEG 5: Market data (använd WebSocket när möjligt)
      await new Promise(resolve => setTimeout(resolve, 200));
      await api.getOrderBook(selectedSymbol);
      
      // STEG 6: Chart data (låg prioritet)
      await new Promise(resolve => setTimeout(resolve, 200));
      const chartDataResponse = await api.getChartData(selectedSymbol);
      setChartData(chartDataResponse);
      
      // STEG 7: Logs (lägsta prioritet)
      await new Promise(resolve => setTimeout(resolve, 200));
      const logsData = await api.getLogs();
      setLogs(logsData);
      
      setIsConnected(true);
      console.log('✅ Sequential data load completed - nonce-safe approach');
    } catch {
      setIsConnected(false);
      console.error('❌ Sequential data load failed');
    } finally {
      setIsLoading(false);
    }
  };

  // ORIGINAL: Parallell loading för initial load (behålls för snabbare start)
  const loadAllData = async () => {
    try {
      const [
        ,
        ,
        ordersData,
        statusData,
        ,
        ,
        chartDataResponse
      ] = await Promise.all([
        api.getBalances(),
        api.getActiveTrades(),
        api.getOrderHistory(),
        api.getBotStatus(),
        api.getOrderBook(selectedSymbol),
        api.getLogs(),
        api.getChartData(selectedSymbol)
      ]);

      setBotStatus(statusData);
      setOrderHistory(ordersData);
      setChartData(chartDataResponse);
      setIsConnected(true);
      console.log('✅ Parallel initial load completed');
    } catch {
      setIsConnected(false);
      console.error('❌ Parallel initial load failed');
    } finally {
      setIsLoading(false);
    }
  };

  const fetchBotStatus = async () => {
    try {
      const status = await api.getBotStatus();
      setBotStatus(status);
    } catch {
      toast({
        title: "Status Error",
        description: "Failed to fetch bot status",
        variant: "destructive",
      });
    }
  };

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
    // OPTIMIZED: Använd sekventiell refresh för att förhindra nonce conflicts
    loadAllDataSequentially();
  };

  useEffect(() => {
    fetchBotStatus();
    
    // OPTIMIZED: Mycket längre intervall för status (ofta cached)
    // Status ändras sällan, så längre polling är OK
    const interval = setInterval(() => {
      fetchBotStatus();
    }, 120000); // Ökat från 60s till 120s för nonce-besparingar

    return () => {
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
              {/* Global Symbol Selector */}
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-muted-foreground" />
                <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
                  <SelectTrigger className="w-[120px]">
                    <SelectValue placeholder="Symbol" />
                  </SelectTrigger>
                  <SelectContent>
                    {SYMBOLS.map((symbol) => (
                      <SelectItem key={symbol} value={symbol}>
                        {symbol}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="flex items-center space-x-4">
              {/* FastAPI Demo Link */}
              <Link to="/fastapi-demo" className="flex items-center space-x-2 px-3 py-2 rounded-md bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 hover:bg-blue-200 dark:hover:bg-blue-800 transition-colors">
                <Zap className="w-4 h-4" />
                <span>FastAPI Demo</span>
              </Link>
              
              <Button 
                variant="outline" 
                size="icon"
                onClick={handleRefresh}
                title="Refresh Data"
              >
                <RefreshCw className="h-4 w-4" />
              </Button>
              <Button 
                variant="outline" 
                size="icon"
                onClick={() => setIsSettingsOpen(true)}
                title="Settings"
              >
                <Settings className="h-4 w-4" />
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
                <HybridBalanceCard 
                  symbol={selectedSymbol} 
                  showDetails={true}
                />
              </div>
              
              <div className="col-span-12 lg:col-span-3">
                <BotControl status={botStatus} onStatusChange={fetchBotStatus} />
              </div>
              
              <div className="col-span-12 lg:col-span-3">
                <ManualTradePanel 
                  symbol={selectedSymbol}
                  onOrderPlaced={handleRefresh} 
                />
              </div>
              
              <div className="col-span-12 lg:col-span-3">
                <ActivePositionsCard 
                  showOnlySymbol={false}
                  maxPositions={5}
                />
              </div>

              {/* Second Row - Chart and Order Book */}
              <div className="col-span-12 lg:col-span-8">
                <HybridPriceChart 
                  symbol={selectedSymbol} 
                  height={400}
                  showControls={true}
                />
              </div>
              
              <div className="col-span-12 lg:col-span-4">
                <HybridOrderBook 
                  symbol={selectedSymbol} 
                  maxLevels={10}
                  showControls={true}
                />
              </div>

              {/* Third Row - Portfolio Summary and History */}
              <div className="col-span-12 lg:col-span-4">
                <PortfolioSummaryCard />
              </div>
              
              <div className="col-span-12 lg:col-span-4">
                <OrderHistory orders={orderHistory} isLoading={isLoading} onOrderCancelled={handleRefresh} />
              </div>
              
              <div className="col-span-12 lg:col-span-4">
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
