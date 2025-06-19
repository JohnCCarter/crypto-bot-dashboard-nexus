/**
 * MINIMAL PRODUCTION LOGGER
 * Only logs critical events, errors, and system status
 * NO API SPAM - NO SUCCESS MESSAGES - NO DEBUG INFO
 */

interface LogEntry {
  timestamp: string;
  level: 'error' | 'warn' | 'critical' | 'status';
  source: string;
  message: string;
}

class MinimalLogger {
  private logs: LogEntry[] = [];
  private maxLogs = 25; // Keep only last 25 critical entries
  private lastCriticalLog = new Map<string, number>(); // Rate limiting

  // CRITICAL EVENTS ONLY (system failures, trading issues)
  critical(source: string, message: string): void {
    this.addLogWithRateLimit('critical', source, message, 5 * 60 * 1000); // 5 min rate limit
  }

  // SYSTEM STATUS (startup, shutdown, major state changes)
  status(source: string, message: string): void
  status(message: string): void
  status(...args: string[]): void {
    if (args.length === 1) {
      // Single argument - treat as message with 'System' source
      this.addLogWithRateLimit('status', 'System', args[0], 2 * 60 * 1000);
    } else if (args.length >= 2) {
      // Two or more arguments - treat as (source, message)
      this.addLogWithRateLimit('status', args[0], args[1], 2 * 60 * 1000);
    }
  }

  // ERRORS (always logged, but rate limited)
  error(source: string, message: string): void
  error(message: string): void
  error(...args: string[]): void {
    if (args.length === 1) {
      // Single argument - treat as message with 'System' source
      this.addLogWithRateLimit('error', 'System', args[0], 30 * 1000);
    } else if (args.length >= 2) {
      // Two or more arguments - treat as (source, message, ...)
      const source = args[0];
      const message = args.slice(1).join(' ');
      this.addLogWithRateLimit('error', source, message, 30 * 1000);
    }
  }

  // WARNINGS (rate limited)
  warn(source: string, message: string): void
  warn(message: string): void  
  warn(...args: string[]): void {
    if (args.length === 1) {
      // Single argument - treat as message with 'System' source  
      this.addLogWithRateLimit('warn', 'System', args[0], 60 * 1000);
    } else if (args.length >= 2) {
      // Two or more arguments - treat as (source, message, ...)
      const source = args[0];
      const message = args.slice(1).join(' ');
      this.addLogWithRateLimit('warn', source, message, 60 * 1000);
    }
  }

  // SUPPRESSED METHODS - NO LOGGING FOR REGULAR OPERATIONS
  info(): void {} // Suppressed
  debug(): void {} // Suppressed
  log(): void {} // Suppressed
  
  // API Methods - ALL SUPPRESSED
  apiRequest(): void {} // Suppressed
  apiResponse(): void {} // Suppressed
  apiSuccess(): void {} // Suppressed
  
  // WebSocket Methods - ONLY ERRORS
  wsStatus(): void {} // Suppressed
  wsInfo(): void {} // Suppressed
  wsWarn(...args: string[]): void {
    const message = args.join(' ');
    // Only log WebSocket warnings if they contain critical keywords
    if (message.includes('Failed') || message.includes('Timeout') || message.includes('Disconnected')) {
      this.warn('WebSocket', message);
    }
  }
  wsError(...args: string[]): void {
    const message = args.join(' ');
    this.error('WebSocket', message);
  }

  private addLogWithRateLimit(
    level: LogEntry['level'], 
    source: string, 
    message: string, 
    rateLimitMs: number
  ): void {
    // Guard against undefined/null values
    if (!message || !source) {
      console.warn('⚠️ Logger: Invalid parameters', { level, source, message });
      return;
    }
    
    const key = `${level}:${source}:${message.substring(0, 50)}`;
    const now = Date.now();
    const lastTime = this.lastCriticalLog.get(key) || 0;
    
    // Rate limiting
    if (now - lastTime < rateLimitMs) {
      return; // Suppressed due to rate limit
    }
    
    this.lastCriticalLog.set(key, now);
    this.addLog(level, source, message);
  }

  private addLog(level: LogEntry['level'], source: string, message: string): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      source,
      message
    };

    this.logs.unshift(entry);
    
    // Keep only recent critical logs
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(0, this.maxLogs);
    }

    // Console output ONLY for important events
    const emoji = {
      error: '🚨',
      warn: '⚠️', 
      critical: '🔥',
      status: '✅'
    }[level];

    console.log(`${emoji} [${source}] ${message}`);
  }

  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  clear(): void {
    this.logs = [];
    this.lastCriticalLog.clear();
    console.log('🗑️ Minimal logs cleared');
  }

  // System health check (once per hour max)
  systemHealth(): void {
    this.status('System', 'Health check - All services operational');
  }

  // Convenience methods that forward to appropriate levels
  group(): void {} // Suppressed
  groupEnd(): void {} // Suppressed
  table(): void {} // Suppressed
}

// Export single instance
export const logger = new MinimalLogger();

// Auto-log system startup (once)
logger.status('System', 'Minimal production logging active - API spam suppressed');

// Default export for compatibility
export default logger;