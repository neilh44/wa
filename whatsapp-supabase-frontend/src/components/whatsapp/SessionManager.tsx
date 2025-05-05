// Fix for the "Data too long" error in SessionManager.tsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Box, Paper, Typography, CircularProgress, Alert, Divider } from '@mui/material';
import { QRCodeSVG } from 'qrcode.react';
import config from '../../api/config';
import Button from '../common/Button';

interface SessionState {
  id: string | null;
  status: 'initializing' | 'qr_ready' | 'authenticated' | 'not_authenticated' | 'error';
  message: string;
  qrData?: string;
}

const SessionManager: React.FC = () => {
  const [session, setSession] = useState<SessionState>({
    id: null,
    status: 'not_authenticated',
    message: 'No active WhatsApp session'
  });
  const [loading, setLoading] = useState(false);
  const [qrError, setQrError] = useState<string | null>(null);

  // This function processes QR data to make it compatible with QRCodeSVG
  const processQrData = (data: string | undefined): string => {
    if (!data) return '';
    
    // If data is a data URL (begins with "data:"), extract just the WhatsApp URL part
    if (data.startsWith('data:')) {
      try {
        // Try to extract WhatsApp URL if it's embedded in the data URL
        const matches = data.match(/https:\/\/web\.whatsapp\.com\/[^\s"')]+/);
        if (matches && matches[0]) {
          return matches[0];
        }
        
        // If no WhatsApp URL found, return a shorter version of the data
        // Data URLs are very long, so we'll truncate it to prevent the "Data too long" error
        return data.substring(0, 500); // Limiting to 500 characters
      } catch (e) {
        console.error('Error processing QR data:', e);
        setQrError('Error processing QR data');
        return '';
      }
    }
    
    return data;
  };

  const initializeSession = async () => {
    setLoading(true);
    setQrError(null);
    try {
      const response = await axios.post(config.WHATSAPP.SESSION);
      if (response.data.qr_available) {
        setSession({
          id: response.data.session_id,
          status: 'qr_ready',
          message: 'Please scan the QR code with your WhatsApp',
          qrData: response.data.qr_data // Get actual QR data from backend
        });
      } else {
        setSession({
          id: null,
          status: 'error',
          message: response.data.error || 'Failed to initialize session'
        });
      }
    } catch (error) {
      setSession({
        id: null,
        status: 'error',
        message: 'An error occurred while initializing the session'
      });
    } finally {
      setLoading(false);
    }
  };

  const checkSessionStatus = async () => {
    if (!session.id) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${config.WHATSAPP.SESSION}/${session.id}`);
      if (response.data.status === 'authenticated') {
        setSession({
          ...session,
          status: 'authenticated',
          message: 'WhatsApp session is active'
        });
      } else {
        setSession({
          ...session,
          status: 'not_authenticated',
          message: 'Session is not authenticated, please rescan the QR code'
        });
      }
    } catch (error) {
      setSession({
        ...session,
        status: 'error',
        message: 'An error occurred while checking the session'
      });
    } finally {
      setLoading(false);
    }
  };

  const closeSession = async () => {
    if (!session.id) return;
    
    setLoading(true);
    try {
      await axios.delete(`${config.WHATSAPP.SESSION}/${session.id}`);
      setSession({
        id: null,
        status: 'not_authenticated',
        message: 'Session has been closed'
      });
    } finally {
      setLoading(false);
    }
  };

  const downloadFiles = async () => {
    setLoading(true);
    try {
      const response = await axios.post(config.WHATSAPP.DOWNLOAD);
      if (response.data.files && response.data.files.length > 0) {
        setSession({
          ...session,
          message: `Downloaded ${response.data.files.length} files`
        });
      } else {
        setSession({
          ...session,
          message: 'No new files found'
        });
      }
    } catch (error) {
      setSession({
        ...session,
        status: 'error',
        message: 'An error occurred while downloading files'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check session status periodically if there's an active session
    let interval: NodeJS.Timeout;
    
    if (session.id && session.status === 'qr_ready') {
      interval = setInterval(checkSessionStatus, 5000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [session.id, session.status]);

  // Process the QR data to be used in the QRCodeSVG component
  const qrDataToRender = processQrData(session.qrData);

  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h6" gutterBottom>
        WhatsApp Session
      </Typography>
      
      <Divider sx={{ mb: 2 }} />
      
      <Box sx={{ mb: 3 }}>
        <Alert 
          severity={
            session.status === 'authenticated' ? 'success' : 
            session.status === 'error' ? 'error' : 
            session.status === 'qr_ready' ? 'info' : 'warning'
          }
        >
          {session.message}
        </Alert>
      </Box>
      
      {session.status === 'qr_ready' && (
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
          {session.qrData ? (
            <Box sx={{ p: 2 }}>
              {!qrError ? (
                // Only try to render QR code if qrDataToRender is not empty and no error
                qrDataToRender ? (
                  <QRCodeSVG 
                    value={qrDataToRender}
                    size={200}
                    level="H" // High error correction
                    includeMargin={true}
                  />
                ) : (
                  <CircularProgress />
                )
              ) : (
                // Show error message if QR processing failed
                <Alert severity="error" sx={{ mb: 2 }}>
                  {qrError}
                </Alert>
              )}
              <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
                Scan with WhatsApp
              </Typography>
            </Box>
          ) : (
            <Paper sx={{ p: 2, width: 200, height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CircularProgress />
            </Paper>
          )}
        </Box>
      )}
      
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        {!session.id && (
          <Button
            variant="contained"
            onClick={initializeSession}
            loading={loading}
          >
            Start WhatsApp Session
          </Button>
        )}
        
        {session.id && session.status !== 'authenticated' && (
          <Button
            variant="outlined"
            onClick={checkSessionStatus}
            loading={loading}
          >
            Check Status
          </Button>
        )}
        
        {session.id && (
          <Button
            variant="outlined"
            color="error"
            onClick={closeSession}
            loading={loading}
          >
            Close Session
          </Button>
        )}
        
        {session.status === 'authenticated' && (
          <Button
            variant="contained"
            color="secondary"
            onClick={downloadFiles}
            loading={loading}
          >
            Download Files
          </Button>
        )}
      </Box>
    </Paper>
  );
};

export default SessionManager;