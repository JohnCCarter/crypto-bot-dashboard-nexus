import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { AlertCircle, CheckCircle, Info, XCircle, Trash2, Download } from 'lucide-react';
import { LogEntry } from '@/types/trading';

// Internal log entry interface for frontend logs
interface FrontendLogEntry {
  timestamp: string;
  level: 'info' | 'error' | 'warning' | 'debug';
  source: string;
  message: string;
}

interface LogViewerProps {
  logs: LogEntry[];
  isLoading?: boolean;
  className?: string;
}

export const LogViewer: React.FC<LogViewerProps> = ({ logs: propLogs, isLoading = false, className }) => {
  const [frontendLogs, setFrontendLogs] = useState<FrontendLogEntry[]>([]);
  const [filter, setFilter] = useState<string>('all');
  const [maxLogs] = useState(1000);

  // Intercept console methods för att fånga frontend logs
  useEffect(() => {
    const originalConsole = {
      log: console.log,
      error: console.error,
      warn: console.warn,
      info: console.info
    };

    const addLog = (level: 'info' | 'error' | 'warning' | 'debug', args: any[]) => {
      const message = args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg, null, 2) : String(arg)
      ).join(' ');

      const logEntry: FrontendLogEntry = {
        timestamp: new Date().toISOString(),
        level,
        source: 'Frontend',
        message
      };

      setFrontendLogs(prev => {
        const updated = [logEntry, ...prev];
        return updated.slice(0, maxLogs);
      });
    };

    // Override console methods
    console.log = (...args) => {
      originalConsole.log(...args);
      addLog('info', args);
    };

    console.error = (...args) => {
      originalConsole.error(...args);
      addLog('error', args);
    };

    console.warn = (...args) => {
      originalConsole.warn(...args);
      addLog('warning', args);
    };

    console.info = (...args) => {
      originalConsole.info(...args);
      addLog('info', args);
    };

    // Cleanup på unmount
    return () => {
      console.log = originalConsole.log;
      console.error = originalConsole.error;
      console.warn = originalConsole.warn;
      console.info = originalConsole.info;
    };
  }, [maxLogs]);

  // Kombinera backend logs med frontend logs - normalisera structure
  const normalizedPropLogs: FrontendLogEntry[] = propLogs.map(log => ({
    timestamp: log.timestamp,
    level: log.level,
    source: 'Backend',
    message: log.message
  }));

  const allLogs = [...normalizedPropLogs, ...frontendLogs].sort((a, b) => 
    new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  const filteredLogs = allLogs.filter(log => {
    if (filter === 'all') return true;
    if (filter === 'errors') return log.level === 'error';
    if (filter === 'warnings') return log.level === 'warning';
    if (filter === 'bot') return log.message.includes('[BotControl]') || log.message.includes('[Backend]');
    if (filter === 'trading') return log.message.includes('[ManualTrade]') || log.message.includes('Order');
    if (filter === 'settings') return log.message.includes('[Settings]');
    return true;
  });

  const getLogIcon = (level: string) => {
    switch (level) {
      case 'error': return <XCircle className="w-4 h-4 text-red-500" />;
      case 'warning': return <AlertCircle className="w-4 h-4 text-yellow-500" />;
      case 'info': return <Info className="w-4 h-4 text-blue-500" />;
      case 'debug': return <CheckCircle className="w-4 h-4 text-green-500" />;
      default: return <Info className="w-4 h-4 text-gray-500" />;
    }
  };

  const getLevelBadgeColor = (level: string) => {
    switch (level) {
      case 'error': return 'bg-red-100 text-red-800 border-red-200';
      case 'warning': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'info': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'debug': return 'bg-green-100 text-green-800 border-green-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const clearLogs = () => {
    setFrontendLogs([]);
    console.info('🗑️ Frontend log viewer cleared by user');
  };

  const exportLogs = () => {
    const logsData = filteredLogs.map(log => ({
      timestamp: log.timestamp,
      level: log.level,
      source: log.source,
      message: log.message
    }));

    const blob = new Blob([JSON.stringify(logsData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `trading-bot-logs-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    console.info(`📥 Exported ${filteredLogs.length} log entries`);
  };

  if (isLoading) {
    return (
      <Card className={`bg-card border-border ${className}`}>
        <CardHeader>
          <CardTitle className="text-sm font-medium">Enhanced Debug Logs</CardTitle>
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

  return (
    <Card className={`bg-card border-border ${className}`}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium">
            Enhanced Debug Logs ({filteredLogs.length})
          </CardTitle>
          <div className="flex items-center gap-2">
            <Select value={filter} onValueChange={setFilter}>
              <SelectTrigger className="w-32 h-8 text-xs">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Logs</SelectItem>
                <SelectItem value="errors">Errors Only</SelectItem>
                <SelectItem value="warnings">Warnings</SelectItem>
                <SelectItem value="bot">Bot Control</SelectItem>
                <SelectItem value="trading">Trading</SelectItem>
                <SelectItem value="settings">Settings</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="sm"
              onClick={exportLogs}
              disabled={filteredLogs.length === 0}
              className="h-8 px-2 text-xs"
            >
              <Download className="w-3 h-3 mr-1" />
              Export
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={clearLogs}
              className="h-8 px-2 text-xs"
            >
              <Trash2 className="w-3 h-3 mr-1" />
              Clear
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-2 max-h-96 overflow-y-auto">
          {filteredLogs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Info className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p className="text-sm">No logs to display. Use the bot to see debug information here.</p>
            </div>
          ) : (
            filteredLogs.map((log, index) => (
              <div
                key={index}
                className="flex items-start gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
              >
                <div className="flex-shrink-0 mt-0.5">
                  {getLogIcon(log.level)}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge className={`${getLevelBadgeColor(log.level)} text-xs`}>
                      {log.level.toUpperCase()}
                    </Badge>
                    <Badge variant="outline" className="text-xs">
                      {log.source}
                    </Badge>
                    <span className="text-xs text-muted-foreground">
                      {new Date(log.timestamp).toLocaleTimeString()}
                    </span>
                  </div>
                  <pre className="text-sm whitespace-pre-wrap break-all font-mono">
                    {log.message}
                  </pre>
                </div>
              </div>
            ))
          )}
        </div>
      </CardContent>
    </Card>
  );
};
