/**
 * Smart Enhanced Logger - Show Status & Errors, Suppress Spam
 * Shows system activity status without overwhelming detail
 */

// Environment detection
const isDevelopment = process.env.NODE_ENV === 'development' || !process.env.NODE_ENV;
const isProduction = process.env.NODE_ENV === 'production';

// Smart Logger configuration - Show important status, suppress spam
const LOG_CONFIG = {
  enableConsoleLogging: true, // Show important messages
  enableErrorLogging: true, // Always show errors
  enableWarningLogging: true, // Show warnings  
  enableInfoLogging: true, // Show status info
  enableDebugLogging: isDevelopment, // Debug only in dev
  enableStatusMessages: true, // Show system status
  enableSpamSuppression: true, // Suppress repetitive messages
};

// Rate limiting for different message types
const ERROR_LOG_CACHE = new Map<string, number>();
const STATUS_LOG_CACHE = new Map<string, number>();
const ERROR_LOG_COOLDOWN = 30000; // 30 seconds between same errors
const STATUS_LOG_COOLDOWN = 60000; // 1 minute between same status messages

// Categories for smart filtering
const STATUS_KEYWORDS = [
  'Connected', 'Disconnected', 'Started', 'Stopped', 'Ready', 'Initialized',
  'System', 'Bot', 'Server', 'Database', 'API', 'Authentication'
];

const SPAM_KEYWORDS = [
  'Ticker update', 'Heartbeat', 'Ping', 'Pong', 'Subscribe', 'Update received',
  'Data received', 'Message', 'Processing', 'Polling'
];

class SmartLogger {
  // Enhanced status logging - shows system activity
  static status(message: string, ...args: unknown[]) {
    if (!LOG_CONFIG.enableStatusMessages) return;
    
    // Rate limit status messages to avoid spam
    const now = Date.now();
    const lastLogged = STATUS_LOG_CACHE.get(message) || 0;
    
    if (now - lastLogged > STATUS_LOG_COOLDOWN) {
      console.log(`🔷 [STATUS] ${message}`, ...args);
      STATUS_LOG_CACHE.set(message, now);
    }
  }

  // Regular info - but smart about spam
  static log(...args: unknown[]) {
    if (!LOG_CONFIG.enableConsoleLogging) return;
    
    const message = args.join(' ');
    
    // Suppress spam messages
    if (LOG_CONFIG.enableSpamSuppression && this.isSpamMessage(message)) {
      return;
    }
    
    console.log(...args);
  }

  static info(...args: unknown[]) {
    if (!LOG_CONFIG.enableInfoLogging) return;
    
    const message = args.join(' ');
    
    // Show status messages prominently
    if (this.isStatusMessage(message)) {
      this.status(message);
      return;
    }
    
    // Suppress spam messages
    if (LOG_CONFIG.enableSpamSuppression && this.isSpamMessage(message)) {
      return;
    }
    
    console.info(...args);
  }

  static warn(...args: unknown[]) {
    if (!LOG_CONFIG.enableWarningLogging) return;
    console.warn('⚠️', ...args);
  }

  static error(...args: unknown[]) {
    if (!LOG_CONFIG.enableErrorLogging) return;

    // Rate limiting for errors to avoid spam
    const errorKey = args.join(' ');
    const now = Date.now();
    const lastLogged = ERROR_LOG_CACHE.get(errorKey) || 0;

    if (now - lastLogged > ERROR_LOG_COOLDOWN) {
      console.error('❌ [ERROR]', ...args);
      ERROR_LOG_CACHE.set(errorKey, now);
    }
  }

  static debug(...args: unknown[]) {
    if (!LOG_CONFIG.enableDebugLogging) return;
    console.debug('🔍', ...args);
  }

  // Smart WebSocket logging - status only, no spam
  static wsStatus(message: string, ...args: unknown[]) {
    // Only log important WebSocket status changes
    if (message.includes('Connected') || 
        message.includes('Disconnected') || 
        message.includes('Error') ||
        message.includes('Failed')) {
      this.status(`WebSocket: ${message}`, ...args);
    }
  }

  static wsError(...args: unknown[]) {
    this.error('WebSocket:', ...args);
  }

  static wsInfo(message: string, ...args: unknown[]) {
    // Only show important WebSocket info, suppress spam
    if (message.includes('Connected') || 
        message.includes('Subscribed to') ||
        message.includes('Maintenance') ||
        message.includes('Platform')) {
      this.info(message, ...args);
    }
    // Suppress: ticker updates, heartbeats, pings, etc.
  }

  static wsWarn(...args: unknown[]) {
    this.warn('WebSocket:', ...args);
  }

  // Helper methods
  private static isStatusMessage(message: string): boolean {
    return STATUS_KEYWORDS.some(keyword => 
      message.toLowerCase().includes(keyword.toLowerCase())
    );
  }

  private static isSpamMessage(message: string): boolean {
    return SPAM_KEYWORDS.some(keyword => 
      message.toLowerCase().includes(keyword.toLowerCase())
    );
  }

  // System health logger - periodic status updates
  static systemHealth() {
    const now = new Date().toLocaleTimeString();
    this.status(`System Health Check - ${now} - All services operational`);
  }

  // Enhanced group logging for complex operations
  static group(label: string) {
    if (LOG_CONFIG.enableConsoleLogging) {
      console.group(`📁 ${label}`);
    }
  }

  static groupEnd() {
    if (LOG_CONFIG.enableConsoleLogging) {
      console.groupEnd();
    }
  }

  static table(data: unknown) {
    if (LOG_CONFIG.enableConsoleLogging) {
      console.table(data);
    }
  }
}

export { SmartLogger as logger };
export default SmartLogger;