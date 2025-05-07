import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { store } from './store';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { initializeSupabaseAuth } from './utils/supabaseHelpers';
import axios from 'axios';
import './index.css';

// Setup axios interceptors for authentication
const setupAxiosInterceptors = () => {
  // Request interceptor to add the token to every request
  axios.interceptors.request.use(
    (config) => {
      // Get token from localStorage
      const token = localStorage.getItem('token');
      
      // If token exists, add it to the header
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor to handle authentication errors
  axios.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      // Handle 401 errors globally
      if (error.response && error.response.status === 401) {
        console.error('Authentication failed:', error);
        
        // Only redirect if not already on login page
        if (!window.location.pathname.includes('/login')) {
          // Clear token
          localStorage.removeItem('token');
          
          console.log('Session expired, redirecting to login...');
          // Redirect to login page
          window.location.href = '/login';
        }
      }
      
      return Promise.reject(error);
    }
  );
  
  console.log('Axios interceptors configured for authentication');
};

// Initialize Supabase auth state
try {
  console.log('Starting Supabase auth initialization...');
  initializeSupabaseAuth()
    .then(() => console.log('Supabase auth initialization completed'))
    .catch(error => console.error('Supabase auth initialization error:', error));
} catch (error) {
  console.error('Exception during Supabase auth initialization:', error);
}

// Initialize Axios interceptors for API authentication
try {
  console.log('Setting up Axios interceptors...');
  setupAxiosInterceptors();
} catch (error) {
  console.error('Failed to setup Axios interceptors:', error);
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