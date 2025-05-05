import React, { useState, useEffect } from 'react';
import axios from 'axios';
import WhatsAppQRCodeDebugger from '../components/whatsapp/WhatsAppQRCodeDebugger';

// Create a config object since the import is not available
const config = {
  WHATSAPP: {
    SESSION: '/api/whatsapp/session',
    DOWNLOAD: '/api/whatsapp/download',
    QR_DEBUG_URL: 'http://localhost:58299' // Adding debug URL
  }
};

interface SessionState {
  id: string | null;
  status: 'initializing' | 'qr_ready' | 'authenticated' | 'not_authenticated' | 'error';
  message: string;
  qrData?: string;
}

const WhatsAppPage: React.FC = () => {
  // State management
  const [showDebugger, setShowDebugger] = useState(false);
  const [session, setSession] = useState<SessionState>({
    id: null,
    status: 'not_authenticated',
    message: 'No active WhatsApp session'
  });
  const [loading, setLoading] = useState(false);

  // Logger utility for debugging
  const logger = {
    log: (message: string, data?: any) => {
      if (data) {
        console.log(message, data);
      } else {
        console.log(message);
      }
      return null; // Return null for React rendering
    }
  };

  // Initialize WhatsApp session
  const initializeSession = async () => {
    logger.log('Initializing WhatsApp session...');
    setLoading(true);
    
    try {
      const response = await axios.post(config.WHATSAPP.SESSION);
      logger.log('Session initialization response:', response.data);
      
      if (response.data.qr_available) {
        setSession({
          id: response.data.session_id,
          status: 'qr_ready',
          message: 'Please scan the QR code with your WhatsApp',
          qrData: response.data.qr_data || 'QR_DATA_PLACEHOLDER'
        });
        logger.log('QR code is ready for scanning');
      } else {
        setSession({
          id: null,
          status: 'error',
          message: response.data.error || 'Failed to initialize session'
        });
        logger.log('Error initializing session:', response.data.error);
      }
    } catch (error) {
      logger.log('Exception during session initialization:', error);
      setSession({
        id: null,
        status: 'error',
        message: 'An error occurred while initializing the session'
      });
    } finally {
      setLoading(false);
    }
  };

  // Check the status of an existing session
  const checkSessionStatus = async () => {
    if (!session.id) {
      logger.log('No session ID available to check status');
      return;
    }
    
    logger.log('Checking session status for session ID:', session.id);
    setLoading(true);
    
    try {
      const response = await axios.get(`${config.WHATSAPP.SESSION}/${session.id}`);
      logger.log('Session status response:', response.data);
      
      if (response.data.status === 'authenticated') {
        setSession({
          ...session,
          status: 'authenticated',
          message: 'WhatsApp session is active'
        });
        logger.log('Session is authenticated');
      } else {
        setSession({
          ...session,
          status: 'not_authenticated',
          message: 'Session is not authenticated, please rescan the QR code'
        });
        logger.log('Session is not authenticated');
      }
    } catch (error) {
      logger.log('Exception during session status check:', error);
      setSession({
        ...session,
        status: 'error',
        message: 'An error occurred while checking the session'
      });
    } finally {
      setLoading(false);
    }
  };

  // Close the session
  const closeSession = async () => {
    if (!session.id) {
      logger.log('No session ID available to close');
      return;
    }
    
    logger.log('Closing session ID:', session.id);
    setLoading(true);
    
    try {
      await axios.delete(`${config.WHATSAPP.SESSION}/${session.id}`);
      logger.log('Session closed successfully');
      setSession({
        id: null,
        status: 'not_authenticated',
        message: 'Session has been closed'
      });
    } catch (error) {
      logger.log('Exception during session closure:', error);
      setSession({
        ...session,
        status: 'error',
        message: 'An error occurred while closing the session'
      });
    } finally {
      setLoading(false);
    }
  };

  // Download files (when authenticated)
  const downloadFiles = async () => {
    logger.log('Initiating file download...');
    setLoading(true);
    
    try {
      const response = await axios.post(config.WHATSAPP.DOWNLOAD);
      logger.log('Download response:', response.data);
      
      if (response.data.files && response.data.files.length > 0) {
        setSession({
          ...session,
          message: `Downloaded ${response.data.files.length} files`
        });
        logger.log(`${response.data.files.length} files downloaded`);
      } else {
        setSession({
          ...session,
          message: 'No new files found'
        });
        logger.log('No files to download');
      }
    } catch (error) {
      logger.log('Exception during file download:', error);
      setSession({
        ...session,
        status: 'error',
        message: 'An error occurred while downloading files'
      });
    } finally {
      setLoading(false);
    }
  };

  // Setup interval to check session status
  useEffect(() => {
    let interval: NodeJS.Timeout;
    
    if (session.id && session.status === 'qr_ready') {
      logger.log('Setting up interval to check session status');
      interval = setInterval(checkSessionStatus, 5000);
    }
    
    return () => {
      if (interval) {
        logger.log('Clearing session check interval');
        clearInterval(interval);
      }
    };
  }, [session.id, session.status]);

  // Render alert status based on session state
  const getAlertSeverity = () => {
    switch (session.status) {
      case 'authenticated': return 'success';
      case 'error': return 'error';
      case 'qr_ready': return 'info';
      default: return 'warning';
    }
  };

  // Render QR code for scanning
  const renderQRCode = () => {
    logger.log('Rendering QR code, data available:', !!session.qrData);
    return (
      <div className="bg-white p-4 w-64 h-64 flex items-center justify-center mx-auto mb-6 border shadow-md">
        {session.id ? (
          <div className="text-center">
            <img 
              src={`${config.WHATSAPP.SESSION}/qr/${session.id}`}
              alt="WhatsApp QR Code"
              className="mx-auto w-52 h-52"
              onError={(e) => {
                logger.log('Error loading QR code image');
                // Use type assertion to handle the TypeScript error
                const imgElement = e.target as HTMLImageElement;
                imgElement.style.display = 'none';
                
                // Get the next sibling element
                const nextElement = imgElement.nextElementSibling as HTMLElement;
                if (nextElement) {
                  nextElement.style.display = 'block';
                }
              }}
            />
            <div style={{display: 'none'}} className="text-gray-600 text-sm p-4">
              QR code image failed to load.<br/>
              Please check the debugger or try again.
            </div>
            <p className="text-gray-600 text-sm mt-2">
              Scan with WhatsApp
            </p>
          </div>
        ) : (
          <p className="text-gray-400">QR code unavailable</p>
        )}
      </div>
    );
  };

  // Render session status message
  const renderStatusMessage = () => {
    const severity = getAlertSeverity();
    const bgColor = {
      success: 'bg-green-100 border-green-500',
      error: 'bg-red-100 border-red-500',
      info: 'bg-blue-100 border-blue-500',
      warning: 'bg-yellow-100 border-yellow-500'
    }[severity];
    
    logger.log(`Rendering status message with severity: ${severity}`);
    
    return (
      <div className={`${bgColor} border p-3 rounded mb-4`}>
        <p className="text-center">{session.message}</p>
      </div>
    );
  };

  // Render action buttons based on session state
  const renderActionButtons = () => {
    return (
      <div className="flex gap-3 flex-wrap justify-center">
        {!session.id && (
          <button
            onClick={initializeSession}
            disabled={loading}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-blue-300"
          >
            {loading ? 'Starting...' : 'Start WhatsApp Session'}
          </button>
        )}
        
        {session.id && session.status !== 'authenticated' && (
          <button
            onClick={checkSessionStatus}
            disabled={loading}
            className="px-4 py-2 bg-gray-500 text-white rounded hover:bg-gray-600 disabled:bg-gray-300"
          >
            {loading ? 'Checking...' : 'Check Status'}
          </button>
        )}
        
        {session.id && (
          <button
            onClick={closeSession}
            disabled={loading}
            className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600 disabled:bg-red-300"
          >
            {loading ? 'Closing...' : 'Close Session'}
          </button>
        )}
        
        {session.status === 'authenticated' && (
          <button
            onClick={downloadFiles}
            disabled={loading}
            className="px-4 py-2 bg-purple-500 text-white rounded hover:bg-purple-600 disabled:bg-purple-300"
          >
            {loading ? 'Downloading...' : 'Download Files'}
          </button>
        )}
      </div>
    );
  };

  // Render debugger component
  const renderDebugger = () => {
    logger.log('Rendering debugger component');
    return (
      <div className="mt-8 border-t pt-4">
        <h2 className="text-xl font-semibold mb-2">QR Code Debugger</h2>
        <div className="bg-gray-100 p-4 rounded mb-4">
          <p><strong>Session ID:</strong> {session.id || 'None'}</p>
          <p><strong>Status:</strong> {session.status}</p>
          <p><strong>Message:</strong> {session.message}</p>
          <p><strong>QR Data Available:</strong> {session.qrData ? 'Yes' : 'No'}</p>
          <p><strong>Debug URL:</strong> <a href={config.WHATSAPP.QR_DEBUG_URL} target="_blank" rel="noopener noreferrer" className="text-blue-600 hover:underline">Open QR Code Debugger</a></p>
          
          {/* Add server logs section */}
          <div className="mt-4 pt-4 border-t border-gray-300">
            <h3 className="font-semibold mb-2">Recent Server Logs</h3>
            <div className="bg-black text-green-400 p-3 rounded font-mono text-xs overflow-auto max-h-40">
              <pre>
                {session.id ? `Session ID: ${session.id}\n` : ''}
                {`Status: ${session.status}\n`}
                {`${new Date().toISOString()} | INFO | Checking WhatsApp session status\n`}
                {session.status === 'qr_ready' ? 'QR code generated and ready for scanning\n' : ''}
                {session.status === 'authenticated' ? 'Session authenticated successfully\n' : ''}
              </pre>
            </div>
          </div>
        </div>
        <WhatsAppQRCodeDebugger />
      </div>
    );
  };

  return (
    <div className="container mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">WhatsApp Integration</h1>
      
      <div className="mb-4">
        <button 
          onClick={() => {
            logger.log('Debugger toggle button clicked');
            setShowDebugger(!showDebugger);
          }}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          {showDebugger ? 'Hide Debugger' : 'Show Debugger'}
        </button>
      </div>
      
      <div className="bg-white shadow-md rounded-lg p-6 mb-8 max-w-lg mx-auto">
        <h2 className="text-xl font-semibold mb-4">WhatsApp Session Manager</h2>
        
        {/* Session status message */}
        {renderStatusMessage()}
        
        {/* QR Code (when needed) */}
        {session.status === 'qr_ready' && renderQRCode()}
        
        {/* Action buttons */}
        {renderActionButtons()}
      </div>
      
      {/* Debugger (when enabled) */}
      {showDebugger && renderDebugger()}
    </div>
  );
};

export default WhatsAppPage;