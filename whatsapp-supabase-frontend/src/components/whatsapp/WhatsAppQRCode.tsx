import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import './WhatsAppQRCode.css';

interface WhatsAppQRCodeProps {
  onAuthenticated?: (status: boolean) => void;
  className?: string;
}

const WhatsAppQRCode: React.FC<WhatsAppQRCodeProps> = ({ 
  onAuthenticated, 
  className = '' 
}) => {
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [qrData, setQrData] = useState<string | null>(null);
  const [status, setStatus] = useState<'initializing' | 'qr_ready' | 'authenticated' | 'error'>('initializing');
  const [error, setError] = useState<string | null>(null);
  const [qrSize, setQrSize] = useState<number>(250);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const maxRetries = 3;
  const [retryCount, setRetryCount] = useState<number>(0);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const imgRef = useRef<HTMLImageElement>(null);

  // Get auth token
  const getAuthToken = (): string => {
    return localStorage.getItem('token') || sessionStorage.getItem('token') || '';
  };

  // Initialize WhatsApp session
  const initializeSession = async () => {
    try {
      console.log('Initializing WhatsApp session...');
      setStatus('initializing');
      setError(null);
      
      // Clear any existing polling
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
      
      // Make API request to initialize session
      const response = await axios.post('/api/whatsapp/session', {}, {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      });
      
      console.log('Session initialization response:', response.data);
      
      if (response.data) {
        setSessionId(response.data.session_id);
        
        if (response.data.already_authenticated) {
          console.log('Already authenticated');
          setStatus('authenticated');
          onAuthenticated && onAuthenticated(true);
        } else if (response.data.qr_available && response.data.qr_data) {
          console.log('QR code available, length:', response.data.qr_data.length);
          setQrData(response.data.qr_data);
          setStatus('qr_ready');
          
          // Start polling for session status
          startPolling(response.data.session_id);
        } else {
          console.error('No QR code or authentication in response');
          setError('QR code not available. Please try again.');
          setStatus('error');
        }
      } else {
        setError('Invalid response from server');
        setStatus('error');
      }
    } catch (err: any) {
      console.error('Error initializing session:', err);
      setError(err.response?.data?.detail || err.message || 'Failed to initialize WhatsApp session');
      setStatus('error');
      
      // Retry initialization if under max retries
      if (retryCount < maxRetries) {
        console.log(`Retrying initialization (attempt ${retryCount + 1}/${maxRetries})...`);
        setRetryCount(prev => prev + 1);
        setTimeout(initializeSession, 3000);
      }
    }
  };

  // Start polling for session status
  const startPolling = (sid: string) => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
    }
    
    console.log('Starting session status polling for', sid);
    
    pollingIntervalRef.current = setInterval(() => {
      checkSessionStatus(sid);
    }, 5000);
  };

  // Check session status
  const checkSessionStatus = async (sid: string) => {
    if (!sid) {
      console.error('No session ID for status check');
      return;
    }
    
    try {
      console.log('Checking session status...');
      
      const response = await axios.get(`/api/whatsapp/session/${sid}`, {
        headers: {
          'Authorization': `Bearer ${getAuthToken()}`
        }
      });
      
      console.log('Session status response:', response.data);
      
      if (response.data.status === 'authenticated') {
        console.log('Session authenticated!');
        
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          pollingIntervalRef.current = null;
        }
        
        setStatus('authenticated');
        onAuthenticated && onAuthenticated(true);
      } else if (response.data.qr_refreshed && response.data.qr_data) {
        console.log('QR code refreshed');
        setQrData(response.data.qr_data);
        
        // Update UI to show new QR code
        if (status !== 'qr_ready') {
          setStatus('qr_ready');
        }
      }
    } catch (err: any) {
      console.error('Error checking session status:', err);
    }
  };

  // Try to render QR code in multiple ways
  const renderQRCode = () => {
    if (!qrData) return null;
    
    console.log('Rendering QR code, data length:', qrData.length);
    
    // Return main image and fallback canvas
    return (
      <div className="qr-visual-container">
        {/* Main QR image using img tag */}
        <img
          ref={imgRef}
          src={`data:image/png;base64,${qrData}`}
          alt="WhatsApp QR Code"
          className="qr-image"
          width={qrSize}
          height={qrSize}
          onError={(e) => {
            console.error('Error loading QR image');
            
            // Try rendering in canvas as backup
            if (canvasRef.current && qrData) {
              try {
                renderInCanvas();
              } catch (canvasErr) {
                console.error('Canvas rendering failed:', canvasErr);
              }
            }
          }}
        />
        
        {/* Fallback canvas element */}
        <canvas 
          ref={canvasRef}
          width={qrSize}
          height={qrSize}
          style={{ display: 'none' }}
          className="qr-canvas"
        />
      </div>
    );
  };
  
  // Helper to render in canvas
  const renderInCanvas = () => {
    if (!canvasRef.current || !qrData) return;
    
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    
    if (!ctx) return;
    
    const img = new Image();
    img.onload = () => {
      canvas.style.display = 'block';
      if (imgRef.current) imgRef.current.style.display = 'none';
      
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    };
    img.onerror = (e) => {
      console.error('Error loading image in canvas:', e);
    };
    img.src = `data:image/png;base64,${qrData}`;
  };

  // Initialize on component mount
  useEffect(() => {
    console.log('WhatsAppQRCode component mounted');
    initializeSession();
    
    // Cleanup on unmount
    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, []);

  // Debug rendering when QR data changes
  useEffect(() => {
    if (qrData && status === 'qr_ready') {
      console.log('QR data changed, attempting rendering');
      // Optionally force canvas rendering here
    }
  }, [qrData, status]);

  return (
    <div className={`whatsapp-qrcode ${className}`} data-testid="whatsapp-qrcode">
      <div className="whatsapp-header">
        <h3>Connect to WhatsApp</h3>
      </div>
      
      <div className="whatsapp-content">
        {status === 'initializing' && (
          <div className="loading-container">
            <div className="loading-spinner"></div>
            <p>Initializing WhatsApp connection...</p>
          </div>
        )}
        
        {status === 'qr_ready' && qrData && (
          <div className="qr-container" data-testid="qr-container">
            {renderQRCode()}
            
            <div className="scan-instructions">
              <p>Scan this QR code with WhatsApp on your phone</p>
              <ol>
                <li>Open WhatsApp on your phone</li>
                <li>Tap <strong>Settings</strong> &gt; <strong>Linked Devices</strong></li>
                <li>Tap <strong>Link a Device</strong></li>
                <li>Point your phone camera at this screen to scan the QR code</li>
              </ol>
            </div>
            
            <button className="refresh-button" onClick={() => initializeSession()}>
              Refresh QR Code
            </button>
          </div>
        )}
        
        {status === 'authenticated' && (
          <div className="success-container">
            <div className="success-icon">✓</div>
            <h3>Successfully Connected!</h3>
            <p>Your WhatsApp account is now linked.</p>
          </div>
        )}
        
        {status === 'error' && (
          <div className="error-container">
            <p className="error-message">{error}</p>
            <button className="retry-button" onClick={() => {
              setRetryCount(0);
              initializeSession();
            }}>
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default WhatsAppQRCode;