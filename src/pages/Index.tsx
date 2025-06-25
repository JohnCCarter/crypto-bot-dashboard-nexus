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
import { HybridTradeTable } from '@/components/HybridTradeTable';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { api } from '@/lib/api';
import { useGlobalWebSocketMarket } from '@/contexts/WebSocketMarketProvider';
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
import { Settings, RefreshCw, TrendingUp, Wifi, WifiOff } from 'lucide-react';

/**
 * Main dashboard page for the crypto trading application.
 * Now uses WebSocket live data instead of REST polling for real-time updates.
 */
const Index: FC = () => {
  // WebSocket Market Data - LIVE DATA!
  const { 
    connected: wsConnected, 
    connecting: wsConnecting,
    subscribeToSymbol,
    unsubscribeFromSymbol,
    getTickerForSymbol,
    getOrderbookForSymbol,
    platformStatus,
    error: wsError,
    latency
  } = useGlobalWebSocketMarket();

  // State management (reduced - most data comes from WebSocket now)
  const [balances, setBalances] = useState<Balance[]>([]);
  const [activeTrades, setActiveTrades] = useState<Trade[]>([]);
  const [orderHistory, setOrderHistory] = useState<OrderHistoryItem[]>([]);
  const [botStatus, setBotStatus] = useState<BotStatus>({
    status: 'stopped',
    uptime: 0,
    last_update: new Date().toISOString()
  });
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [chartData, setChartData] = useState<OHLCVData[]>([]);
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [emaFast, setEmaFast] = useState<number[] | undefined>(undefined);
  const [emaSlow, setEmaSlow] = useState<number[] | undefined>(undefined);
  const [signals, setSignals] = useState<EmaCrossoverBacktestResult["signals"] | undefined>(undefined);
  const [refreshKey, setRefreshKey] = useState(0);
  const { toast } = useToast();

  // Global symbol selection state
  const [selectedSymbol, setSelectedSymbol] = useState<string>('TESTBTC/TESTUSD');

  // Available trading symbols (paper trading)
  const SYMBOLS = [
    { label: 'BTCUSD', value: 'TESTBTC/TESTUSD' },
    { label: 'ETHUSD', value: 'TESTETH/TESTUSD' },
    { label: 'LTCUSD', value: 'TESTLTC/TESTUSD' }
  ];

  // Convert paper trading symbols to Bitfinex format for WebSocket
  const getBitfinexSymbol = (symbol: string) => {
    const mapping: Record<string, string> = {
      'TESTBTC/TESTUSD': 'tBTCUSD',
      'TESTETH/TESTUSD': 'tETHUSD', 
      'TESTLTC/TESTUSD': 'tLTCUSD'
    };
    return mapping[symbol] || 'tBTCUSD';
  };

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

  // Load initial data (only REST for non-market data)
  useEffect(() => {
    loadInitialData();
    
    // Subscribe to WebSocket data for selected symbol
    const bitfinexSymbol = getBitfinexSymbol(selectedSymbol);
    subscribeToSymbol(bitfinexSymbol);
    
    // Setup periodic updates only for non-market data
    const interval = setInterval(() => {
      loadNonMarketData();
    }, 10000); // Reduced frequency since market data is live

    return () => {
      clearInterval(interval);
      // Unsubscribe when changing symbols or unmounting
      unsubscribeFromSymbol(bitfinexSymbol);
    };
  }, [selectedSymbol, subscribeToSymbol, unsubscribeFromSymbol]);

  // Load EMA crossover data when chartData is available
  useEffect(() => {
    if (chartData.length > 0) {
      loadEmaCrossover();
    }
  }, [chartData, loadEmaCrossover]);

  const loadInitialData = async () => {
    try {
      setIsLoading(true);
      
      const [
        balancesData,
        tradesData,
        ordersData,
        statusData,
        logsData,
        chartDataResponse
      ] = await Promise.all([
        api.getBalances(),
        api.getActiveTrades(),
        api.getOrderHistory(),
        api.getBotStatus(),
        api.getLogs(),
        api.getChartData(selectedSymbol)
      ]);

      setBalances(balancesData);
      setActiveTrades(tradesData);
      setOrderHistory(ordersData);
      setBotStatus(statusData);
      setLogs(logsData);
      setChartData(chartDataResponse);
    } catch (error) {
      toast({
        title: "Data Loading Error",
        description: "Failed to load initial data",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  // Load only non-market data (balances, orders, logs, bot status)
  const loadNonMarketData = async () => {
    try {
      const [
        balancesData,
        tradesData,
        ordersData,
        statusData,
        logsData
      ] = await Promise.all([
        api.getBalances(),
        api.getActiveTrades(),
        api.getOrderHistory(),
        api.getBotStatus(),
        api.getLogs()
      ]);

      setBalances(balancesData);
      setActiveTrades(tradesData);
      setOrderHistory(ordersData);
      setBotStatus(statusData);
      setLogs(logsData);
    } catch (error) {
      // Silent error handling for background updates
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
    loadNonMarketData();
    fetchBotStatus();
  };

  // Get live market data from WebSocket
  const currentTicker = getTickerForSymbol(getBitfinexSymbol(selectedSymbol));
  const currentOrderbook = getOrderbookForSymbol(getBitfinexSymbol(selectedSymbol));

  // Connection status for display
  const isConnected = wsConnected && platformStatus === 'operative';

  return (
    <div className="min-h-screen bg-background text-foreground">
      {/* Header */}
      <header className="border-b border-border bg-card">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold">Crypto Trading Dashboard</h1>
              
              {/* Live Connection Status */}
              <div className="flex items-center space-x-2">
                {isConnected ? (
                  <Badge variant="default" className="bg-green-500">
                    <Wifi className="w-3 h-3 mr-1" />
                    Live Data
                  </Badge>
                ) : wsConnecting ? (
                  <Badge variant="outline">
                    <div className="w-3 h-3 mr-1 animate-spin rounded-full border border-gray-400 border-t-transparent"></div>
                    Connecting...
                  </Badge>
                ) : (
                  <Badge variant="destructive">
                    <WifiOff className="w-3 h-3 mr-1" />
                    Offline
                  </Badge>
                )}
                
                {/* Platform Status */}
                {platformStatus === 'maintenance' && (
                  <Badge variant="secondary" className="bg-yellow-500">
                    Maintenance
                  </Badge>
                )}
                
                {/* Latency Display */}
                {latency !== null && isConnected && (
                  <Badge variant="outline" className="text-xs">
                    {latency}ms
                  </Badge>
                )}
              </div>
              
              {/* Global Symbol Selector */}
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-muted-foreground" />
                <Select value={selectedSymbol} onValueChange={setSelectedSymbol}>
                  <SelectTrigger className="w-32">
                    <SelectValue placeholder="Symbol" />
                  </SelectTrigger>
                  <SelectContent>
                    {SYMBOLS.map((symbol) => (
                      <SelectItem key={symbol.value} value={symbol.value}>
                        {symbol.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              
              {/* Live Price Display */}
              {currentTicker && (
                <div className="text-sm">
                  <span className="font-semibold text-green-600">
                    ${currentTicker.price.toFixed(2)}
                  </span>
                  {currentTicker.bid && currentTicker.ask && (
                    <span className="text-gray-500 ml-2">
                      Spread: ${(currentTicker.ask - currentTicker.bid).toFixed(2)}
                    </span>
                  )}
                </div>
              )}
            </div>
            
            <div className="flex items-center space-x-2">
              <Button 
                variant="outline" 
                size="sm"
                onClick={handleRefresh}
                disabled={isLoading}
              >
                <RefreshCw className={`w-4 h-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
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

      {/* Error Display */}
      {wsError && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4">
          <p className="font-bold">WebSocket Error:</p>
          <p>{wsError}</p>
        </div>
      )}

      {/* Main Dashboard */}
      <main className="container mx-auto px-6 py-6">
        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="dashboard">Trading Dashboard - Live Data</TabsTrigger>
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
                <HybridTradeTable 
                  symbol={selectedSymbol} 
                  maxTrades={5}
                />
              </div>

              {/* Second Row - Chart and Order Book - LIVE DATA */}
              <div className="col-span-12 lg:col-span-8">
                <HybridPriceChart 
                  symbol={getBitfinexSymbol(selectedSymbol)}
                  height={400}
                  showControls={true}
                />
              </div>
              
              <div className="col-span-12 lg:col-span-4">
                <HybridOrderBook 
                  symbol={getBitfinexSymbol(selectedSymbol)}
                  maxLevels={10}
                  showControls={true}
                />
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
