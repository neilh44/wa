import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './WhatsAppQRCodeDebugger.css';

// Configuration - adjust as needed
const API_BASE_URL = 'http://127.0.0.1:8000/api'; // Change this to match your API base URL
const DEBUG_LEVEL = 'verbose'; // 'basic' or 'verbose'
const BACKEND_CHECKS = true; // Set to false if you only want to debug frontend

const WhatsAppQRCodeDebugger = () => {
  const [debugLogs, setDebugLogs] = useState([]);
  const [sessionData, setSessionData] = useState(null);
  const [sessionId, setSessionId] = useState(null);
  const [qrData, setQrData] = useState(null);
  const [apiResponses, setApiResponses] = useState({});
  const [componentDetails, setComponentDetails] = useState({});
  const [apiAvailable, setApiAvailable] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [backendLogs, setBackendLogs] = useState([]);

  // Helper function to add log
  const addLog = (message, type = 'info') => {
    const timestamp = new Date().toISOString();
    setDebugLogs(prevLogs => [...prevLogs, { timestamp, message, type }]);
    console.log(`[${type.toUpperCase()}] ${message}`);
  };

  // Check if API is available
  const checkApiAvailability = async () => {
    try {
      addLog('Checking API availability...', 'info');
      const response = await axios.get(`${API_BASE_URL}/`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        timeout: 5000
      });
      
      setApiAvailable(true);
      addLog('✅ API is available', 'success');
      return true;
    } catch (error) {
      setApiAvailable(false);
      addLog('❌ API is not available. Check server status.', 'error');
      addLog(`Error details: ${error.message}`, 'error');
      return false;
    }
  };

  // Check WhatsApp component
  const analyzeWhatsAppComponent = () => {
    addLog('Analyzing WhatsAppQRCode component...', 'info');
    
    try {
      // Try to find component in window object
      const componentFound = window.WhatsAppQRCode || 
                            document.querySelector('[data-testid="whatsapp-qrcode"]') ||
                            document.querySelector('.whatsapp-qrcode');
      
      if (!componentFound) {
        addLog('❌ WhatsAppQRCode component not found in DOM', 'error');
        setComponentDetails(prev => ({...prev, found: false}));
      } else {
        addLog('✅ WhatsAppQRCode component found', 'success');
        setComponentDetails(prev => ({...prev, found: true}));
        
        // Check if QR container exists
        const qrContainer = document.querySelector('.qr-container') || 
                           document.querySelector('[data-testid="qr-container"]');
        
        if (!qrContainer) {
          addLog('❌ QR container element not found in component', 'error');
          setComponentDetails(prev => ({...prev, qrContainer: false}));
        } else {
          addLog('✅ QR container element found', 'success');
          setComponentDetails(prev => ({...prev, qrContainer: true}));
          
          // Check for QR image
          const qrImage = qrContainer.querySelector('img') ||
                         qrContainer.querySelector('canvas');
          
          if (!qrImage) {
            addLog('❌ QR image element not found in container', 'error');
            setComponentDetails(prev => ({...prev, qrImage: false}));
          } else {
            const imgSrc = qrImage.src || qrImage.dataset.src;
            addLog('✅ QR image element found', 'success');
            addLog(`QR image source: ${imgSrc ? imgSrc.substring(0, 40) + '...' : 'not set'}`, 'info');
            setComponentDetails(prev => ({...prev, qrImage: true, imgSrc}));
          }
        }
      }
    } catch (error) {
      addLog(`❌ Error analyzing component: ${error.message}`, 'error');
    }
  };

  // Initialize WhatsApp session
  const initializeSession = async () => {
    try {
      addLog('Initializing WhatsApp session...', 'info');
      
      const response = await axios.post(`${API_BASE_URL}/whatsapp/session`, {}, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      setApiResponses(prev => ({...prev, initSession: response.data}));
      setSessionData(response.data);
      
      if (response.data && response.data.session_id) {
        setSessionId(response.data.session_id);
        addLog(`✅ Session initialized with ID: ${response.data.session_id}`, 'success');
        
        if (response.data.already_authenticated) {
          addLog('✅ Session already authenticated', 'success');
          setIsAuthenticated(true);
        } else if (response.data.qr_available && response.data.qr_data) {
          addLog('✅ QR code data received from API', 'success');
          setQrData(response.data.qr_data);
          
          // Verify QR data format
          if (typeof response.data.qr_data === 'string') {
            addLog(`QR data length: ${response.data.qr_data.length} characters`, 'info');
            
            if (response.data.qr_data.length < 100) {
              addLog('❌ QR data seems too short to be valid', 'warning');
            }
            
            try {
              // Check if it's a valid base64
              const decodedLength = atob(response.data.qr_data).length;
              addLog(`✅ Valid base64 data (decoded length: ${decodedLength})`, 'success');
            } catch (e) {
              addLog('❌ QR data is not valid base64', 'error');
            }
          } else {
            addLog('❌ QR data is not a string, check format', 'error');
          }
        } else {
          addLog('❌ No QR code data in response', 'error');
        }
      } else {
        addLog('❌ No session ID in response', 'error');
      }
    } catch (error) {
      addLog(`❌ Error initializing session: ${error.message}`, 'error');
      if (error.response) {
        addLog(`Response status: ${error.response.status}`, 'error');
        addLog(`Response data: ${JSON.stringify(error.response.data)}`, 'error');
      }
    }
  };

  // Check session status
  const checkSessionStatus = async () => {
    if (!sessionId) {
      addLog('❌ No session ID available for status check', 'error');
      return;
    }
    
    try {
      addLog(`Checking session status for ID: ${sessionId}...`, 'info');
      
      const response = await axios.get(`${API_BASE_URL}/whatsapp/session/${sessionId}`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      
      setApiResponses(prev => ({...prev, sessionStatus: response.data}));
      
      if (response.data.status === 'authenticated') {
        addLog('✅ Session is authenticated', 'success');
        setIsAuthenticated(true);
      } else if (response.data.qr_refreshed && response.data.qr_data) {
        addLog('ℹ️ QR code refreshed', 'info');
        setQrData(response.data.qr_data);
      } else {
        addLog(`ℹ️ Session status: ${response.data.status}`, 'info');
      }
    } catch (error) {
      addLog(`❌ Error checking session status: ${error.message}`, 'error');
    }
  };

  // Fetch backend logs if available
  const fetchBackendLogs = async () => {
    if (!BACKEND_CHECKS) return;
    
    try {
      addLog('Fetching backend logs (if available)...', 'info');
      
      const response = await axios.get(`${API_BASE_URL}/debug/logs`, {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
        params: { service: 'whatsapp', lines: 20 }
      });
      
      if (response.data && response.data.logs) {
        setBackendLogs(response.data.logs);
        addLog('✅ Backend logs retrieved', 'success');
        
        // Check for QR code related errors in logs
        const qrErrors = response.data.logs.filter(log => 
          log.toLowerCase().includes('qr') && 
          (log.toLowerCase().includes('error') || log.toLowerCase().includes('fail'))
        );
        
        if (qrErrors.length > 0) {
          addLog(`⚠️ Found ${qrErrors.length} QR-related errors in backend logs`, 'warning');
          qrErrors.forEach(err => {
            addLog(`Backend log: ${err}`, 'warning');
          });
        }
      }
    } catch (error) {
      // This endpoint might not exist, which is ok
      addLog('ℹ️ Could not fetch backend logs (endpoint may not exist)', 'info');
    }
  };

  // Network request analysis
  const analyzeNetworkRequests = () => {
    addLog('Analyzing network requests...', 'info');
    
    if (window.performance && window.performance.getEntries) {
      const resources = window.performance.getEntries();
      const whatsappRequests = resources.filter(r => 
        r.name.includes('/whatsapp/') || r.name.includes('web.whatsapp.com')
      );
      
      addLog(`Found ${whatsappRequests.length} WhatsApp related requests`, 'info');
      
      if (DEBUG_LEVEL === 'verbose') {
        whatsappRequests.forEach(req => {
          addLog(`Request: ${req.name} (${req.duration ? req.duration.toFixed(2) : 'N/A'}ms)`, 'info');
          
          if (req.responseStatus && req.responseStatus !== 200) {
            addLog(`⚠️ Non-200 response: ${req.responseStatus}`, 'warning');
          }
        });
      }
    } else {
      addLog('❌ Performance API not available for network analysis', 'error');
    }
  };

  // Run all checks
  const runAllChecks = async () => {
    addLog('Starting WhatsApp QR Code debugging...', 'info');
    await checkApiAvailability();
    
    if (!apiAvailable) return;
    
    analyzeWhatsAppComponent();
    await initializeSession();
    
    if (sessionId) {
      await checkSessionStatus();
    }
    
    analyzeNetworkRequests();
    await fetchBackendLogs();
    
    addLog('Debugging process completed', 'info');
  };

  // Manual QR rendering test
  const testQRRendering = () => {
    if (!qrData) {
      addLog('❌ No QR data available for rendering test', 'error');
      return;
    }
    
    addLog('Testing manual QR rendering...', 'info');
    
    try {
      // Create a test img element
      const testImg = document.createElement('img');
      testImg.src = `data:image/png;base64,${qrData}`;
      testImg.style.width = '200px';
      testImg.style.height = '200px';
      testImg.style.border = '1px solid black';
      
      // Add to debug container
      const debugContainer = document.getElementById('whatsapp-debug-container');
      if (debugContainer) {
        // Create header
        const header = document.createElement('h4');
        header.textContent = 'QR Code Rendering Test:';
        debugContainer.appendChild(header);
        debugContainer.appendChild(testImg);
        
        testImg.onload = () => addLog('✅ Test QR image loaded successfully', 'success');
        testImg.onerror = () => addLog('❌ Test QR image failed to load', 'error');
      }
    } catch (error) {
      addLog(`❌ Error in rendering test: ${error.message}`, 'error');
    }
  };

  // Function to export debug data
  const exportDebugData = () => {
    const debugData = {
      timestamp: new Date().toISOString(),
      logs: debugLogs,
      sessionData,
      apiResponses,
      componentDetails,
      backendLogs
    };
    
    const blob = new Blob([JSON.stringify(debugData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `whatsapp-qr-debug-${new Date().toISOString()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    addLog('Debug data exported', 'success');
  };

  // Execute checks on mount
  useEffect(() => {
    runAllChecks();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Render test QR code when QR data is available
  useEffect(() => {
    if (qrData) {
      testQRRendering();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qrData]);

  return (
    <div className="whatsapp-qrcode-debugger" id="whatsapp-debug-container">
      <h2>WhatsApp QR Code Debugger</h2>
      
      <div className="debug-controls">
        <button onClick={runAllChecks}>Run All Checks</button>
        <button onClick={initializeSession}>Initialize Session</button>
        {sessionId && <button onClick={checkSessionStatus}>Check Session Status</button>}
        <button onClick={analyzeWhatsAppComponent}>Analyze Component</button>
        <button onClick={exportDebugData}>Export Debug Data</button>
      </div>
      
      <div className="debug-status">
        <h3>Status Summary</h3>
        <div className="status-grid">
          <div className={`status-item ${apiAvailable ? 'success' : 'error'}`}>
            API Available: {apiAvailable ? '✅' : '❌'}
          </div>
          <div className={`status-item ${componentDetails.found ? 'success' : 'error'}`}>
            Component Found: {componentDetails.found ? '✅' : '❌'}
          </div>
          <div className={`status-item ${sessionId ? 'success' : 'error'}`}>
            Session Created: {sessionId ? '✅' : '❌'}
          </div>
          <div className={`status-item ${qrData ? 'success' : 'error'}`}>
            QR Data Received: {qrData ? '✅' : '❌'}
          </div>
          <div className={`status-item ${componentDetails.qrContainer ? 'success' : 'error'}`}>
            QR Container: {componentDetails.qrContainer ? '✅' : '❌'}
          </div>
          <div className={`status-item ${componentDetails.qrImage ? 'success' : 'error'}`}>
            QR Image Element: {componentDetails.qrImage ? '✅' : '❌'}
          </div>
        </div>
      </div>
      
      <div className="debug-logs">
        <h3>Debug Logs</h3>
        <div className="log-container">
          {debugLogs.map((log, index) => (
            <div key={index} className={`log-entry ${log.type}`}>
              <span className="log-time">[{new Date(log.timestamp).toLocaleTimeString()}]</span>
              <span className="log-message">{log.message}</span>
            </div>
          ))}
        </div>
      </div>
      
      {backendLogs.length > 0 && (
        <div className="backend-logs">
          <h3>Backend Logs (Last 20 entries)</h3>
          <div className="log-container">
            {backendLogs.map((log, index) => (
              <div key={index} className="backend-log-entry">
                <pre>{log}</pre>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {sessionData && DEBUG_LEVEL === 'verbose' && (
        <div className="response-data">
          <h3>API Response Data</h3>
          <pre>{JSON.stringify(sessionData, null, 2)}</pre>
        </div>
      )}
    </div>
  );
};

export default WhatsAppQRCodeDebugger;
