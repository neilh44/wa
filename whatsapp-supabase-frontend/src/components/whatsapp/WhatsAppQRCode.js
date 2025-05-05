// WhatsAppQRCode.js - Main component that needs fixing
import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './WhatsAppQRCode.css';

const API_BASE_URL = 'http://127.0.0.1:8000/api'; // Change as needed to match your API base URL

const WhatsAppQRCode = () => {
  const [sessionId, setSessionId] = useState(null);
  const [qrData, setQrData] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [statusCheckInterval, setStatusCheckInterval] = useState(null);

  // Initialize WhatsApp session
  const initializeSession = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await axios.post(`${API_BASE_URL}/whatsapp/session`, {}, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      if (response.data && response.data.session_id) {
        setSessionId(response.data.session_id);
        
        // Check if already authenticated
        if (response.data.already_authenticated) {
          setIsAuthenticated(true);
        } 
        // Check if QR data is available
        else if (response.data.qr_available && response.data.qr_data) {
          setQrData(response.data.qr_data);
        }
        
        // Start periodic status checks
        startStatusChecks(response.data.session_id);
      } else {
        setError('Invalid response from server. Session ID not received.');
      }
    } catch (error) {
      console.error('Error initializing WhatsApp session:', error);
      setError('Failed to initialize WhatsApp session. ' + (error.response?.data?.message || error.message));
    } finally {
      setLoading(false);
    }
  };

  // Check session status periodically
  const startStatusChecks = (id) => {
    // Clear any existing interval
    if (statusCheckInterval) {
      clearInterval(statusCheckInterval);
    }
    
    // Set up new interval
    const interval = setInterval(async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/whatsapp/session/${id}`, {
          headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
        });
        
        if (response.data.status === 'authenticated') {
          setIsAuthenticated(true);
          clearInterval(interval);
          setStatusCheckInterval(null);
        } 
        // Check if QR has been refreshed
        else if (response.data.qr_refreshed && response.data.qr_data) {
          setQrData(response.data.qr_data);
        }
      } catch (error) {
        console.error('Error checking session status:', error);
        // Don't stop the interval on error, just log it
      }
    }, 5000); // Check every 5 seconds
    
    setStatusCheckInterval(interval);
  };

  // Initialize session on component mount
  useEffect(() => {
    initializeSession();
    
    // Clean up interval on component unmount
    return () => {
      if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
      }
    };
  }, []);

  // Render QR code when data is available
  const renderQR = () => {
    if (!qrData) return null;
    
    // Determine if QR data is base64 or just a string
    const isBase64 = /^[A-Za-z0-9+/=]+$/.test(qrData) && qrData.length % 4 === 0;
    
    if (isBase64) {
      return (
        <div className="qr-container" data-testid="qr-container">
          <img 
            src={`data:image/png;base64,${qrData}`} 
            alt="WhatsApp QR Code" 
            className="qr-image"
          />
        </div>
      );
    } else {
      // If not base64, it might be a string that needs to be rendered as QR code
      // You could use a library like qrcode.react here
      return (
        <div className="qr-container" data-testid="qr-container">
          <div className="qr-text-data">{qrData}</div>
        </div>
      );
    }
  };

  // Handle retry if there's an error
  const handleRetry = () => {
    initializeSession();
  };

  return (
    <div className="whatsapp-qrcode" data-testid="whatsapp-qrcode">
      <h3>WhatsApp Connection</h3>
      
      {loading && (
        <div className="loading-container">
          <div className="loading-spinner"></div>
          <p>Initializing WhatsApp connection...</p>
        </div>
      )}
      
      {error && (
        <div className="error-container">
          <p className="error-message">{error}</p>
          <button className="retry-button" onClick={handleRetry}>Retry</button>
        </div>
      )}
      
      {isAuthenticated ? (
        <div className="authenticated-container">
          <div className="success-checkmark">✓</div>
          <p>WhatsApp connection established!</p>
        </div>
      ) : (
        !loading && !error && (
          <div className="qr-section">
            <p>Scan this QR code with WhatsApp on your phone to connect</p>
            {renderQR()}
            <p className="hint-text">Open WhatsApp, tap Menu or Settings and select WhatsApp Web</p>
          </div>
        )
      )}
    </div>
  );
};

export default WhatsAppQRCode;
