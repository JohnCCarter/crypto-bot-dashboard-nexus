
import { useState } from 'react';
import { BotStatus } from '@/types/trading';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { api } from '@/lib/api';
import { useToast } from '@/hooks/use-toast';

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
    setIsLoading(true);
    try {
      const response = status.status === 'running' 
        ? await api.stopBot()
        : await api.startBot();
      
      if (response.success) {
        toast({
          title: "Success",
          description: response.message,
        });
        onStatusChange();
      } else {
        throw new Error(response.message);
      }
    } catch (error) {
      toast({
        title: "Error",
        description: "Failed to toggle bot status",
        variant: "destructive",
      });
    } finally {
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
