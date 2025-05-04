import React, { useEffect, useState } from 'react';
import { Box, Container, Typography, Paper, Accordion, AccordionSummary, AccordionDetails } from '@mui/material';

interface LogEntry {
  timestamp: string;
  type: string;
  message: string;
}

interface DebugLogs {
  errors: LogEntry[];
  warnings: LogEntry[];
  reactError: any;
}

const Debug: React.FC = () => {
  const [logs, setLogs] = useState<DebugLogs>({
    errors: [],
    warnings: [],
    reactError: null
  });

  useEffect(() => {
    // Get logs from localStorage via the debug utils
    if (window.debugUtils) {
      setLogs(window.debugUtils.getLogs());
    } else {
      // Try to get raw logs if debugUtils isn't available
      try {
        const errors = JSON.parse(localStorage.getItem('debug_error_logs') || '[]');
        const warnings = JSON.parse(localStorage.getItem('debug_warn_logs') || '[]');
        const reactError = JSON.parse(localStorage.getItem('react_error') || 'null');
        setLogs({ errors, warnings, reactError });
      } catch (e) {
        console.error('Error loading logs:', e);
      }
    }
  }, []);

  const formatTime = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleTimeString();
    } catch (e) {
      return timestamp;
    }
  };

  return (
    <Container>
      <Typography variant="h4" component="h1" gutterBottom sx={{ mt: 4 }}>
        Debug Information
      </Typography>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          React Error
        </Typography>
        {logs.reactError ? (
          <Box sx={{ backgroundColor: '#fff0f0', p: 2, borderRadius: 1 }}>
            <Typography variant="body1" gutterBottom>
              <strong>Message:</strong> {logs.reactError.message}
            </Typography>
            <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
              <strong>Stack:</strong> 
              {logs.reactError.stack}
            </Typography>
            <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
              <strong>Component Stack:</strong> 
              {logs.reactError.componentStack}
            </Typography>
          </Box>
        ) : (
          <Typography>No React errors caught by the ErrorBoundary.</Typography>
        )}
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Console Errors ({logs.errors.length})
        </Typography>
        {logs.errors.length > 0 ? (
          logs.errors.map((error, index) => (
            <Accordion key={index}>
              <AccordionSummary>
                <Typography>
                  [{formatTime(error.timestamp)}] {error.message.substring(0, 60)}
                  {error.message.length > 60 ? '...' : ''}
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                  {error.message}
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))
        ) : (
          <Typography>No console errors recorded.</Typography>
        )}
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Console Warnings ({logs.warnings.length})
        </Typography>
        {logs.warnings.length > 0 ? (
          logs.warnings.map((warning, index) => (
            <Accordion key={index}>
              <AccordionSummary>
                <Typography>
                  [{formatTime(warning.timestamp)}] {warning.message.substring(0, 60)}
                  {warning.message.length > 60 ? '...' : ''}
                </Typography>
              </AccordionSummary>
              <AccordionDetails>
                <Typography component="pre" sx={{ whiteSpace: 'pre-wrap' }}>
                  {warning.message}
                </Typography>
              </AccordionDetails>
            </Accordion>
          ))
        ) : (
          <Typography>No console warnings recorded.</Typography>
        )}
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Environment Variables
        </Typography>
        <Typography><strong>NODE_ENV:</strong> {process.env.NODE_ENV}</Typography>
        <Typography><strong>REACT_APP_SUPABASE_URL:</strong> {process.env.REACT_APP_SUPABASE_URL ? 'Set (hidden for security)' : 'Not set'}</Typography>
        <Typography><strong>REACT_APP_SUPABASE_ANON_KEY:</strong> {process.env.REACT_APP_SUPABASE_ANON_KEY ? 'Set (hidden for security)' : 'Not set'}</Typography>
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Debugging Instructions
        </Typography>
        <Typography paragraph>
          If you're seeing a white screen or experiencing issues, check the errors above for clues.
        </Typography>
        <Typography paragraph>
          <strong>Common issues:</strong>
        </Typography>
        <ul>
          <li>Missing environment variables - Check if your .env file is properly configured</li>
          <li>Supabase connection errors - Verify your API keys and URL</li>
          <li>React rendering errors - Check component syntax and dependencies</li>
          <li>Redux state issues - Look for store configuration problems</li>
        </ul>
      </Paper>
    </Container>
  );
};

export default Debug;
