// Debug logging functions
export const initDebugLogging = (): void => {
  // Store original console methods
  const originalConsoleError = console.error;
  const originalConsoleWarn = console.warn;
  
  // Replace with versions that store logs
  console.error = (...args: any[]) => {
    // Call original function
    originalConsoleError.apply(console, args);
    
    // Store in localStorage (limiting to avoid overflow)
    const logs = JSON.parse(localStorage.getItem('debug_error_logs') || '[]');
    logs.push({
      timestamp: new Date().toISOString(),
      type: 'error',
      message: args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
      ).join(' ')
    });
    
    // Keep only the latest 50 logs
    if (logs.length > 50) logs.shift();
    
    localStorage.setItem('debug_error_logs', JSON.stringify(logs));
  };

  console.warn = (...args: any[]) => {
    originalConsoleWarn.apply(console, args);
    
    const logs = JSON.parse(localStorage.getItem('debug_warn_logs') || '[]');
    logs.push({
      timestamp: new Date().toISOString(),
      type: 'warn',
      message: args.map(arg => 
        typeof arg === 'object' ? JSON.stringify(arg) : String(arg)
      ).join(' ')
    });
    
    if (logs.length > 50) logs.shift();
    localStorage.setItem('debug_warn_logs', JSON.stringify(logs));
  };

  // Add utilities for retrieving logs
  window.debugUtils = {
    getLogs: () => {
      return {
        errors: JSON.parse(localStorage.getItem('debug_error_logs') || '[]'),
        warnings: JSON.parse(localStorage.getItem('debug_warn_logs') || '[]'),
        reactError: JSON.parse(localStorage.getItem('react_error') || 'null')
      };
    },
    clearLogs: () => {
      localStorage.removeItem('debug_error_logs');
      localStorage.removeItem('debug_warn_logs');
      localStorage.removeItem('react_error');
    }
  };

  console.log('Debug logging initialized!');
};

// Add debug types to the window object
declare global {
  interface Window {
    debugUtils: {
      getLogs: () => {
        errors: Array<{timestamp: string, type: string, message: string}>;
        warnings: Array<{timestamp: string, type: string, message: string}>;
        reactError: any;
      };
      clearLogs: () => void;
    };
  }
}
