import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { useWebSocketAccount } from '@/contexts/WebSocketAccountProvider';
import { 
  Wifi, 
  WifiOff, 
  Shield, 
  ShieldCheck, 
  Loader2, 
  Eye, 
  EyeOff,
  DollarSign,
  TrendingUp,
  Activity,
  RefreshCw
} from 'lucide-react';

/**
 * AccountStatus Component
 * 
 * Visar real-time account status från Bitfinex WebSocket
 * Hanterar authentication och connection status
 */
export const AccountStatus: React.FC = () => {
  const {
    connected,
    connecting,
    authenticated,
    authenticating,
    error,
    lastHeartbeat,
    orders,
    balances,
    positions,
    trades,
    marginInfo,
    authenticate,
    disconnect,
    getActiveOrders,
    getTotalBalance,
    getMarginRequirement,
    getTradableBalance
  } = useWebSocketAccount();

  // Local state för authentication form
  const [apiKey, setApiKey] = useState('');
  const [apiSecret, setApiSecret] = useState('');
  const [showSecret, setShowSecret] = useState(false);
  const [showForm, setShowForm] = useState(false);

  // Handle authentication
  const handleAuthenticate = () => {
    if (!apiKey.trim() || !apiSecret.trim()) {
      return;
    }
    authenticate(apiKey.trim(), apiSecret.trim());
  };

  // Handle disconnect
  const handleDisconnect = () => {
    disconnect();
    setApiKey('');
    setApiSecret('');
    setShowForm(false);
  };

  // Connection status
  const connectionStatus = () => {
    if (connecting) return { icon: Loader2, text: 'Ansluter...', color: 'bg-yellow-500' };
    if (connected && authenticated) return { icon: Wifi, text: 'Ansluten & Autentiserad', color: 'bg-green-500' };
    if (connected) return { icon: Shield, text: 'Ansluten (Ej autentiserad)', color: 'bg-blue-500' };
    return { icon: WifiOff, text: 'Frånkopplad', color: 'bg-red-500' };
  };

  const status = connectionStatus();

  // Active orders count
  const activeOrders = getActiveOrders();
  const totalBalance = getTotalBalance();

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Account Status
          </span>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${status.color} animate-pulse`} />
            <Badge variant="outline" className="text-xs">
              <status.icon className="w-3 h-3 mr-1" />
              {status.text}
            </Badge>
          </div>
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Error Display */}
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Connection Statistics */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Senaste Heartbeat</Label>
            <div className="text-sm font-mono">
              {lastHeartbeat ? new Date(lastHeartbeat).toLocaleTimeString() : 'N/A'}
            </div>
          </div>
          <div className="space-y-1">
            <Label className="text-xs text-muted-foreground">Data Status</Label>
            <div className="text-sm">
              {authenticated ? `${orders.length} orders, ${balances.length} balances` : 'Ingen data'}
            </div>
          </div>
        </div>

        {/* Account Summary (only if authenticated) */}
        {authenticated && (
          <>
            <div className="grid grid-cols-3 gap-4 p-4 bg-muted/50 rounded-lg">
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">{activeOrders.length}</div>
                <div className="text-xs text-muted-foreground">Aktiva Orders</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{positions.length}</div>
                <div className="text-xs text-muted-foreground">Positioner</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  ${totalBalance.toFixed(2)}
                </div>
                <div className="text-xs text-muted-foreground">Total Balance</div>
              </div>
            </div>

            {/* Margin Info Summary */}
            {marginInfo.base && (
              <div className="grid grid-cols-2 gap-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <div className="space-y-1">
                  <Label className="text-xs text-blue-600 font-medium">Margin Required</Label>
                  <div className="text-lg font-bold text-blue-800">
                    ${getMarginRequirement().toFixed(2)}
                  </div>
                  <div className="text-xs text-blue-600">
                    Net: ${marginInfo.base.marginNet.toFixed(2)}
                  </div>
                </div>
                <div className="space-y-1">
                  <Label className="text-xs text-blue-600 font-medium">P&L</Label>
                  <div className={`text-lg font-bold ${marginInfo.base.userPL >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                    ${marginInfo.base.userPL.toFixed(2)}
                  </div>
                  <div className="text-xs text-blue-600">
                    Tradable: ${getTradableBalance().toFixed(2)}
                  </div>
                </div>
              </div>
            )}
          </>
        )}

        {/* Recent Activity */}
        {authenticated && trades.length > 0 && (
          <div className="space-y-2">
            <Label className="text-sm font-medium">Senaste Trades</Label>
            <div className="space-y-1 max-h-32 overflow-y-auto">
              {trades.slice(0, 3).map((trade) => (
                <div key={trade.id} className="flex justify-between items-center p-2 bg-muted/30 rounded text-xs">
                  <span className="font-mono">{trade.symbol}</span>
                  <span className={trade.side === 'buy' ? 'text-green-600' : 'text-red-600'}>
                    {trade.side.toUpperCase()} {trade.amount}
                  </span>
                  <span className="text-muted-foreground">
                    ${trade.entry_price.toFixed(2)}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Authentication Controls */}
        <div className="space-y-3 pt-4 border-t">
          {!authenticated ? (
            <>
              <div className="flex justify-between items-center">
                <Label className="text-sm font-medium">Bitfinex API Authentication</Label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowForm(!showForm)}
                >
                  {showForm ? 'Dölj' : 'Visa'} Form
                </Button>
              </div>

              {showForm && (
                <div className="space-y-3 p-4 border rounded-lg bg-muted/20">
                  <div className="space-y-2">
                    <Label htmlFor="apiKey" className="text-xs">API Key</Label>
                    <Input
                      id="apiKey"
                      type="text"
                      placeholder="Din Bitfinex API Key"
                      value={apiKey}
                      onChange={(e) => setApiKey(e.target.value)}
                      className="text-xs font-mono"
                    />
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="apiSecret" className="text-xs">API Secret</Label>
                    <div className="relative">
                      <Input
                        id="apiSecret"
                        type={showSecret ? "text" : "password"}
                        placeholder="Din Bitfinex API Secret"
                        value={apiSecret}
                        onChange={(e) => setApiSecret(e.target.value)}
                        className="text-xs font-mono pr-8"
                      />
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        className="absolute right-0 top-0 h-full px-2"
                        onClick={() => setShowSecret(!showSecret)}
                      >
                        {showSecret ? <EyeOff className="w-3 h-3" /> : <Eye className="w-3 h-3" />}
                      </Button>
                    </div>
                  </div>

                  <div className="flex gap-2">
                    <Button
                      onClick={handleAuthenticate}
                      disabled={!apiKey.trim() || !apiSecret.trim() || authenticating || !connected}
                      className="flex-1"
                      size="sm"
                    >
                      {authenticating ? (
                        <>
                          <Loader2 className="w-3 h-3 mr-2 animate-spin" />
                          Autentiserar...
                        </>
                      ) : (
                        <>
                          <ShieldCheck className="w-3 h-3 mr-2" />
                          Autentisera
                        </>
                      )}
                    </Button>
                  </div>

                  <Alert>
                    <AlertDescription className="text-xs">
                      <strong>Säkerhet:</strong> API-nycklar lagras endast temporärt i minnet och skickas direkt till Bitfinex. 
                      Se till att dina API-nycklar har begränsade permissions (endast läs + trading).
                    </AlertDescription>
                  </Alert>
                </div>
              )}
            </>
          ) : (
            <div className="flex justify-between items-center p-3 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2">
                <ShieldCheck className="w-4 h-4 text-green-600" />
                <span className="text-sm text-green-800">Autentiserad & Aktiv</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={handleDisconnect}
                className="border-red-200 text-red-600 hover:bg-red-50"
              >
                <RefreshCw className="w-3 h-3 mr-1" />
                Koppla från
              </Button>
            </div>
          )}
        </div>

        {/* Connection Help */}
        {!connected && (
          <Alert>
            <AlertDescription className="text-xs">
              <strong>Obs:</strong> WebSocket-anslutning krävs för real-time data. 
              Anslutning sker automatiskt. För authentication behövs Bitfinex API-nycklar.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};