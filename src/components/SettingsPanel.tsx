
import { useState, useEffect, useCallback } from 'react';
import { TradingConfig } from '@/types/trading';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

interface SettingsPanelProps {
  isOpen: boolean;
  onClose: () => void;
}

export function SettingsPanel({ isOpen, onClose }: SettingsPanelProps) {
  const [config, setConfig] = useState<TradingConfig | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (isOpen) {
      loadConfig();
    }
  }, [isOpen, loadConfig]);

  const loadConfig = useCallback(async () => {
    setIsLoading(true);
    try {
      const configData = await api.getConfig();
      setConfig(configData);
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to load configuration",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  }, [toast]);

  const handleSave = async () => {
    if (!config) return;
    
    setIsSaving(true);
    try {
      const response = await api.updateConfig(config);
      if (response.success) {
        toast({
          title: "Success",
          description: response.message,
        });
        onClose();
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to save configuration",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  const updateConfig = <K extends keyof TradingConfig>(key: K, value: TradingConfig[K]) => {
    setConfig(prev => prev ? { ...prev, [key]: value } : null);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-4xl bg-card border-border max-h-[90vh]">
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Trading Bot Settings</CardTitle>
          <Button variant="ghost" onClick={onClose}>✕</Button>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center h-[400px]">
              <div className="animate-pulse text-muted-foreground">Loading configuration...</div>
            </div>
          ) : config ? (
            <Tabs defaultValue="strategy" className="w-full">
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="strategy">Strategy</TabsTrigger>
                <TabsTrigger value="risk">Risk Management</TabsTrigger>
                <TabsTrigger value="notifications">Notifications</TabsTrigger>
              </TabsList>
              
              <ScrollArea className="h-[500px] mt-4">
                <TabsContent value="strategy" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="symbol">Trading Symbol</Label>
                      <Select value={config.SYMBOL} onValueChange={(value) => updateConfig('SYMBOL', value)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="BTCUSD">BTCUSD</SelectItem>
                          <SelectItem value="ETHUSD">ETHUSD</SelectItem>
                          <SelectItem value="LTCUSD">LTCUSD</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="timeframe">Timeframe</Label>
                      <Select value={config.TIMEFRAME} onValueChange={(value) => updateConfig('TIMEFRAME', value)}>
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="1m">1 Minute</SelectItem>
                          <SelectItem value="5m">5 Minutes</SelectItem>
                          <SelectItem value="15m">15 Minutes</SelectItem>
                          <SelectItem value="1h">1 Hour</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div>
                      <Label htmlFor="ema_length">EMA Length</Label>
                      <Input
                        id="ema_length"
                        type="number"
                        value={config.EMA_LENGTH}
                        onChange={(e) => updateConfig('EMA_LENGTH', parseInt(e.target.value))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="ema_fast">EMA Fast</Label>
                      <Input
                        id="ema_fast"
                        type="number"
                        value={config.EMA_FAST}
                        onChange={(e) => updateConfig('EMA_FAST', parseInt(e.target.value))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="ema_slow">EMA Slow</Label>
                      <Input
                        id="ema_slow"
                        type="number"
                        value={config.EMA_SLOW}
                        onChange={(e) => updateConfig('EMA_SLOW', parseInt(e.target.value))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="rsi_period">RSI Period</Label>
                      <Input
                        id="rsi_period"
                        type="number"
                        value={config.RSI_PERIOD}
                        onChange={(e) => updateConfig('RSI_PERIOD', parseInt(e.target.value))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="atr_multiplier">ATR Multiplier</Label>
                      <Input
                        id="atr_multiplier"
                        type="number"
                        step="0.1"
                        value={config.ATR_MULTIPLIER}
                        onChange={(e) => updateConfig('ATR_MULTIPLIER', parseFloat(e.target.value))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="volume_multiplier">Volume Multiplier</Label>
                      <Input
                        id="volume_multiplier"
                        type="number"
                        step="0.1"
                        value={config.VOLUME_MULTIPLIER}
                        onChange={(e) => updateConfig('VOLUME_MULTIPLIER', parseFloat(e.target.value))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="lookback">Lookback Period</Label>
                      <Input
                        id="lookback"
                        type="number"
                        value={config.LOOKBACK}
                        onChange={(e) => updateConfig('LOOKBACK', parseInt(e.target.value))}
                      />
                    </div>
                  </div>
                </TabsContent>
                
                <TabsContent value="risk" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="trading_start">Trading Start Hour</Label>
                      <Input
                        id="trading_start"
                        type="number"
                        min="0"
                        max="23"
                        value={config.TRADING_START_HOUR}
                        onChange={(e) => updateConfig('TRADING_START_HOUR', parseInt(e.target.value))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="trading_end">Trading End Hour</Label>
                      <Input
                        id="trading_end"
                        type="number"
                        min="0"
                        max="23"
                        value={config.TRADING_END_HOUR}
                        onChange={(e) => updateConfig('TRADING_END_HOUR', parseInt(e.target.value))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="stop_loss">Stop Loss %</Label>
                      <Input
                        id="stop_loss"
                        type="number"
                        step="0.1"
                        value={config.STOP_LOSS_PERCENT}
                        onChange={(e) => updateConfig('STOP_LOSS_PERCENT', parseFloat(e.target.value))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="take_profit">Take Profit %</Label>
                      <Input
                        id="take_profit"
                        type="number"
                        step="0.1"
                        value={config.TAKE_PROFIT_PERCENT}
                        onChange={(e) => updateConfig('TAKE_PROFIT_PERCENT', parseFloat(e.target.value))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="max_trades">Max Trades Per Day</Label>
                      <Input
                        id="max_trades"
                        type="number"
                        value={config.MAX_TRADES_PER_DAY}
                        onChange={(e) => updateConfig('MAX_TRADES_PER_DAY', parseInt(e.target.value))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="max_loss">Max Daily Loss ($)</Label>
                      <Input
                        id="max_loss"
                        type="number"
                        value={config.MAX_DAILY_LOSS}
                        onChange={(e) => updateConfig('MAX_DAILY_LOSS', parseFloat(e.target.value))}
                      />
                    </div>
                    
                    <div>
                      <Label htmlFor="risk_per_trade">Risk Per Trade (%)</Label>
                      <Input
                        id="risk_per_trade"
                        type="number"
                        step="0.1"
                        value={config.RISK_PER_TRADE}
                        onChange={(e) => updateConfig('RISK_PER_TRADE', parseFloat(e.target.value))}
                      />
                    </div>
                  </div>
                </TabsContent>
                
                <TabsContent value="notifications" className="space-y-4">
                  <div className="space-y-4">
                    <div className="flex items-center space-x-2">
                      <Switch
                        checked={config.EMAIL_NOTIFICATIONS}
                        onCheckedChange={(checked) => updateConfig('EMAIL_NOTIFICATIONS', checked)}
                      />
                      <Label>Enable Email Notifications</Label>
                    </div>
                    
                    {config.EMAIL_NOTIFICATIONS && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <Label htmlFor="email_sender">Sender Email</Label>
                          <Input
                            id="email_sender"
                            type="email"
                            value={config.EMAIL_SENDER}
                            onChange={(e) => updateConfig('EMAIL_SENDER', e.target.value)}
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="email_receiver">Receiver Email</Label>
                          <Input
                            id="email_receiver"
                            type="email"
                            value={config.EMAIL_RECEIVER}
                            onChange={(e) => updateConfig('EMAIL_RECEIVER', e.target.value)}
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="smtp_server">SMTP Server</Label>
                          <Input
                            id="smtp_server"
                            value={config.EMAIL_SMTP_SERVER}
                            onChange={(e) => updateConfig('EMAIL_SMTP_SERVER', e.target.value)}
                          />
                        </div>
                        
                        <div>
                          <Label htmlFor="smtp_port">SMTP Port</Label>
                          <Input
                            id="smtp_port"
                            type="number"
                            value={config.EMAIL_SMTP_PORT}
                            onChange={(e) => updateConfig('EMAIL_SMTP_PORT', parseInt(e.target.value))}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </TabsContent>
              </ScrollArea>
              
              <div className="flex gap-2 mt-6">
                <Button onClick={handleSave} disabled={isSaving} className="flex-1">
                  {isSaving ? 'Saving...' : 'Save Configuration'}
                </Button>
                <Button variant="outline" onClick={onClose}>Cancel</Button>
              </div>
            </Tabs>
          ) : (
            <div className="text-center text-muted-foreground">Failed to load configuration</div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
