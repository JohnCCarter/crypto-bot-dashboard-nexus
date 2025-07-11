import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { BotStatus } from '@/types/trading';
import { useState } from 'react';

interface BotControlProps {
  status: BotStatus;
  onStatusChange: () => void;
}

export function BotControl({ status, onStatusChange }: BotControlProps) {
  const [loading, setLoading] = useState(false);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-green-500';
      case 'stopped': return 'bg-gray-500';
      case 'error': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const formatUptime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const handleButtonClick = async (action: string) => {
    setLoading(true);
    try {
      console.log(`🤖 [BotControl] User clicked ${action.toUpperCase()} button`);
      console.log(`🤖 [BotControl] Current bot status: ${status.status}`);
      console.log(`🤖 [BotControl] Bot uptime: ${status.uptime}s`);
      console.log(`🤖 [BotControl] Timestamp: ${new Date().toISOString()}`);

      console.log(`🤖 [BotControl] Sending ${action} request to API...`);
      const response = await fetch(`/api/bot/${action}`, { method: 'POST' });
      const data = await response.json();

      console.log(`✅ [BotControl] API Response received:`, data);
      if (data.success) {
        console.log(`✅ [BotControl] Bot ${action} operation successful!`);
        console.log(`✅ [BotControl] Server message: ${data.message}`);
        onStatusChange();
      } else {
        console.error(`❌ [BotControl] Bot ${action} failed - response.success = false`);
        console.error(`❌ [BotControl] Server message: ${data.message || 'No message provided'}`);
      }
    } catch (error) {
      console.error(`❌ [BotControl] Bot ${action} operation failed!`);
      console.error(`❌ [BotControl] Error:`, error);
      console.error(`❌ [BotControl] Error type: ${error instanceof Error ? error.constructor.name : typeof error}`);
      console.error(`❌ [BotControl] Error message: ${error.message}`);
      console.error(`❌ [BotControl] Stack trace:`, error instanceof Error ? error.stack : 'No stack trace');
    } finally {
      setLoading(false);
      console.log(`🤖 [BotControl] Bot ${action} operation completed (loading=false)`);
    }
  };

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm font-medium">Bot Control</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${getStatusColor(status.status)}`}></div>
            <span className="font-medium capitalize">{status.status}</span>
          </div>
          <Badge variant="outline" className="text-xs">
            {status.status === 'running' ? formatUptime(status.uptime) : 'Offline'}
          </Badge>
        </div>
        
        <div className="text-xs text-muted-foreground">
          Last update: {new Date(status.last_update).toLocaleTimeString()}
        </div>
        
        <Button 
          onClick={() => handleButtonClick('start')}
          disabled={loading || status.status === 'running'}
          className={`w-full bg-green-600 hover:bg-green-700`}
        >
          {loading ? 'Processing...' : 'Start Bot'}
        </Button>
        <Button 
          onClick={() => handleButtonClick('stop')}
          disabled={loading || status.status === 'stopped'}
          className={`w-full bg-red-600 hover:bg-red-700`}
        >
          {loading ? 'Processing...' : 'Stop Bot'}
        </Button>
      </CardContent>
    </Card>
  );
}
