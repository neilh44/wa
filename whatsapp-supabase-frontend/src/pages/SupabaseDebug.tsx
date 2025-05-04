import React, { useState, useEffect } from 'react';
import { Box, Container, Typography, Paper, Button, TextField, Alert } from '@mui/material';
import { supabase } from '../api/supabase';

const SupabaseDebug: React.FC = () => {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [connectionStatus, setConnectionStatus] = useState<string>('Checking...');
  const [message, setMessage] = useState<string>('');
  const [session, setSession] = useState<any>(null);
  const [testEmail, setTestEmail] = useState<string>('');
  const [testPassword, setTestPassword] = useState<string>('');

  useEffect(() => {
    checkSupabaseConnection();
    checkSession();
  }, []);

  const checkSupabaseConnection = async () => {
    try {
      setConnectionStatus('Checking connection...');
      // A simple query to check if we can connect to Supabase
      const { data, error } = await supabase.from('_not_a_real_table_').select('*').limit(1);
      
      if (error && error.code === 'PGRST116') {
        // This is actually good - it means we connected but the table doesn't exist
        setConnectionStatus('Connected to Supabase successfully!');
      } else if (error) {
        setConnectionStatus(`Connection error: ${error.message}`);
      } else {
        setConnectionStatus('Connected to Supabase successfully!');
      }
    } catch (err: any) {
      setConnectionStatus(`Connection failed: ${err.message}`);
    }
  };

  const checkSession = async () => {
    try {
      const { data, error } = await supabase.auth.getSession();
      if (error) {
        console.error('Session error:', error);
      } else {
        setSession(data.session);
      }
    } catch (err) {
      console.error('Session check failed:', err);
    }
  };

  const testSignIn = async () => {
    if (!testEmail || !testPassword) {
      setMessage('Please enter both email and password');
      setStatus('error');
      return;
    }

    setStatus('loading');
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email: testEmail,
        password: testPassword,
      });

      if (error) {
        setMessage(`Sign in error: ${error.message}`);
        setStatus('error');
      } else {
        setMessage('Sign in successful!');
        setStatus('success');
        setSession(data.session);
      }
    } catch (err: any) {
      setMessage(`Sign in exception: ${err.message}`);
      setStatus('error');
    }
  };

  const handleSignOut = async () => {
    setStatus('loading');
    try {
      const { error } = await supabase.auth.signOut();
      
      if (error) {
        setMessage(`Sign out error: ${error.message}`);
        setStatus('error');
      } else {
        setMessage('Signed out successfully');
        setStatus('success');
        setSession(null);
      }
    } catch (err: any) {
      setMessage(`Sign out exception: ${err.message}`);
      setStatus('error');
    }
  };

  return (
    <Container>
      <Typography variant="h4" component="h1" gutterBottom sx={{ mt: 4 }}>
        Supabase Debugging
      </Typography>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Connection Status
        </Typography>
        <Typography color={connectionStatus.includes('error') || connectionStatus.includes('failed') ? 'error' : 'success'}>
          {connectionStatus}
        </Typography>
        <Button variant="outlined" sx={{ mt: 2 }} onClick={checkSupabaseConnection}>
          Recheck Connection
        </Button>
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Current Session
        </Typography>
        {session ? (
          <Box>
            <Typography><strong>User ID:</strong> {session.user?.id}</Typography>
            <Typography><strong>Email:</strong> {session.user?.email}</Typography>
            <Typography><strong>Token expires:</strong> {new Date(session.expires_at * 1000).toLocaleString()}</Typography>
            <Button variant="contained" color="secondary" sx={{ mt: 2 }} onClick={handleSignOut}>
              Sign Out
            </Button>
          </Box>
        ) : (
          <Typography>No active session found.</Typography>
        )}
      </Paper>

      <Paper elevation={3} sx={{ p: 3, mb: 4 }}>
        <Typography variant="h6" gutterBottom>
          Test Authentication
        </Typography>
        
        {status !== 'idle' && (
          <Alert severity={status === 'success' ? 'success' : status === 'error' ? 'error' : 'info'} sx={{ mb: 2 }}>
            {message}
          </Alert>
        )}
        
        <TextField
          label="Email"
          variant="outlined"
          fullWidth
          margin="normal"
          value={testEmail}
          onChange={(e) => setTestEmail(e.target.value)}
        />
        
        <TextField
          label="Password"
          variant="outlined"
          fullWidth
          margin="normal"
          type="password"
          value={testPassword}
          onChange={(e) => setTestPassword(e.target.value)}
        />
        
        <Button 
          variant="contained" 
          color="primary" 
          sx={{ mt: 2 }}
          onClick={testSignIn}
          disabled={status === 'loading'}
        >
          {status === 'loading' ? 'Testing...' : 'Test Sign In'}
        </Button>
      </Paper>
    </Container>
  );
};

export default SupabaseDebug;
