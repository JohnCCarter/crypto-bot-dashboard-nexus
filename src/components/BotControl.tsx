import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useToast } from '@/hooks/use-toast';
import { api } from '@/lib/api';
import { BotStatus } from '@/types/trading';
import { logger } from '@/utils/logger';
import { useState } from 'react';

interface BotControlProps {
  status: BotStatus;
  onStatusChange: () => void;
}

export function BotControl({ status, onStatusChange }: BotControlProps) {
  const [isLoading, setIsLoading] = useState(false);
  const { toast } = useToast();

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

  const handleToggleBot = async () => {
    const action = status.status === 'running' ? 'stop' : 'start';
    
    console.log(`🤖 [BotControl] User clicked ${action.toUpperCase()} button`);
    console.log(`🤖 [BotControl] Current bot status: ${status.status}`);
    console.log(`🤖 [BotControl] Bot uptime: ${status.uptime}s`);
    console.log(`🤖 [BotControl] Timestamp: ${new Date().toISOString()}`);
    
    setIsLoading(true);
    
    try {
      console.log(`🤖 [BotControl] Sending ${action} request to API...`);
      
      const response = status.status === 'running' 
        ? await api.stopBot()
        : await api.startBot();
      
      console.log(`🤖 [BotControl] API Response received:`, response);
      
      if (response.success) {
        console.log(`✅ [BotControl] Bot ${action} operation successful!`);
        console.log(`✅ [BotControl] Server message: ${response.message}`);
        
        // Log bot status change using trading logger
        if (action === 'start') {
          logger.botActivated();
        } else {
          logger.botDeactivated();
        }
        
        toast({
          title: "Success",
          description: response.message,
        });
        
        console.log(`🤖 [BotControl] Triggering status refresh...`);
        onStatusChange();
      } else {
        console.error(`❌ [BotControl] Bot ${action} failed - response.success = false`);
        console.error(`❌ [BotControl] Server message: ${response.message || 'No message provided'}`);
        
        logger.botError(action, response.message);
        throw new Error(response.message);
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      
      console.error(`❌ [BotControl] Bot ${action} operation failed!`);
      console.error(`❌ [BotControl] Error:`, error);
      console.error(`❌ [BotControl] Error type: ${error instanceof Error ? error.constructor.name : typeof error}`);
      console.error(`❌ [BotControl] Error message: ${errorMessage}`);
      console.error(`❌ [BotControl] Stack trace:`, error instanceof Error ? error.stack : 'No stack trace');
      
      logger.botError(action, errorMessage);
      
      toast({
        title: "Bot Control Error",
        description: `Failed to toggle bot status: ${errorMessage}`,
        variant: "destructive",
      });
    } finally {
      console.log(`🤖 [BotControl] Bot ${action} operation completed (loading=false)`);
      setIsLoading(false);
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
          onClick={handleToggleBot}
          disabled={isLoading}
          className={`w-full ${
            status.status === 'running' 
              ? 'bg-red-600 hover:bg-red-700' 
              : 'bg-green-600 hover:bg-green-700'
          }`}
        >
          {isLoading ? 'Processing...' : status.status === 'running' ? 'Stop Bot' : 'Start Bot'}
        </Button>
      </CardContent>
    </Card>
  );
}
