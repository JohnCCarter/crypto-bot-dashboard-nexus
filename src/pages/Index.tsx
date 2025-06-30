import { HybridBalanceCard } from '@/components/HybridBalanceCard';
import { BotControl } from '@/components/BotControl';
import { LogViewer } from '@/components/LogViewer';
import { ManualTradePanel } from '@/components/ManualTradePanel';
import { HybridOrderBook } from '@/components/HybridOrderBook';
import { OrderHistory } from '@/components/OrderHistory';
import { HybridPriceChart } from '@/components/HybridPriceChart';
import ProbabilityAnalysis from '@/components/ProbabilityAnalysis';
import { SettingsPanel } from '@/components/SettingsPanel';
import { ThemeToggle } from '@/components/ThemeToggle';
import { ActivePositionsCard } from '@/components/ActivePositionsCard';
import { PortfolioSummaryCard } from '@/components/PortfolioSummaryCard';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
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
import { Settings, RefreshCw, TrendingUp } from 'lucide-react';

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

  // Global symbol selection state
  const [selectedSymbol, setSelectedSymbol] = useState<string>('BTCUSD');

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
      
      const result = await api.runBacktestEmaCrossover(data, {
        fast_period: 3,
        slow_period: 5,
        lookback: 5
      });
      setEmaFast(result.ema_fast);
      setEmaSlow(result.ema_slow);
      setSignals(result.signals);
    } catch (error) {
      // Reset EMA data on error to prevent stale data
      setEmaFast(undefined);
      setEmaSlow(undefined);
      setSignals(undefined);
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
      const balancesData = await api.getBalances();
      setBalances(balancesData);
      
      // STEG 3: Positions och trades
      await new Promise(resolve => setTimeout(resolve, 200));
      const tradesData = await api.getActiveTrades();
      setActiveTrades(tradesData);
      
      // STEG 4: Order history (låg prioritet, kan vara cached längre)
      await new Promise(resolve => setTimeout(resolve, 200));
      const ordersData = await api.getOrderHistory();
      setOrderHistory(ordersData);
      
      // STEG 5: Market data (använd WebSocket när möjligt)
      await new Promise(resolve => setTimeout(resolve, 200));
      const orderBookData = await api.getOrderBook(selectedSymbol);
      setOrderBook(orderBookData);
      
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
    } catch (error) {
      setIsConnected(false);
      console.error('❌ Sequential data load failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  // ORIGINAL: Parallell loading för initial load (behålls för snabbare start)
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
        api.getOrderBook(selectedSymbol),
        api.getLogs(),
        api.getChartData(selectedSymbol)
      ]);

      setBalances(balancesData);
      setActiveTrades(tradesData);
      setOrderHistory(ordersData);
      setBotStatus(statusData);
      setOrderBook(orderBookData);
      setLogs(logsData);
      setChartData(chartDataResponse);
      setIsConnected(true);
      console.log('✅ Parallel initial load completed');
    } catch (error) {
      setIsConnected(false);
      console.error('❌ Parallel initial load failed:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const fetchBotStatus = async () => {
    try {
      const status = await api.getBotStatus();
      setBotStatus(status);
    } catch (error) {
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
                  <SelectTrigger className="w-32">
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
