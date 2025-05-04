import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Box, Paper, Typography, CircularProgress, Alert, Divider } from '@mui/material';
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

  const initializeSession = async () => {
    setLoading(true);
    try {
      const response = await axios.post(config.WHATSAPP.SESSION);
      if (response.data.qr_available) {
        setSession({
          id: response.data.session_id,
          status: 'qr_ready',
          message: 'Please scan the QR code with your WhatsApp',
          qrData: 'QR_DATA_PLACEHOLDER' // In a real app, you'd use the actual QR data
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
    } catch (error) {
      setSession({
        ...session,
        status: 'error',
        message: 'An error occurred while closing the session'
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
          {/* In a real app, you'd display an actual QR code here */}
          <Paper sx={{ p: 2, width: 200, height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Typography variant="body2" color="text.secondary" align="center">
              QR Code placeholder<br />
              Scan with WhatsApp
            </Typography>
          </Paper>
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
