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
    </Container>
  );
};

export default Debug;
