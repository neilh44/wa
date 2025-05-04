import React, { useState } from 'react';
import WhatsAppQRCode from '../components/whatsapp/WhatsAppQRCode';
import WhatsAppQRCodeDebugger from '../components/whatsapp/WhatsAppQRCodeDebugger';

const WhatsAppPage: React.FC = () => {
  const [showDebugger, setShowDebugger] = useState(false);

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">WhatsApp Integration</h1>
      
      <div className="mb-4">
        <button 
          onClick={() => setShowDebugger(!showDebugger)}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          {showDebugger ? 'Hide Debugger' : 'Show Debugger'}
        </button>
      </div>
      
      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-2">Original WhatsApp QR Code Component</h2>
        <div className="border p-4 rounded">
          <WhatsAppQRCode />
        </div>
      </div>
      
      {showDebugger && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-2">QR Code Debugger</h2>
          <WhatsAppQRCodeDebugger />
        </div>
      )}
    </div>
  );
};

export default WhatsAppPage;
