// src/components/debug/AuthDebug.tsx
import React, { useState } from 'react';
import { Box, Button, Typography, Paper } from '@mui/material';
import axios from 'axios';
import config from '../../api/config';

// Define a type for the result state
interface AuthResult {
  tokenExists?: boolean;
  token?: string;
  status?: number;
  data?: any;
  message?: string;
  success?: boolean;
  error?: string;
}

const AuthDebug: React.FC = () => {
  const [result, setResult] = useState<AuthResult | null>(null);
  const [loading, setLoading] = useState(false);
  
  const testAuth = async () => {
    setLoading(true);
    
    try {
      // Get current token
      const token = localStorage.getItem('api_token');
      setResult({ tokenExists: !!token, token: token ? `${token.substring(0, 10)}...` : 'none' });
      
      if (token) {
        // Test endpoint
        try {
          const response = await axios.get(config.AUTH.ME, {
            headers: {
              'Authorization': `Bearer ${token}`
            }
          });
          
          setResult((prev: AuthResult | null) => ({ 
            ...prev || {},
            status: response.status,
            data: response.data,
            success: true
          }));
        } catch (reqError: any) {
          setResult((prev: AuthResult | null) => ({ 
            ...prev || {},
            status: reqError.response?.status,
            message: reqError.message,
            success: false
          }));
        }
      }
    } catch (error: any) {
      setResult({ error: String(error) });
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <Paper sx={{ p: 2, m: 2 }}>
      <Typography variant="h6">Authentication Debug</Typography>
      <Button 
        variant="contained" 
        onClick={testAuth}
        disabled={loading}
        sx={{ my: 2 }}
      >
        Test Auth Status
      </Button>
      
      {result && (
        <Box sx={{ p: 2, bgcolor: '#f5f5f5' }}>
          <pre>{JSON.stringify(result, null, 2)}</pre>
        </Box>
      )}
    </Paper>
  );
};

export default AuthDebug;