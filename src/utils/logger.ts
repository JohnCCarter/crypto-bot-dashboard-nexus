/**
 * TRADING BOT MINIMAL LOGGER
 * Only logs trading operations and bot status changes
 * NO SYSTEM/API/WEBSOCKET SPAM
 */

interface LogEntry {
  timestamp: string;
  level: 'success' | 'error' | 'status';
  message: string;
}

class TradingLogger {
  private logs: LogEntry[] = [];
  private maxLogs = 10; // Keep only last 10 trading events

  // BOT STATUS CHANGES ONLY
  botActivated(): void {
    this.addLog('status', '✅ Bot aktiverad');
  }

  botDeactivated(): void {
    this.addLog('status', '❌ Bot avstängd');
  }

  // TRADING OPERATIONS ONLY
  buyApproved(symbol: string, amount: number, price?: number): void {
    const priceStr = price ? ` @ $${price}` : ' @ marknaspris';
    this.addLog('success', `💰 Köp godkänt: ${amount} ${symbol}${priceStr}`);
  }

  sellApproved(symbol: string, amount: number, price?: number): void {
    const priceStr = price ? ` @ $${price}` : ' @ marknaspris';
    this.addLog('success', `💰 Sälj godkänt: ${amount} ${symbol}${priceStr}`);
  }

  // ERRORS WHEN BOT FAILS
  botError(action: string, error: string): void {
    this.addLog('error', `🚨 Bot fel (${action}): ${error}`);
  }

  tradeError(operation: string, symbol: string, error: string): void {
    this.addLog('error', `🚨 Handel fel (${operation} ${symbol}): ${error}`);
  }

  // ALL OTHER METHODS - SUPPRESSED
  status(): void {} // Suppressed
  critical(): void {} // Suppressed
  error(): void {} // Suppressed  
  warn(): void {} // Suppressed
  info(): void {} // Suppressed
  debug(): void {} // Suppressed
  log(): void {} // Suppressed
  apiRequest(): void {} // Suppressed
  apiResponse(): void {} // Suppressed
  apiSuccess(): void {} // Suppressed
  wsStatus(): void {} // Suppressed
  wsInfo(): void {} // Suppressed
  wsWarn(): void {} // Suppressed
  wsError(): void {} // Suppressed
  group(): void {} // Suppressed
  groupEnd(): void {} // Suppressed
  table(): void {} // Suppressed
  systemHealth(): void {} // Suppressed

  private addLog(level: LogEntry['level'], message: string): void {
    const entry: LogEntry = {
      timestamp: new Date().toISOString(),
      level,
      message
    };

    this.logs.unshift(entry);
    
    // Keep only recent trading events
    if (this.logs.length > this.maxLogs) {
      this.logs = this.logs.slice(0, this.maxLogs);
    }

    // Console output ONLY for trading events
    console.log(message);
  }

  getLogs(): LogEntry[] {
    return [...this.logs];
  }

  clear(): void {
    this.logs = [];
    console.log('🗑️ Trading logs cleared');
  }
}

// Export single instance
export const logger = new TradingLogger();

// Default export for compatibility
export default logger;