#!/bin/bash

# Script to add Supabase authentication to the WhatsApp to Supabase frontend
echo "Adding Supabase authentication to the frontend..."

# Navigate to the frontend directory
cd whatsapp-supabase-frontend || { echo "Frontend directory not found!"; exit 1; }

# Update auth API service
cat > src/api/auth.ts << 'EOL'
import axios from 'axios';
import config from './config';
import { supabase } from './supabase';

// Types
export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
}

export interface UserData {
  id: string;
  email: string;
  username: string;
  is_active: boolean;
  is_admin: boolean;
  created_at: string;
}

// Get token from local storage
const getToken = (): string | null => localStorage.getItem('token');

// Set auth header
const setAuthHeader = (token: string | null) => {
  if (token) {
    axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
  } else {
    delete axios.defaults.headers.common['Authorization'];
  }
};

// Initialize auth header
setAuthHeader(getToken());

// Auth API functions
export const login = async (credentials: LoginCredentials): Promise<TokenResponse> => {
  // Try to sign in with Supabase first
  try {
    const { data: supabaseData, error: supabaseError } = await supabase.auth.signInWithPassword({
      email: credentials.username,
      password: credentials.password,
    });

    if (supabaseError) throw supabaseError;

    if (supabaseData && supabaseData.session) {
      const token = supabaseData.session.access_token;
      localStorage.setItem('token', token);
      setAuthHeader(token);

      return {
        access_token: token,
        token_type: 'bearer'
      };
    }
  } catch (supabaseError) {
    console.error('Supabase login error:', supabaseError);
    // Fall back to backend API if Supabase fails
  }

  // Fall back to our backend API
  const formData = new URLSearchParams();
  formData.append('username', credentials.username);
  formData.append('password', credentials.password);

  const response = await axios.post(config.AUTH.LOGIN, formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });

  const token = response.data.access_token;
  localStorage.setItem('token', token);
  setAuthHeader(token);

  return response.data;
};

export const register = async (data: RegisterData): Promise<UserData> => {
  // First register with Supabase
  try {
    const { error: signUpError } = await supabase.auth.signUp({
      email: data.email,
      password: data.password,
      options: {
        data: {
          username: data.username
        }
      }
    });

    if (signUpError) throw signUpError;

    // Now register with our backend to keep both systems in sync
    const response = await axios.post(config.AUTH.REGISTER, data);
    return response.data;
  } catch (error: any) {
    console.error('Registration error:', error);
    throw error;
  }
};

export const getCurrentUser = async (): Promise<UserData> => {
  // Try to get user from Supabase first
  try {
    const { data: supabaseData, error: supabaseError } = await supabase.auth.getUser();
    
    if (supabaseError) throw supabaseError;
    
    if (supabaseData && supabaseData.user) {
      // Still get user details from backend to ensure we have all fields
      const token = getToken();
      if (!token) {
        throw new Error('No authentication token found');
      }
      
      setAuthHeader(token);
      const response = await axios.get(config.AUTH.ME);
      return response.data;
    }
  } catch (supabaseError) {
    console.error('Supabase get user error:', supabaseError);
    // Fall back to backend API
  }
  
  // Fall back to our backend API
  const token = getToken();
  
  if (!token) {
    throw new Error('No authentication token found');
  }
  
  setAuthHeader(token);
  const response = await axios.get(config.AUTH.ME);
  return response.data;
};

export const logout = async (): Promise<void> => {
  // Sign out from Supabase
  try {
    await supabase.auth.signOut();
  } catch (error) {
    console.error('Supabase logout error:', error);
  }
  
  // Clear local storage and headers
  localStorage.removeItem('token');
  setAuthHeader(null);
};
EOL

# Update Redux auth slice
cat > src/store/slices/authSlice.ts << 'EOL'
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { login as loginApi, register as registerApi, getCurrentUser, logout as logoutApi, LoginCredentials, RegisterData, UserData } from '../../api/auth';
import { supabase } from '../../api/supabase';

interface AuthState {
  user: UserData | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
  registrationSuccess: boolean;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: localStorage.getItem('token') ? true : false,
  loading: false,
  error: null,
  registrationSuccess: false
};

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      await loginApi(credentials);
      const user = await getCurrentUser();
      return user;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || error.message || 'Login failed');
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (data: RegisterData, { rejectWithValue }) => {
    try {
      return await registerApi(data);
    } catch (error: any) {
      // Handle Supabase specific errors
      if (error.code) {
        switch (error.code) {
          case 'user-already-exists':
            return rejectWithValue('User with this email already exists');
          case 'weak-password':
            return rejectWithValue('Password is too weak');
          default:
            return rejectWithValue(error.message || 'Registration failed');
        }
      }
      return rejectWithValue(error.response?.data?.detail || error.message || 'Registration failed');
    }
  }
);

export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      // First check if we have a valid Supabase session
      const { data: sessionData } = await supabase.auth.getSession();
      
      if (!sessionData.session) {
        throw new Error('No valid session found');
      }
      
      return await getCurrentUser();
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || error.message || 'Failed to fetch user');
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async () => {
    await logoutApi();
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    clearRegistrationSuccess: (state) => {
      state.registrationSuccess = false;
    }
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action: PayloadAction<UserData>) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Register
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
        state.registrationSuccess = false;
      })
      .addCase(register.fulfilled, (state) => {
        state.loading = false;
        state.registrationSuccess = true;
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
        state.registrationSuccess = false;
      })
      // Fetch current user
      .addCase(fetchCurrentUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action: PayloadAction<UserData>) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload;
      })
      .addCase(fetchCurrentUser.rejected, (state, action) => {
        state.loading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.error = action.payload as string;
      })
      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.isAuthenticated = false;
        state.user = null;
      });
  },
});

export const { clearError, clearRegistrationSuccess } = authSlice.actions;
export default authSlice.reducer;
EOL

# Update SignupForm
cat > src/components/auth/SignupForm.tsx << 'EOL'
import React, { useState, useEffect } from 'react';
import { TextField, Box, Typography, Alert, Link, Snackbar } from '@mui/material';
import { useDispatch, useSelector } from 'react-redux';
import { register, clearError, clearRegistrationSuccess } from '../../store/slices/authSlice';
import { AppDispatch, RootState } from '../../store';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import Button from '../common/Button';

const SignupForm: React.FC = () => {
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [formErrors, setFormErrors] = useState({
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  });
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();
  const { loading, error, registrationSuccess } = useSelector((state: RootState) => state.auth);
  const [successOpen, setSuccessOpen] = useState(false);

  useEffect(() => {
    if (registrationSuccess) {
      setSuccessOpen(true);
      // Reset form
      setFormData({
        email: '',
        username: '',
        password: '',
        confirmPassword: '',
      });
      
      // Navigate to login after short delay
      const timer = setTimeout(() => {
        dispatch(clearRegistrationSuccess());
        navigate('/login');
      }, 3000);
      
      return () => clearTimeout(timer);
    }
  }, [registrationSuccess, dispatch, navigate]);

  const validateForm = (): boolean => {
    let isValid = true;
    const newErrors = {
      email: '',
      username: '',
      password: '',
      confirmPassword: '',
    };

    // Email validation
    if (!formData.email) {
      newErrors.email = 'Email is required';
      isValid = false;
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = 'Email is invalid';
      isValid = false;
    }

    // Username validation
    if (!formData.username) {
      newErrors.username = 'Username is required';
      isValid = false;
    } else if (formData.username.length < 3) {
      newErrors.username = 'Username must be at least 3 characters';
      isValid = false;
    }

    // Password validation
    if (!formData.password) {
      newErrors.password = 'Password is required';
      isValid = false;
    } else if (formData.password.length < 6) {
      newErrors.password = 'Password must be at least 6 characters';
      isValid = false;
    }

    // Confirm password validation
    if (formData.password !== formData.confirmPassword) {
      newErrors.confirmPassword = 'Passwords do not match';
      isValid = false;
    }

    setFormErrors(newErrors);
    return isValid;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
    ...formData,
      [name]: value,
    });
    
    // Clear the error for this field
    if (formErrors[name as keyof typeof formErrors]) {
      setFormErrors({
        ...formErrors,
        [name]: '',
      });
    }
    
    if (error) {
      dispatch(clearError());
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      const { confirmPassword, ...registerData } = formData;
      dispatch(register(registerData));
    }
  };

  const handleCloseSuccess = () => {
    setSuccessOpen(false);
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%', maxWidth: 400 }}>
      <Typography variant="h5" component="h1" gutterBottom>
        Create Account
      </Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      <TextField
        margin="normal"
        required
        fullWidth
        id="email"
        label="Email Address"
        name="email"
        autoComplete="email"
        autoFocus
        value={formData.email}
        onChange={handleChange}
        error={!!formErrors.email}
        helperText={formErrors.email}
      />
      
      <TextField
        margin="normal"
        required
        fullWidth
        id="username"
        label="Username"
        name="username"
        autoComplete="username"
        value={formData.username}
        onChange={handleChange}
        error={!!formErrors.username}
        helperText={formErrors.username}
      />
      
      <TextField
        margin="normal"
        required
        fullWidth
        name="password"
        label="Password"
        type="password"
        id="password"
        autoComplete="new-password"
        value={formData.password}
        onChange={handleChange}
        error={!!formErrors.password}
        helperText={formErrors.password}
      />
      
      <TextField
        margin="normal"
        required
        fullWidth
        name="confirmPassword"
        label="Confirm Password"
        type="password"
        id="confirmPassword"
        autoComplete="new-password"
        value={formData.confirmPassword}
        onChange={handleChange}
        error={!!formErrors.confirmPassword}
        helperText={formErrors.confirmPassword}
      />
      
      <Button
        type="submit"
        fullWidth
        variant="contained"
        sx={{ mt: 3, mb: 2 }}
        loading={loading}
      >
        Sign Up
      </Button>
      
      <Box sx={{ textAlign: 'center', mt: 2 }}>
        <Typography variant="body2">
          Already have an account?{' '}
          <Link component={RouterLink} to="/login" variant="body2">
            Sign in
          </Link>
        </Typography>
      </Box>

      <Snackbar
        open={successOpen}
        autoHideDuration={3000}
        onClose={handleCloseSuccess}
        message="Registration successful! Redirecting to login..."
      />
    </Box>
  );
};

export default SignupForm;
EOL

# Add helper function to ensure Supabase authentication is initialized properly
cat > src/utils/supabaseHelpers.ts << 'EOL'
import { supabase } from '../api/supabase';
import { store } from '../store';
import { fetchCurrentUser, logout } from '../store/slices/authSlice';

// Initialize Supabase auth state
export const initializeSupabaseAuth = async () => {
  // Check if there's an active session
  const { data } = await supabase.auth.getSession();
  
  if (data.session) {
    // If there's a session, try to fetch the current user
    store.dispatch(fetchCurrentUser());
  }
  
  // Listen for auth state changes
  supabase.auth.onAuthStateChange((event, session) => {
    if (event === 'SIGNED_IN') {
      // User signed in, fetch user data
      store.dispatch(fetchCurrentUser());
    } else if (event === 'SIGNED_OUT') {
      // User signed out
      store.dispatch(logout());
    } else if (event === 'TOKEN_REFRESHED') {
      // Token was refreshed, update local storage
      if (session) {
        localStorage.setItem('token', session.access_token);
      }
    }
  });
};
EOL

# Update index.tsx to initialize Supabase auth on app start
cat > src/index.tsx << 'EOL'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { store } from './store';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import { initializeSupabaseAuth } from './utils/supabaseHelpers';
import './index.css';

// Initialize Supabase auth state
initializeSupabaseAuth();

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <Provider store={store}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Provider>
  </React.StrictMode>
);
EOL

# Create an email verification page
mkdir -p src/pages
cat > src/pages/VerifyEmail.tsx << 'EOL'
import React, { useEffect, useState } from 'react';
import { Box, Container, Paper, Typography, Alert, CircularProgress } from '@mui/material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { supabase } from '../api/supabase';

const VerifyEmail: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Verifying your email...');
  const navigate = useNavigate();

  useEffect(() => {
    const verifyEmail = async () => {
      try {
        // Get the token from the URL
        const token = searchParams.get('token');
        const type = searchParams.get('type');
        
        if (!token || type !== 'email_verification') {
          setStatus('error');
          setMessage('Invalid or missing verification parameters');
          return;
        }
        
        // Verify the token with Supabase
        const { error } = await supabase.auth.verifyOtp({
          token_hash: token,
          type: 'email',
        });
        
        if (error) {
          setStatus('error');
          setMessage(error.message);
        } else {
          setStatus('success');
          setMessage('Email verified successfully! Redirecting to login...');
          
          // Redirect to login after a delay
          setTimeout(() => {
            navigate('/login');
          }, 3000);
        }
      } catch (error: any) {
        setStatus('error');
        setMessage(error.message || 'An error occurred during verification');
      }
    };
    
    verifyEmail();
  }, [searchParams, navigate]);

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
              Email Verification
            </Typography>
          </Box>
          
          {status === 'loading' && (
            <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
              <CircularProgress />
            </Box>
          )}
          
          <Alert severity={status === 'success' ? 'success' : status === 'error' ? 'error' : 'info'}>
            {message}
          </Alert>
        </Paper>
      </Box>
    </Container>
  );
};

export default VerifyEmail;
EOL

# Update App.tsx to include the email verification route
cat > src/App.tsx << 'EOL'
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import Login from './pages/Login';
import Signup from './pages/Signup';
import VerifyEmail from './pages/VerifyEmail';
import Dashboard from './pages/Dashboard';
import Files from './pages/Files';
import Settings from './pages/Settings';
import { RootState } from './store';
import MainLayout from './components/common/MainLayout';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#25D366', // WhatsApp green
    },
    secondary: {
      main: '#34B7F1', // WhatsApp blue
    },
  },
});

const App: React.FC = () => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Routes>
        <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
        <Route path="/signup" element={!isAuthenticated ? <Signup /> : <Navigate to="/" />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/" element={isAuthenticated ? <MainLayout /> : <Navigate to="/login" />}>
          <Route index element={<Dashboard />} />
          <Route path="files" element={<Files />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </ThemeProvider>
  );
};

export default App;
EOL

# Create reset password components
cat > src/pages/ResetPassword.tsx << 'EOL'
import React, { useState } from 'react';
import { Box, Container, Paper, Typography, TextField, Alert } from '@mui/material';
import { supabase } from '../api/supabase';
import Button from '../components/common/Button';

const ResetPassword: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setMessage({ type: 'error', text: 'Please enter your email address' });
      return;
    }
    
    setLoading(true);
    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/update-password`,
      });
      
      if (error) {
        throw error;
      }
      
      setMessage({ 
        type: 'success', 
        text: 'Password reset link sent! Check your email inbox.' 
      });
      setEmail('');
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.message || 'An error occurred. Please try again.' 
      });
    } finally {
      setLoading(false);
    }
  };

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
              Reset Password
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              Enter your email address to receive a password reset link
            </Typography>
          </Box>
          
          {message && (
            <Alert 
              severity={message.type} 
              sx={{ mb: 2 }}
              onClose={() => setMessage(null)}
            >
              {message.text}
            </Alert>
          )}
          
          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              id="email"
              label="Email Address"
              name="email"
              autoComplete="email"
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              loading={loading}
            >
              Send Reset Link
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default ResetPassword;
EOL

# Create update password page (after reset)
cat > src/pages/UpdatePassword.tsx << 'EOL'
import React, { useState, useEffect } from 'react';
import { Box, Container, Paper, Typography, TextField, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../api/supabase';
import Button from '../components/common/Button';

const UpdatePassword: React.FC = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info', text: string } | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    // Check if we're in a password reset flow
    const checkSession = async () => {
      const { data, error } = await supabase.auth.getSession();
      
      if (error || !data.session) {
        setMessage({ 
          type: 'error', 
          text: 'Invalid or expired password reset session. Please try again.' 
        });
      }
    };
    
    checkSession();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (password.length < 6) {
      setMessage({ type: 'error', text: 'Password must be at least 6 characters long' });
      return;
    }
    
    if (password !== confirmPassword) {
      setMessage({ type: 'error', text: 'Passwords do not match' });
      return;
    }
    
    setLoading(true);
    try {
      const { error } = await supabase.auth.updateUser({
        password,
      });
      
      if (error) {
        throw error;
      }
      
      setMessage({ 
        type: 'success', 
        text: 'Password updated successfully! Redirecting to login...' 
      });
      
      // Redirect to login after a delay
      setTimeout(() => {
        navigate('/login');
      }, 3000);
    } catch (error: any) {
      setMessage({ 
        type: 'error', 
        text: error.message || 'Failed to update password. Please try again.' 
      });
    } finally {
      setLoading(false);
    }
  };

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
              Update Password
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              Please enter your new password
            </Typography>
          </Box>
          
          {message && (
            <Alert 
              severity={message.type} 
              sx={{ mb: 2 }}
              onClose={() => message.type !== 'success' && setMessage(null)}
            >
              {message.text}
            </Alert>
          )}
          
          <Box component="form" onSubmit={handleSubmit} sx={{ mt: 1 }}>
            <TextField
              margin="normal"
              required
              fullWidth
              name="password"
              label="New Password"
              type="password"
              id="password"
              autoComplete="new-password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            
            <TextField
              margin="normal"
              required
              fullWidth
              name="confirmPassword"
              label="Confirm New Password"
              type="password"
              id="confirmPassword"
              autoComplete="new-password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
            />
            
            <Button
              type="submit"
              fullWidth
              variant="contained"
              sx={{ mt: 3, mb: 2 }}
              loading={loading}
              disabled={!!message?.type === 'success'}
            >
              Update Password
            </Button>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default UpdatePassword;
EOL

# Update App.tsx to include reset password routes
cat > src/App.tsx << 'EOL'
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import Login from './pages/Login';
import Signup from './pages/Signup';
import VerifyEmail from './pages/VerifyEmail';
import ResetPassword from './pages/ResetPassword';
import UpdatePassword from './pages/UpdatePassword';
import Dashboard from './pages/Dashboard';
import Files from './pages/Files';
import Settings from './pages/Settings';
import { RootState } from './store';
import MainLayout from './components/common/MainLayout';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#25D366', // WhatsApp green
    },
    secondary: {
      main: '#34B7F1', // WhatsApp blue
    },
  },
});

const App: React.FC = () => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Routes>
        <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
        <Route path="/signup" element={!isAuthenticated ? <Signup /> : <Navigate to="/" />} />
        <Route path="/verify-email" element={<VerifyEmail />} />
        <Route path="/reset-password" element={!isAuthenticated ? <ResetPassword /> : <Navigate to="/" />} />
        <Route path="/update-password" element={<UpdatePassword />} />
        <Route path="/" element={isAuthenticated ? <MainLayout /> : <Navigate to="/login" />}>
          <Route index element={<Dashboard />} />
          <Route path="files" element={<Files />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </ThemeProvider>
  );
};

export default App;
EOL

# Update LoginForm to include forgot password link
cat > src/components/auth/LoginForm.tsx << 'EOL'
import React, { useState } from 'react';
import { TextField, Box, Typography, Alert, Link, Grid } from '@mui/material';
import { useDispatch, useSelector } from 'react-redux';
import { Link as RouterLink } from 'react-router-dom';
import { login, clearError } from '../../store/slices/authSlice';
import { AppDispatch, RootState } from '../../store';
import Button from '../common/Button';

const LoginForm: React.FC = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const dispatch = useDispatch<AppDispatch>();
  const { loading, error } = useSelector((state: RootState) => state.auth);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
    if (error) {
      dispatch(clearError());
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    dispatch(login(formData));
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%', maxWidth: 400 }}>
      <Typography variant="h5" component="h1" gutterBottom>
        Login
      </Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      <TextField
        margin="normal"
        required
        fullWidth
        id="username"
        label="Email Address"
        name="username"
        autoComplete="email"
        autoFocus
        value={formData.username}
        onChange={handleChange}
      />
      
      <TextField
        margin="normal"
        required
        fullWidth
        name="password"
        label="Password"
        type="password"
        id="password"
        autoComplete="current-password"
        value={formData.password}
        onChange={handleChange}
      />
      
      <Box sx={{ textAlign: 'right', mt: 1 }}>
        <Link component={RouterLink} to="/reset-password" variant="body2">
          Forgot password?
        </Link>
      </Box>
      
      <Button
        type="submit"
        fullWidth
        variant="contained"
        sx={{ mt: 3, mb: 2 }}
        loading={loading}
      >
        Sign In
      </Button>
      
      <Box sx={{ textAlign: 'center', mt: 2 }}>
        <Typography variant="body2">
          Don't have an account?{' '}
          <Link component={RouterLink} to="/signup" variant="body2">
            Sign up
          </Link>
        </Typography>
      </Box>
    </Box>
  );
};

export default LoginForm;
EOL

echo "Supabase authentication successfully integrated!"
