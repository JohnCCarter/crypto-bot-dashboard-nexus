/**
 * Production Logger - Minimize console spam
 */

// Check if we're in production or development
const isDevelopment = process.env.NODE_ENV === 'development';
const isProduction = process.env.NODE_ENV === 'production';

// Logger configuration
const LOG_CONFIG = {
  enableConsoleLogging: isDevelopment,
  enableErrorLogging: true, // Always log errors
  enableWarningLogging: isDevelopment,
  enableInfoLogging: false, // Disable info in production
  enableDebugLogging: isDevelopment,
};

// Rate limiting for error logs
const ERROR_LOG_CACHE = new Map<string, number>();
const ERROR_LOG_COOLDOWN = 30000; // 30 seconds

class ProductionLogger {
  static log(...args: unknown[]) {
    if (LOG_CONFIG.enableConsoleLogging) {
      console.log(...args);
    }
  }

  static info(...args: unknown[]) {
    if (LOG_CONFIG.enableInfoLogging) {
      console.info(...args);
    }
  }

  static warn(...args: unknown[]) {
    if (LOG_CONFIG.enableWarningLogging) {
      console.warn(...args);
    }
  }

  static error(...args: unknown[]) {
    if (!LOG_CONFIG.enableErrorLogging) return;

    // Rate limiting for errors
    const errorKey = args.join(' ');
    const now = Date.now();
    const lastLogged = ERROR_LOG_CACHE.get(errorKey) || 0;

    if (now - lastLogged > ERROR_LOG_COOLDOWN) {
      console.error(...args);
      ERROR_LOG_CACHE.set(errorKey, now);
    }
  }

  static debug(...args: unknown[]) {
    if (LOG_CONFIG.enableDebugLogging) {
      console.debug(...args);
    }
  }

  static group(label: string) {
    if (LOG_CONFIG.enableConsoleLogging) {
      console.group(label);
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

  // Suppress all React development warnings in production
  static suppressReactWarnings() {
    if (isProduction) {
      // Override console.warn to filter React warnings
      const originalWarn = console.warn;
      console.warn = (...args) => {
        const message = args.join(' ');
        
        // Filter out common React warnings that spam the console
        const suppressedWarnings = [
          'Warning: Maximum update depth exceeded',
          'Warning: Can\'t perform a React state update',
          'Warning: Each child in a list should have a unique "key" prop',
          'Warning: Failed prop type',
          'Warning: componentWillReceiveProps has been renamed',
          'Warning: componentWillMount has been renamed',
          'Warning: componentWillUpdate has been renamed'
        ];

        const shouldSuppress = suppressedWarnings.some(warning => 
          message.includes(warning)
        );

        if (!shouldSuppress) {
          originalWarn(...args);
        }
      };
    }
  }
}

// Auto-suppress React warnings in production
ProductionLogger.suppressReactWarnings();

export { ProductionLogger as logger };
export default ProductionLogger;