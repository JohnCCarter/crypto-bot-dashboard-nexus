import React, { useEffect, useState } from 'react';
import { useGlobalWebSocketMarket } from '../contexts/WebSocketMarketProvider';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './ui/card';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Separator } from './ui/separator';
import { CheckCircle, XCircle, Circle, DollarSign, TrendingUp, Clock } from 'lucide-react';

export const UserDataStreamDemo: React.FC = () => {
  const {
    userDataConnected,
    userDataError,
    userFills,
    liveOrders,
    liveBalances,
    subscribeToUserData,
    unsubscribeFromUserData
  } = useGlobalWebSocketMarket();

  const [connectionAttempted, setConnectionAttempted] = useState(false);

  // Auto-connect to user data on mount
  useEffect(() => {
    if (!connectionAttempted) {
      setConnectionAttempted(true);
      subscribeToUserData();
    }
  }, [subscribeToUserData, connectionAttempted]);

  const handleConnect = () => {
    subscribeToUserData();
  };

  const handleDisconnect = () => {
    unsubscribeFromUserData();
  };

  const formatTimestamp = (timestamp: number | undefined | null) => {
    if (
      typeof timestamp !== 'number' ||
      isNaN(timestamp) ||
      !isFinite(timestamp)
    ) {
      return '';
    }
    const date = new Date(timestamp);
    if (isNaN(date.getTime())) {
      return '';
    }
    return date.toLocaleTimeString();
  };

  const formatCurrency = (amount: number, precision = 4) => {
    return amount.toFixed(precision);
  };

  const getStatusIcon = (connected: boolean) => {
    if (connected) {
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    }
    return <XCircle className="h-4 w-4 text-red-500" />;
  };

  const getOrderStatusBadge = (status: string) => {
    const statusColors = {
      open: 'bg-blue-500',
      filled: 'bg-green-500',
      cancelled: 'bg-red-500',
      partial: 'bg-yellow-500'
    };
    
    return (
      <Badge className={`${statusColors[status as keyof typeof statusColors] || 'bg-gray-500'} text-white`}>
        {status}
      </Badge>
    );
  };

  return (
    <div className="space-y-6">
      {/* Connection Status Card */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            {getStatusIcon(userDataConnected)}
            User Data Streams
          </CardTitle>
          <CardDescription>
            Real-time order executions, live orders, and balance updates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium">Status:</span>
              <Badge variant={userDataConnected ? "default" : "destructive"}>
                {userDataConnected ? "Connected" : "Disconnected"}
              </Badge>
            </div>
            
            {userDataError && (
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-red-500">Error:</span>
                <span className="text-sm text-red-500">{userDataError}</span>
              </div>
            )}
          </div>
          
          <div className="flex gap-2 mt-4">
            <Button 
              onClick={handleConnect} 
              disabled={userDataConnected}
              size="sm"
            >
              Connect
            </Button>
            <Button 
              onClick={handleDisconnect} 
              disabled={!userDataConnected}
              variant="outline"
              size="sm"
            >
              Disconnect
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Live Balances */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            Live Balances
          </CardTitle>
          <CardDescription>
            Real-time balance updates ({Object.keys(liveBalances).length} currencies)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {Object.keys(liveBalances).length === 0 ? (
            <p className="text-sm text-muted-foreground">No balance data available</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(liveBalances).map(([currency, balance]) => (
                <div key={currency} className="flex items-center justify-between p-3 bg-muted rounded-lg">
                  <div>
                    <span className="font-medium">{currency}</span>
                    <span className="text-xs text-muted-foreground ml-2">
                      {formatTimestamp(balance.timestamp)}
                    </span>
                  </div>
                  <div className="text-right">
                    <div className="font-mono text-sm">
                      Available: {formatCurrency(balance.available)}
                    </div>
                    <div className="font-mono text-xs text-muted-foreground">
                      Total: {formatCurrency(balance.total)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Live Orders */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Live Orders
          </CardTitle>
          <CardDescription>
            Active orders with real-time status updates ({Object.keys(liveOrders).length} orders)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {Object.keys(liveOrders).length === 0 ? (
            <p className="text-sm text-muted-foreground">No active orders</p>
          ) : (
            <div className="space-y-3">
              {Object.entries(liveOrders).map(([orderId, order]) => (
                <div key={orderId} className="p-3 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{order.symbol}</span>
                      <Badge variant={order.side === 'buy' ? 'default' : 'destructive'}>
                        {order.side.toUpperCase()}
                      </Badge>
                      {getOrderStatusBadge(order.status)}
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatTimestamp(order.timestamp)}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Amount:</span>
                      <span className="ml-2 font-mono">{formatCurrency(order.amount)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Price:</span>
                      <span className="ml-2 font-mono">{formatCurrency(order.price)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Filled:</span>
                      <span className="ml-2 font-mono">{formatCurrency(order.filled)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Remaining:</span>
                      <span className="ml-2 font-mono">{formatCurrency(order.remaining)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Recent Fills */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Recent Order Fills
          </CardTitle>
          <CardDescription>
            Latest order executions ({userFills.length} fills)
          </CardDescription>
        </CardHeader>
        <CardContent>
          {userFills.length === 0 ? (
            <p className="text-sm text-muted-foreground">No recent fills</p>
          ) : (
            <div className="space-y-3">
              {userFills.slice(0, 10).map((fill, index) => (
                <div key={`${fill.id}-${index}`} className="p-3 border rounded-lg">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{fill.symbol}</span>
                      <Badge variant={fill.side === 'buy' ? 'default' : 'destructive'}>
                        {fill.side.toUpperCase()}
                      </Badge>
                    </div>
                    <span className="text-xs text-muted-foreground">
                      {formatTimestamp(fill.timestamp)}
                    </span>
                  </div>
                  
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div>
                      <span className="text-muted-foreground">Amount:</span>
                      <span className="ml-2 font-mono">{formatCurrency(fill.amount)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Price:</span>
                      <span className="ml-2 font-mono">{formatCurrency(fill.price)}</span>
                    </div>
                    <div>
                      <span className="text-muted-foreground">Fee:</span>
                      <span className="ml-2 font-mono">{formatCurrency(fill.fee)}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};