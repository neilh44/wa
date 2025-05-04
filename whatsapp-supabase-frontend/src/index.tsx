import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { store } from './store';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { initializeSupabaseAuth } from './utils/supabaseHelpers';
import { initDebugLogging } from './utils/debugLogging';
import ErrorBoundary from './components/debug/ErrorBoundary';
import './index.css';

// Initialize debug logging
initDebugLogging();

// Add Supabase initialization debugging
try {
  console.log('Starting Supabase auth initialization...');
  initializeSupabaseAuth()
    .then(() => console.log('Supabase auth initialization completed'))
    .catch(error => console.error('Supabase auth initialization error:', error));
} catch (error) {
  console.error('Exception during Supabase auth initialization:', error);
}

// Add Redux store debugging
try {
  console.log('Initial Redux state:', store.getState());
  
  // Subscribe to Redux state changes
  store.subscribe(() => {
    console.log('Redux state updated:', store.getState());
  });
} catch (error) {
  console.error('Redux store error:', error);
}

try {
  const root = ReactDOM.createRoot(
    document.getElementById('root') as HTMLElement
  );

  console.log('Attempting to render React app...');
  
  root.render(
    <ErrorBoundary>
      <Provider store={store}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </Provider>
    </ErrorBoundary>
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
