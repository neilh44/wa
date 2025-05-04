import React from 'react';
import ReactDOM from 'react-dom/client';
import Diagnostic from './pages/Diagnostic';
import './index.css';

// Add error handling to catch initialization errors
try {
  console.log('Attempting to render minimal diagnostic page...');
  
  const root = document.getElementById('root');
  
  if (root) {
    ReactDOM.createRoot(root).render(
      <React.StrictMode>
        <Diagnostic />
      </React.StrictMode>
    );
    console.log('Successfully rendered diagnostic page. If you see a white screen, check browser console for errors.');
  } else {
    console.error('Root element not found in the DOM. Check your public/index.html file.');
    // Try to add a visible error message to the body
    document.body.innerHTML = `
      <div style="padding: 20px; font-family: sans-serif;">
        <h2>App Initialization Error</h2>
        <p>Could not find the root element in the DOM. Check your public/index.html file.</p>
      </div>
    `;
  }
} catch (error) {
  console.error('Critical error during app initialization:', error);
  // Try to add a visible error message to the body
  document.body.innerHTML = `
    <div style="padding: 20px; font-family: sans-serif;">
      <h2>App Initialization Error</h2>
      <p>The application failed to initialize. Error details:</p>
      <pre style="background-color: #f7f7f7; padding: 10px; border-radius: 4px; overflow: auto;">${error.message}\n\n${error.stack}</pre>
    </div>
  `;
}
