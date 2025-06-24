import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Label } from './ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './ui/tabs';
import { Badge } from './ui/badge';
import { Alert, AlertDescription } from './ui/alert';
import { TrendingUp, TrendingDown, DollarSign, Zap, AlertTriangle, CheckCircle } from 'lucide-react';
import { useWebSocketAccount } from '../contexts/WebSocketAccountProvider';
import { useGlobalWebSocketMarket } from '../contexts/WebSocketMarketProvider';

/**
 * WebSocket Trading Panel - Live trading via Bitfinex WebSocket WS Input Commands
 * Implementerar alla trading operationer från Bitfinex WS Inputs dokumentation
 */
export const WebSocketTradePanel: React.FC = () => {
  const {
    authenticated,
    orders,
    balances,
    marginInfo,
    fundingInfo,
    newOrder,
    updateOrder,
    cancelOrder,
    cancelAllOrders,
    newFundingOffer,
    cancelFundingOffer,
    calcRequest,
    getActiveOrders,
    getTotalBalance,
    getMarginRequirement,
    getTradableBalance
  } = useWebSocketAccount();

  const { tickers } = useGlobalWebSocketMarket();

  // Trading form states
  const [symbol, setSymbol] = useState('tBTCUSD');
  const [orderType, setOrderType] = useState('LIMIT');
  const [amount, setAmount] = useState('');
  const [price, setPrice] = useState('');
  const [side, setSide] = useState<'buy' | 'sell'>('buy');
  
  // Funding form states
  const [fundingSymbol, setFundingSymbol] = useState('fUSD');
  const [fundingAmount, setFundingAmount] = useState('');
  const [fundingRate, setFundingRate] = useState('');
  const [fundingPeriod, setFundingPeriod] = useState('7');
  
  // UI states
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);
  const [selectedOrderId, setSelectedOrderId] = useState<string>('');

  // Auto-update price från ticker data
  useEffect(() => {
    const ticker = tickers[symbol];
    if (ticker && !price) {
      setPrice(ticker.price.toString());
    }
  }, [symbol, tickers, price]);

  // Clear message after 5 seconds
  useEffect(() => {
    if (message) {
      const timer = setTimeout(() => setMessage(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [message]);

  const handleNewOrder = async () => {
    if (!authenticated) {
      setMessage({ type: 'error', text: 'Inte autentiserad - logga in först' });
      return;
    }

    if (!amount || !symbol) {
      setMessage({ type: 'error', text: 'Symbol och belopp krävs' });
      return;
    }

    if (orderType === 'LIMIT' && !price) {
      setMessage({ type: 'error', text: 'Pris krävs för limit-ordrar' });
      return;
    }

    setLoading(true);
    setMessage(null);

    try {
      const orderAmount = side === 'buy' ? Math.abs(parseFloat(amount)) : -Math.abs(parseFloat(amount));
      
      const success = await newOrder({
        type: orderType,
        symbol: symbol,
        amount: orderAmount,
        price: orderType === 'LIMIT' ? parseFloat(price) : undefined,
        flags: 0
      });

      if (success) {
        setMessage({ type: 'success', text: `${side.toUpperCase()} order skickad: ${Math.abs(orderAmount)} ${symbol}` });
        // Reset form
        setAmount('');
        if (orderType === 'MARKET') setPrice('');
      } else {
        setMessage({ type: 'error', text: 'Kunde inte skicka order' });
      }
    } catch (error) {
      setMessage({ type: 'error', text: `Fel vid order: ${error}` });
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateOrder = async () => {
    if (!selectedOrderId || !price) {
      setMessage({ type: 'error', text: 'Välj order och ange nytt pris' });
      return;
    }

    setLoading(true);
    const success = await updateOrder(parseInt(selectedOrderId), {
      price: parseFloat(price)
    });

    if (success) {
      setMessage({ type: 'success', text: `Order ${selectedOrderId} uppdaterad` });
    } else {
      setMessage({ type: 'error', text: 'Kunde inte uppdatera order' });
    }
    setLoading(false);
  };

  const handleCancelOrder = async (orderId: string) => {
    setLoading(true);
    const success = await cancelOrder(parseInt(orderId));
    
    if (success) {
      setMessage({ type: 'success', text: `Order ${orderId} avbruten` });
    } else {
      setMessage({ type: 'error', text: 'Kunde inte avbryta order' });
    }
    setLoading(false);
  };

  const handleCancelAllOrders = async () => {
    if (!window.confirm('Är du säker på att du vill avbryta ALLA aktiva ordrar?')) {
      return;
    }

    setLoading(true);
    const success = await cancelAllOrders();
    
    if (success) {
      setMessage({ type: 'success', text: 'Alla ordrar avbrutna' });
    } else {
      setMessage({ type: 'error', text: 'Kunde inte avbryta alla ordrar' });
    }
    setLoading(false);
  };

  const handleNewFundingOffer = async () => {
    if (!fundingAmount || !fundingRate || !fundingSymbol) {
      setMessage({ type: 'error', text: 'Alla funding-fält krävs' });
      return;
    }

    setLoading(true);
    const success = await newFundingOffer({
      type: 'LIMIT',
      symbol: fundingSymbol,
      amount: parseFloat(fundingAmount),
      rate: parseFloat(fundingRate) / 365, // Convert annual rate to daily
      period: parseInt(fundingPeriod),
      flags: 0
    });

    if (success) {
      setMessage({ type: 'success', text: `Funding offer skickad: ${fundingAmount} ${fundingSymbol}` });
      setFundingAmount('');
      setFundingRate('');
    } else {
      setMessage({ type: 'error', text: 'Kunde inte skicka funding offer' });
    }
    setLoading(false);
  };

  const handleCalcRequest = async () => {
    setLoading(true);
    const success = await calcRequest({});
    
    if (success) {
      setMessage({ type: 'success', text: 'Margin-beräkning begärd' });
    } else {
      setMessage({ type: 'error', text: 'Kunde inte begära beräkning' });
    }
    setLoading(false);
  };

  const activeOrders = getActiveOrders();
  const currentTicker = tickers[symbol];
  const totalBalance = getTotalBalance();
  const marginRequired = getMarginRequirement();
  const tradableBalance = getTradableBalance();

  if (!authenticated) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5" />
            WebSocket Trading
          </CardTitle>
          <CardDescription>
            Autentisera dig först för att använda live trading
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Alert>
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              Du måste vara inloggad för att använda trading-funktioner
            </AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Zap className="h-5 w-5 text-blue-500" />
          WebSocket Live Trading
        </CardTitle>
        <CardDescription>
          Direkt trading via Bitfinex WebSocket WS Input Commands
        </CardDescription>
        
        {/* Account Summary */}
        <div className="flex gap-4 text-sm">
          <div className="flex items-center gap-1">
            <DollarSign className="h-3 w-3" />
            Total: ${totalBalance.toFixed(2)}
          </div>
          <div className="flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            Tradable: ${tradableBalance.toFixed(2)}
          </div>
          <div className="flex items-center gap-1">
            <AlertTriangle className="h-3 w-3" />
            Margin: ${marginRequired.toFixed(2)}
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {message && (
          <Alert className={`mb-4 ${message.type === 'success' ? 'border-green-500' : 'border-red-500'}`}>
            {message.type === 'success' ? (
              <CheckCircle className="h-4 w-4 text-green-500" />
            ) : (
              <AlertTriangle className="h-4 w-4 text-red-500" />
            )}
            <AlertDescription className={message.type === 'success' ? 'text-green-700' : 'text-red-700'}>
              {message.text}
            </AlertDescription>
          </Alert>
        )}

        <Tabs defaultValue="trade" className="w-full">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="trade">Ny Order</TabsTrigger>
            <TabsTrigger value="manage">Hantera</TabsTrigger>
            <TabsTrigger value="funding">Funding</TabsTrigger>
            <TabsTrigger value="orders">Ordrar ({activeOrders.length})</TabsTrigger>
          </TabsList>

          {/* New Order Tab */}
          <TabsContent value="trade" className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="symbol">Symbol</Label>
                <Select value={symbol} onValueChange={setSymbol}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="tBTCUSD">BTC/USD</SelectItem>
                    <SelectItem value="tETHUSD">ETH/USD</SelectItem>
                    <SelectItem value="tLTCUSD">LTC/USD</SelectItem>
                    <SelectItem value="tXRPUSD">XRP/USD</SelectItem>
                  </SelectContent>
                </Select>
                                 {currentTicker && (
                   <div className="text-xs text-gray-500">
                     Aktuellt pris: ${currentTicker.price.toFixed(2)}
                     {currentTicker.bid && currentTicker.ask && (
                       <span className="ml-2 text-gray-400">
                         Bid: ${currentTicker.bid.toFixed(2)} | Ask: ${currentTicker.ask.toFixed(2)}
                       </span>
                     )}
                   </div>
                 )}
              </div>

              <div className="space-y-2">
                <Label htmlFor="orderType">Order Type</Label>
                <Select value={orderType} onValueChange={setOrderType}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LIMIT">Limit</SelectItem>
                    <SelectItem value="MARKET">Market</SelectItem>
                    <SelectItem value="STOP">Stop</SelectItem>
                    <SelectItem value="TRAILING STOP">Trailing Stop</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="amount">Belopp</Label>
                <Input
                  id="amount"
                  type="number"
                  step="0.00001"
                  value={amount}
                  onChange={(e) => setAmount(e.target.value)}
                  placeholder="0.001"
                />
              </div>

              {orderType === 'LIMIT' && (
                <div className="space-y-2">
                  <Label htmlFor="price">Pris ($)</Label>
                  <Input
                    id="price"
                    type="number"
                    step="0.01"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    placeholder="0.00"
                  />
                </div>
              )}
            </div>

            <div className="flex gap-2">
              <Button
                variant={side === 'buy' ? 'default' : 'outline'}
                onClick={() => setSide('buy')}
                className="flex-1"
                disabled={loading}
              >
                <TrendingUp className="h-4 w-4 mr-2" />
                KÖP
              </Button>
              <Button
                variant={side === 'sell' ? 'destructive' : 'outline'}
                onClick={() => setSide('sell')}
                className="flex-1"
                disabled={loading}
              >
                <TrendingDown className="h-4 w-4 mr-2" />
                SÄLJ
              </Button>
            </div>

            <Button
              onClick={handleNewOrder}
              disabled={loading || !amount}
              className="w-full"
              size="lg"
            >
              {loading ? 'Skickar...' : `Skicka ${side.toUpperCase()} Order`}
            </Button>
          </TabsContent>

          {/* Order Management Tab */}
          <TabsContent value="manage" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="selectOrder">Välj Order att Uppdatera</Label>
              <Select value={selectedOrderId} onValueChange={setSelectedOrderId}>
                <SelectTrigger>
                  <SelectValue placeholder="Välj order..." />
                </SelectTrigger>
                <SelectContent>
                  {activeOrders.map((order) => (
                    <SelectItem key={order.id} value={order.id}>
                      {order.symbol} - {order.amount} @ ${order.price}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="newPrice">Nytt Pris</Label>
              <Input
                id="newPrice"
                type="number"
                step="0.01"
                value={price}
                onChange={(e) => setPrice(e.target.value)}
                placeholder="Nytt pris..."
              />
            </div>

            <div className="flex gap-2">
              <Button
                onClick={handleUpdateOrder}
                disabled={loading || !selectedOrderId || !price}
                className="flex-1"
              >
                Uppdatera Order
              </Button>
              <Button
                onClick={handleCalcRequest}
                disabled={loading}
                variant="outline"
                className="flex-1"
              >
                Beräkna Margin
              </Button>
            </div>

            <Button
              onClick={handleCancelAllOrders}
              disabled={loading || activeOrders.length === 0}
              variant="destructive"
              className="w-full"
            >
              ⚠️ Avbryt ALLA Ordrar ({activeOrders.length})
            </Button>
          </TabsContent>

          {/* Funding Tab */}
          <TabsContent value="funding" className="space-y-4">
            <div className="text-sm text-blue-600 bg-blue-50 p-3 rounded">
              💡 Funding offers låter dig tjäna passiv inkomst genom att låna ut dina medel till andra traders
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="fundingSymbol">Valuta</Label>
                <Select value={fundingSymbol} onValueChange={setFundingSymbol}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="fUSD">USD</SelectItem>
                    <SelectItem value="fBTC">BTC</SelectItem>
                    <SelectItem value="fETH">ETH</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div className="space-y-2">
                <Label htmlFor="fundingPeriod">Period (dagar)</Label>
                <Select value={fundingPeriod} onValueChange={setFundingPeriod}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="2">2 dagar</SelectItem>
                    <SelectItem value="7">7 dagar</SelectItem>
                    <SelectItem value="30">30 dagar</SelectItem>
                    <SelectItem value="120">120 dagar</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="fundingAmount">Belopp</Label>
                <Input
                  id="fundingAmount"
                  type="number"
                  step="0.01"
                  value={fundingAmount}
                  onChange={(e) => setFundingAmount(e.target.value)}
                  placeholder="100.00"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="fundingRate">Årlig Ränta (%)</Label>
                <Input
                  id="fundingRate"
                  type="number"
                  step="0.001"
                  value={fundingRate}
                  onChange={(e) => setFundingRate(e.target.value)}
                  placeholder="5.0"
                />
              </div>
            </div>

            <Button
              onClick={handleNewFundingOffer}
              disabled={loading || !fundingAmount || !fundingRate}
              className="w-full"
            >
              {loading ? 'Skickar...' : 'Skapa Funding Offer'}
            </Button>

            {/* Active Funding Offers */}
            {fundingInfo.offers.length > 0 && (
              <div className="space-y-2">
                <Label>Aktiva Funding Offers</Label>
                {fundingInfo.offers.map((offer) => (
                  <div key={offer.id} className="flex justify-between items-center p-2 border rounded">
                    <span>{offer.amount} {offer.symbol} @ {(offer.rate * 365 * 100).toFixed(3)}%</span>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => cancelFundingOffer(offer.id)}
                      disabled={loading}
                    >
                      Avbryt
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>

          {/* Active Orders Tab */}
          <TabsContent value="orders" className="space-y-4">
            {activeOrders.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                Inga aktiva ordrar
              </div>
            ) : (
              <div className="space-y-2">
                {activeOrders.map((order) => (
                  <div key={order.id} className="flex justify-between items-center p-3 border rounded">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Badge variant={order.amount > 0 ? "default" : "destructive"}>
                          {order.amount > 0 ? 'BUY' : 'SELL'}
                        </Badge>
                        <span className="font-medium">{order.symbol}</span>
                        <span>{Math.abs(order.amount)} @ ${order.price}</span>
                      </div>
                      <div className="text-xs text-gray-500">
                        Status: {order.status} | ID: {order.id}
                      </div>
                    </div>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleCancelOrder(order.id)}
                      disabled={loading}
                    >
                      Avbryt
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
};