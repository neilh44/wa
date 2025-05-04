#!/bin/bash

# Script to fix the white screen issue in the WhatsApp Supabase frontend
echo "Starting WhatsApp Supabase frontend fix script..."

# Navigate to the frontend directory
cd whatsapp-supabase-frontend || { echo "Frontend directory not found!"; exit 1; }

# Step 1: Create necessary directories
echo "Creating necessary directories..."
mkdir -p src/components/debug
mkdir -p src/utils
mkdir -p src/pages

# Step 2: Backup existing files
echo "Backing up existing files..."
if [ -f src/index.tsx ]; then
  cp src/index.tsx src/index.tsx.backup
  echo "✅ Backed up index.tsx"
fi

if [ -f src/utils/debugLogging.ts ]; then
  cp src/utils/debugLogging.ts src/utils/debugLogging.ts.backup
  echo "✅ Backed up debugLogging.ts"
fi

# Step 3: Create ErrorBoundary.tsx
echo "Creating ErrorBoundary.tsx..."
cat > src/components/debug/ErrorBoundary.tsx << 'EOF'
import React, { Component, ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error, errorInfo: null };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({
      error,
      errorInfo
    });
    
    // Log error to console for debugging
    console.error('React Error Boundary caught an error:', error, errorInfo);
    
    // Send to a logging service or save to localStorage for debugging
    localStorage.setItem('react_error', JSON.stringify({
      message: error.message,
      stack: error.stack,
      componentStack: errorInfo.componentStack
    }));
  }

  render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div style={{ 
          padding: '20px', 
          margin: '20px', 
          border: '1px solid red',
          borderRadius: '5px',
          backgroundColor: '#fff0f0' 
        }}>
          <h2>Something went wrong.</h2>
          <details style={{ whiteSpace: 'pre-wrap' }}>
            <summary>Error Details</summary>
            <p>{this.state.error && this.state.error.toString()}</p>
            <p>Component Stack:</p>
            <pre>{this.state.errorInfo && this.state.errorInfo.componentStack}</pre>
          </details>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
EOF

# Step 4: Create debugLogging.ts
echo "Creating debugLogging.ts..."
cat > src/utils/debugLogging.ts << 'EOF'
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
EOF

# Step 5: Create Debug.tsx
echo "Creating Debug.tsx..."
cat > src/pages/Debug.tsx << 'EOF'
import React, { useEffect, useState } from 'react';
import { Box, Container, Typography, Paper, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';

interface LogEntry {
  timestamp: string;
  type: string;
  message: string;
}

interface DebugLogs {
  errors: LogEntry[];
  warnings: LogEntry[];
  reactError: any;
}

const Debug: React.FC = () => {
  const [logs, setLogs] = useState<DebugLogs>({
    errors: [],
    warnings: [],
    reactError: null
  });

  useEffect(() => {
    // Get logs from localStorage via the debug utils
    if (window.debugUtils) {
      setLogs(window.debugUtils.getLogs());
    } else {
      // Try to get raw logs if debugUtils isn't available
      try {
        const errors = JSON.parse(localStorage.getItem('debug_error_logs') || '[]');
        const warnings = JSON.parse(localStorage.getItem('debug_warn_logs') || '[]');
        const reactError = JSON.parse(localStorage.getItem('react_error') || 'null');
        setLogs({ errors, warnings, reactError });
      } catch (e) {
        console.error('Error loading logs:', e);
      }
    }
  }, []);

  const formatTime = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch (e) {
      return timestamp;
    }
  };

  return (
    <Container>
      <Typography variant="h4" component="h1" gutterBottom sx={{ mt: 4 }}>
        Debug Information
      </Typography>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          React Error
        </Typography>
        {logs.reactError ? (
          <Box sx={{ backgroundColor: '#fff0f0', p: 2, borderRadius: 1 }}>
            <Typography variant="body1" gutterBottom>
              <strong>Message:</strong> {logs.reactError.message}
            </Typography>
            <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
              <strong>Stack:</strong> 
              {logs.reactError.stack}
            </Typography>
            <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
              <strong>Component Stack:</strong> 
              {logs.reactError.componentStack}
            </Typography>
          </Box>
        ) : (
          <Typography>No React errors caught by the ErrorBoundary.</Typography>
        )}
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Console Errors ({logs.errors.length})
        </Typography>
        {logs.errors.length > 0 ? (
          logs.errors.map((error, index) => (
            <Accordion key={index}>
              <AccordionSummary>
                <Typography>
                  [{formatTime(error.timestamp)}] {error.message.substring(0, 60)}
                  {error.message.length > 60 ? '...' : ''}
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                  {error.message}
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))
        ) : (
          <Typography>No console errors recorded.</Typography>
        )}
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Console Warnings ({logs.warnings.length})
        </Typography>
        {logs.warnings.length > 0 ? (
          logs.warnings.map((warning, index) => (
            <Accordion key={index}>
              <AccordionSummary>
                <Typography>
                  [{formatTime(warning.timestamp)}] {warning.message.substring(0, 60)}
                  {warning.message.length > 60 ? '...' : ''}
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                  {warning.message}
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))
        ) : (
          <Typography>No console warnings recorded.</Typography>
        )}
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Environment Variables
        </Typography>
        <Typography><strong>NODE_ENV:</strong> {process.env.NODE_ENV}</Typography>
        <Typography><strong>REACT_APP_SUPABASE_URL:</strong> {process.env.REACT_APP_SUPABASE_URL ? 'Set (hidden for security)' : 'Not set'}</Typography>
        <Typography><strong>REACT_APP_SUPABASE_ANON_KEY:</strong> {process.env.REACT_APP_SUPABASE_ANON_KEY ? 'Set (hidden for security)' : 'Not set'}</Typography>
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Debugging Instructions
        </Typography>
        <Typography paragraph>
          If you're seeing a white screen or experiencing issues, check the errors above for clues.
        </Typography>
        <Typography paragraph>
          <strong>Common issues:</strong>
        </Typography>
        <ul>
          <li>Missing environment variables - Check if your .env file is properly configured</li>
          <li>Supabase connection errors - Verify your API keys and URL</li>
          <li>React rendering errors - Check component syntax and dependencies</li>
          <li>Redux state issues - Look for store configuration problems</li>
        </ul>
      </Paper>
    </Container>
  );
};

export default Debug;
EOF

# Step 6: Replace index.tsx with a simplified version
echo "Creating simplified index.tsx..."
cat > src/index.tsx << 'EOF'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { store } from './store';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { initializeSupabaseAuth } from './utils/supabaseHelpers';
import './index.css';

// Initialize Supabase auth state
try {
  console.log('Starting Supabase auth initialization...');
  initializeSupabaseAuth()
    .then(() => console.log('Supabase auth initialization completed'))
    .catch(error => console.error('Supabase auth initialization error:', error));
} catch (error) {
  console.error('Exception during Supabase auth initialization:', error);
}

try {
  const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
  );

  console.log('Attempting to render React app...');
  
  root.render(
    <React.StrictMode>
      <Provider store={store}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </Provider>
    </React.StrictMode>
  );
  
  console.log('React rendering completed');
} catch (error) {
  console.error('Critical rendering error:', error);
  
  // Display fallback UI if React fails to render
  const rootElement = document.getElementById('root');
  if (rootElement) {
    rootElement.innerHTML = `
      <div style="padding: 20px; font-family: sans-serif;">
        <h2>Application Error</h2>
        <p>Sorry, the application failed to initialize. Please check the console for more details.</p>
        <pre style="background: #f0f0f0; padding: 10px; overflow: auto;">${
          error instanceof Error ? error.stack : String(error)
        }</pre>
      </div>
    `;
  }
}
EOF

# Step 7: Update App.tsx to include Debug route if necessary
echo "Checking if App.tsx needs to be updated..."
if [ -f src/App.tsx ]; then
  if ! grep -q "import Debug from './pages/Debug';" src/App.tsx; then
    echo "Adding Debug route to App.tsx..."
    # First, backup the App.tsx file
    cp src/App.tsx src/App.tsx.backup
    
    # Now attempt to add the import and route
    # This is simplified and might not work for all App.tsx structures
    # so we'll be cautious and check first
    
    # Add import statement
    sed -i.bak '0,/import/s/import/import Debug from '\''\.\/pages\/Debug'\'';\nimport/' src/App.tsx
    
    # Try to add the route - this is a simple approach and might need manual adjustment
    if grep -q "<Route path=" src/App.tsx; then
      # Find last Route and add our Debug route after it
      sed -i.bak '/<Route path/a\ \ \ \ \ \ \ \ \ \ <Route path="debug" element={<Debug \/>} \/>' src/App.tsx
      echo "Added Debug route to App.tsx - please verify it's correctly positioned"
    else
      echo "Could not automatically add Debug route to App.tsx. Please manually add:"
      echo "<Route path=\"debug\" element={<Debug />} />"
      echo "to your routes in App.tsx"
    fi
  else
    echo "Debug route already exists in App.tsx"
  fi
else
  echo "App.tsx not found. Please manually add Debug route."
fi

# Step 8: Check for and create .env file
echo "Checking for .env file..."
if [ ! -f .env ]; then
  echo "Creating .env file..."
  cat > .env << 'EOF'
# Supabase Configuration - REPLACE WITH YOUR ACTUAL VALUES
REACT_APP_SUPABASE_URL=https://your-project.supabase.co
REACT_APP_SUPABASE_ANON_KEY=your-anon-key
EOF
  echo "⚠️ Created .env file. Please update with your ACTUAL Supabase credentials before starting the app."
else
  echo ".env file exists, checking for required variables..."
  if ! grep -q "REACT_APP_SUPABASE_URL" .env || ! grep -q "REACT_APP_SUPABASE_ANON_KEY" .env; then
    echo "⚠️ WARNING: .env file might be missing required Supabase variables."
    echo "Make sure your .env file contains:"
    echo "REACT_APP_SUPABASE_URL=https://your-project.supabase.co"
    echo "REACT_APP_SUPABASE_ANON_KEY=your-anon-key"
  else
    echo "✅ .env file contains the required variables."
  fi
fi

echo ""
echo "===================================================="
echo "     WhatsApp Supabase Frontend Fix Complete!       "
echo "===================================================="
echo ""
echo "Next Steps:"
echo "1. If you created or updated the .env file, make sure to add your actual Supabase credentials."
echo "2. Restart your development server:"
echo "   npm start"
echo ""
echo "If you still see a white screen:"
echo "- Check the browser console (F12 or right-click -> Inspect -> Console)"
echo "- Navigate to http://localhost:3002/debug for detailed error information"
echo "- Check for any errors in the terminal output"
echo ""
echo "Good luck! 🚀"