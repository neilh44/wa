// Create a simple test page for WhatsAppQRCodeDebugger
// Test.js or TestDebugger.js
import React from 'react';
import ReactDOM from 'react-dom';
import WhatsAppQRCodeDebugger from './components/whatsapp/WhatsAppQRCodeDebugger';

// Simple CSS to ensure the component is visible
const testStyles = `
  body {
    margin: 0;
    padding: 20px;
    font-family: sans-serif;
    background-color: #f5f5f5;
  }
  
  .test-container {
    max-width: 1000px;
    margin: 0 auto;
    background-color: white;
    padding: 20px;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  }
  
  h1 {
    color: #333;
  }
`;

function TestDebuggerPage() {
  return (
    <div className="test-container">
      <h1>WhatsApp QR Code Debugger Test Page</h1>
      <p>This is a test implementation to verify the debugger is working correctly.</p>
      
      {/* Mount the debugger component */}
      <WhatsAppQRCodeDebugger />
      
      {/* Status information */}
      <div style={{ marginTop: '20px', padding: '10px', backgroundColor: '#f0f0f0', borderRadius: '4px' }}>
        <h3>Test Environment Information</h3>
        <p>Frontend URL: {window.location.href}</p>
        <p>API Base URL: http://127.0.0.1:8000/api (configured in the debugger)</p>
        <p>Current Time: {new Date().toLocaleString()}</p>
      </div>
    </div>
  );
}

// Insert the styles
const styleElement = document.createElement('style');
styleElement.textContent = testStyles;
document.head.appendChild(styleElement);

// Render the test page
const root = document.createElement('div');
root.id = 'test-root';
document.body.appendChild(root);

ReactDOM.render(<TestDebuggerPage />, root);

// Additional debugging to console
console.log('Test Debugger page mounted');
console.log('Checking for WhatsAppQRCodeDebugger component:', !!WhatsAppQRCodeDebugger);