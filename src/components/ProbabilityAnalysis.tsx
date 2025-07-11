import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Progress } from './ui/progress';
import { Alert, AlertDescription } from './ui/alert';
import { TrendingUp, TrendingDown, Minus, AlertTriangle, BarChart3 } from 'lucide-react';

interface ProbabilityData {
  buy: number;
  sell: number;
  hold: number;
}

interface StrategySignal {
  action: string;
  confidence: number;
  position_size: number;
  metadata: {
    probability_buy: number;
    probability_sell: number;
    probability_hold: number;
    [key: string]: number | string | boolean;
  };
}

interface CombinedSignal {
  action: string;
  combined_confidence: number;
  probabilities: ProbabilityData;
  risk_score: number;
  metadata: {
    strategies_used: string[];
    combination_method: string;
    [key: string]: string[] | string | number | boolean;
  };
}

interface AnalysisResult {
  symbol: string;
  current_price: number;
  analysis_timestamp: string;
  individual_signals: Record<string, StrategySignal>;
  combined_signal: CombinedSignal;
  strategies_analyzed: number;
  valid_signals: number;
}

const ProbabilityAnalysis: React.FC = () => {
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedSymbol, setSelectedSymbol] = useState('BTC/USD');

  const runAnalysis = async () => {
    setLoading(true);
    setError(null);

    try {
      // Generate sample OHLC data for demonstration
      const sampleData = generateSampleData(100);
      
      const requestData = {
        symbol: selectedSymbol,
        timeframe: '1h',
        data: sampleData,
        strategies: {
          ema_crossover: { fast_period: 12, slow_period: 26 },
          rsi: { rsi_period: 14, overbought: 70, oversold: 30 },
          fvg: { lookback: 3 }
        }
      };

      const response = await fetch('/api/strategy/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (!response.ok) {
        throw new Error(`Analysis failed: ${response.statusText}`);
      }

      const result = await response.json();
      setAnalysisResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred');
    } finally {
      setLoading(false);
    }
  };

  const generateSampleData = (count: number) => {
    const data = [];
    let price = 50000;
    
    for (let i = 0; i < count; i++) {
      const volatility = 0.02;
      const change = (Math.random() - 0.5) * volatility * price;
      price = Math.max(1000, price + change);
      
      const open = price;
      const high = open + Math.random() * 0.01 * open;
      const low = open - Math.random() * 0.01 * open;
      const close = low + Math.random() * (high - low);
      
      data.push({ open, high, low, close });
    }
    
    return data;
  };

  const formatPercentage = (value: number) => `${(value * 100).toFixed(1)}%`;
  
  const getActionIcon = (action: string) => {
    switch (action) {
      case 'buy': return <TrendingUp className="w-4 h-4 text-green-500" />;
      case 'sell': return <TrendingDown className="w-4 h-4 text-red-500" />;
      default: return <Minus className="w-4 h-4 text-gray-500" />;
    }
  };

  const getActionColor = (action: string) => {
    switch (action) {
      case 'buy': return 'bg-green-100 text-green-800';
      case 'sell': return 'bg-red-100 text-red-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getRiskColor = (riskScore: number) => {
    if (riskScore < 0.3) return 'text-green-600';
    if (riskScore < 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getRiskLabel = (riskScore: number) => {
    if (riskScore < 0.3) return 'Low Risk';
    if (riskScore < 0.6) return 'Medium Risk';
    return 'High Risk';
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Probability-Based Strategy Analysis
          </CardTitle>
          <CardDescription>
            Analyze multiple trading strategies with advanced probability calculations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 items-end">
            <div>
              <label className="block text-sm font-medium mb-2">Symbol</label>
              <select 
                value={selectedSymbol}
                onChange={(e) => setSelectedSymbol(e.target.value)}
                className="border rounded px-3 py-2"
              >
                <option value="BTC/USD">BTC/USD</option>
                <option value="ETH/USD">ETH/USD</option>
                <option value="ADA/USD">ADA/USD</option>
              </select>
            </div>
            <Button 
              onClick={runAnalysis}
              disabled={loading}
              className="flex items-center gap-2"
            >
              {loading ? 'Analyzing...' : 'Run Analysis'}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {error && (
        <Alert className="border-red-200">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {/* Analysis Results */}
      {analysisResult && (
        <div className="grid gap-6">
          {/* Combined Signal */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center justify-between">
                <span>Combined Signal</span>
                <Badge className={getActionColor(analysisResult.combined_signal.action)}>
                  {getActionIcon(analysisResult.combined_signal.action)}
                  {analysisResult.combined_signal.action.toUpperCase()}
                </Badge>
              </CardTitle>
              <CardDescription>
                Aggregated signal from {analysisResult.valid_signals} strategies
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="text-sm font-medium text-gray-600">Confidence</label>
                  <div className="mt-1">
                    <Progress 
                      value={analysisResult.combined_signal.combined_confidence * 100} 
                      className="h-2"
                    />
                    <span className="text-sm text-gray-500">
                      {formatPercentage(analysisResult.combined_signal.combined_confidence)}
                    </span>
                  </div>
                </div>
                
                <div>
                  <label className="text-sm font-medium text-gray-600">Risk Score</label>
                  <div className={`text-lg font-semibold ${getRiskColor(analysisResult.combined_signal.risk_score)}`}>
                    {formatPercentage(analysisResult.combined_signal.risk_score)}
                    <span className="text-sm ml-2">
                      ({getRiskLabel(analysisResult.combined_signal.risk_score)})
                    </span>
                  </div>
                </div>

                <div>
                  <label className="text-sm font-medium text-gray-600">Current Price</label>
                  <div className="text-lg font-semibold">
                    ${analysisResult.current_price.toLocaleString()}
                  </div>
                </div>
              </div>

              {/* Probability Breakdown */}
              <div>
                <h4 className="font-medium mb-3">Action Probabilities</h4>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <TrendingUp className="w-4 h-4 text-green-500" />
                      Buy
                    </span>
                    <div className="flex items-center gap-2 w-48">
                      <Progress 
                        value={analysisResult.combined_signal.probabilities.buy * 100} 
                        className="h-2 flex-1"
                      />
                      <span className="text-sm font-medium w-12">
                        {formatPercentage(analysisResult.combined_signal.probabilities.buy)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <TrendingDown className="w-4 h-4 text-red-500" />
                      Sell
                    </span>
                    <div className="flex items-center gap-2 w-48">
                      <Progress 
                        value={analysisResult.combined_signal.probabilities.sell * 100} 
                        className="h-2 flex-1"
                      />
                      <span className="text-sm font-medium w-12">
                        {formatPercentage(analysisResult.combined_signal.probabilities.sell)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-2">
                      <Minus className="w-4 h-4 text-gray-500" />
                      Hold
                    </span>
                    <div className="flex items-center gap-2 w-48">
                      <Progress 
                        value={analysisResult.combined_signal.probabilities.hold * 100} 
                        className="h-2 flex-1"
                      />
                      <span className="text-sm font-medium w-12">
                        {formatPercentage(analysisResult.combined_signal.probabilities.hold)}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Individual Strategy Signals */}
          <Card>
            <CardHeader>
              <CardTitle>Individual Strategy Signals</CardTitle>
              <CardDescription>
                Detailed breakdown of signals from each strategy
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid gap-4">
                {Object.entries(analysisResult.individual_signals).map(([strategyName, signal]) => (
                  <div key={strategyName} className="border rounded-lg p-4">
                    <div className="flex items-center justify-between mb-3">
                      <h4 className="font-medium capitalize">
                        {strategyName.replace('_', ' ')} Strategy
                      </h4>
                      <Badge className={getActionColor(signal.action)}>
                        {getActionIcon(signal.action)}
                        {signal.action.toUpperCase()}
                      </Badge>
                    </div>
                    
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                      <div>
                        <span className="text-gray-600">Confidence:</span>
                        <div className="font-medium">{formatPercentage(signal.confidence)}</div>
                      </div>
                      <div>
                        <span className="text-gray-600">Buy Prob:</span>
                        <div className="font-medium text-green-600">
                          {formatPercentage(signal.metadata.probability_buy)}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-600">Sell Prob:</span>
                        <div className="font-medium text-red-600">
                          {formatPercentage(signal.metadata.probability_sell)}
                        </div>
                      </div>
                      <div>
                        <span className="text-gray-600">Hold Prob:</span>
                        <div className="font-medium text-gray-600">
                          {formatPercentage(signal.metadata.probability_hold)}
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Analysis Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Analysis Summary</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                <div className="text-center">
                  <div className="text-2xl font-bold text-blue-600">
                    {analysisResult.strategies_analyzed}
                  </div>
                  <div className="text-gray-600">Strategies Analyzed</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-green-600">
                    {analysisResult.valid_signals}
                  </div>
                  <div className="text-gray-600">Valid Signals</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-purple-600">
                    {analysisResult.combined_signal.metadata.combination_method}
                  </div>
                  <div className="text-gray-600">Method</div>
                </div>
                <div className="text-center">
                  <div className="text-2xl font-bold text-orange-600">
                    {new Date(analysisResult.analysis_timestamp).toLocaleTimeString()}
                  </div>
                  <div className="text-gray-600">Analysis Time</div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default ProbabilityAnalysis;