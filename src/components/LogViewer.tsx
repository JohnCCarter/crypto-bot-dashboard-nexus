
import { LogEntry } from '@/types/trading';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';

interface LogViewerProps {
  logs: LogEntry[];
  isLoading?: boolean;
}

export function LogViewer({ logs, isLoading = false }: LogViewerProps) {
  if (isLoading) {
    return (
      <Card className="bg-card border-border">
        <CardHeader>
          <CardTitle className="text-sm font-medium">Bot Logs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="animate-pulse">
                <div className="h-4 bg-muted rounded w-3/4 mb-1"></div>
                <div className="h-3 bg-muted rounded w-full"></div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  }

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'error': return 'bg-red-500';
      case 'warning': return 'bg-yellow-500';
      case 'info': return 'bg-blue-500';
      case 'debug': return 'bg-gray-500';
      default: return 'bg-gray-500';
    }
  };

  return (
    <Card className="bg-card border-border">
      <CardHeader>
        <CardTitle className="text-sm font-medium">
          Bot Logs ({logs.length})
        </CardTitle>
      </CardHeader>
      <CardContent>
        <ScrollArea className="h-[400px]">
          {logs.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">No logs available</p>
          ) : (
            <div className="space-y-3">
              {logs.map((log, index) => (
                <div key={index} className="border-l-2 border-muted pl-3 py-1">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge className={`text-xs ${getLevelColor(log.level)}`}>
                      {log.level.toUpperCase()}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <p className="text-sm font-mono">{log.message}</p>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
