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
import { useOptimizedMarketData } from '@/hooks/useOptimizedMarketData';
import { Settings, RefreshCw, TrendingUp } from 'lucide-react';

/**
 * Main dashboard page for the crypto trading application.
 * Displays balances, active trades, order history, charts, and control panels.
 */
const Index: FC = () => {
  // Global symbol selection state
  const [selectedSymbol, setSelectedSymbol] = useState<string>('BTCUSD');
  
  // Use optimized market data hook (replaces all individual state and polling)
  const {
    balances,
    activeTrades,
    orderHistory,
    botStatus,
    orderbook,
    logs,
    chartData,
    ticker,
    connected,
    error,
    refreshData
  } = useOptimizedMarketData(selectedSymbol);
  
  // UI state
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [emaFast, setEmaFast] = useState<number[] | undefined>(undefined);
  const [emaSlow, setEmaSlow] = useState<number[] | undefined>(undefined);
  const [signals, setSignals] = useState<EmaCrossoverBacktestResult["signals"] | undefined>(undefined);
  const [refreshKey, setRefreshKey] = useState(0);
  const { toast } = useToast();

  // Available trading symbols
  const SYMBOLS = ['BTCUSD', 'ETHUSD', 'LTCUSD', 'XRPUSD', 'ADAUSD'];

  // No longer needed - data loading handled by useOptimizedMarketData hook

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

  // Loading state management
  useEffect(() => {
    if (connected || error) {
      setIsLoading(false);
    }
  }, [connected, error]);

  // Load EMA crossover data when chartData is available
  useEffect(() => {
    if (chartData.length > 0) {
      loadEmaCrossover();
    }
  }, [chartData, loadEmaCrossover]);

  const handleRefresh = () => {
    setRefreshKey(prev => prev + 1);
    refreshData(true); // Force refresh all data
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
                <HybridTradeTable 
                  symbol={selectedSymbol} 
                  maxTrades={5}
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
