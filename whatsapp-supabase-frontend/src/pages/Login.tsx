import React from 'react';
import { Box, Container, Paper, Typography } from '@mui/material';
import LoginForm from '../components/auth/LoginForm';

const Login: React.FC = () => {
  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              mb: 4,
            }}
          >
            <Typography component="h1" variant="h4" align="center" gutterBottom>
              WhatsApp to Supabase
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              File Management System
            </Typography>
          </Box>
          <LoginForm />
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;
