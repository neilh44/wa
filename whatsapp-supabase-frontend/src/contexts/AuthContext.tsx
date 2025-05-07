import React, { createContext, useState, useContext, useEffect } from 'react';
import axios from 'axios';
import { supabase } from '../api/supabase'; // Import your Supabase client

interface AuthContextType {
  token: string | null;
  user: any | null;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  loading: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(!!token);

  const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

  // Set up axios with the token - this ensures all API requests include the token
  useEffect(() => {
    if (token) {
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
      console.log('Set Authorization header with token');
    } else {
      delete axios.defaults.headers.common['Authorization'];
      console.log('Removed Authorization header');
    }
  }, [token]);

  // Load user profile if token exists
  useEffect(() => {
    const loadUserProfile = async () => {
      if (!token) return;

      try {
        setLoading(true);
        console.log('Loading user profile...');
        
        // Try to get user from Supabase first
        const { data: supabaseUser, error: supabaseError } = await supabase.auth.getUser();
        
        if (supabaseUser?.user) {
          console.log('Got user from Supabase:', supabaseUser.user);
          setUser(supabaseUser.user);
          setIsAuthenticated(true);
          setError(null);
        } else {
          // Fallback to FastAPI endpoint
          console.log('Falling back to API /me endpoint');
          try {
            const response = await axios.get(`${API_URL}/me`);
            console.log('API user response:', response.data);
            setUser(response.data);
            setIsAuthenticated(true);
            setError(null);
          } catch (apiError) {
            console.error('API user fetch failed:', apiError);
            // If token is invalid, clear it
            if (axios.isAxiosError(apiError) && apiError.response?.status === 401) {
              console.warn('Invalid token, logging out');
              logout();
            }
          }
        }
      } catch (err) {
        console.error('Failed to load user profile:', err);
        // If token is invalid, clear it
        if (axios.isAxiosError(err) && err.response?.status === 401) {
          logout();
        }
      } finally {
        setLoading(false);
      }
    };

    if (token) {
      loadUserProfile();
    }
  }, [token]);

  // Listen for Supabase auth changes
  useEffect(() => {
    const { data: authListener } = supabase.auth.onAuthStateChange(
      async (event, session) => {
        console.log('Supabase auth state changed:', event);
        
        if (event === 'SIGNED_IN' && session) {
          console.log('User signed in via Supabase');
          const supabaseToken = session.access_token;
          
          // Store the token
          localStorage.setItem('token', supabaseToken);
          setToken(supabaseToken);
          setUser(session.user);
          setIsAuthenticated(true);
          
          // Get a JWT token from your FastAPI backend
          try {
            // You may need to exchange the Supabase token for a FastAPI token
            // This depends on your backend implementation
            const response = await axios.post(`${API_URL}/token`, { supabase_token: supabaseToken });
            if (response.data.access_token) {
              localStorage.setItem('token', response.data.access_token);
              setToken(response.data.access_token);
              console.log('Exchanged Supabase token for API token');
            }
          } catch (err) {
            console.error('Failed to exchange token:', err);
          }
        } else if (event === 'SIGNED_OUT') {
          console.log('User signed out via Supabase');
          logout();
        }
      }
    );

    return () => {
      authListener.subscription.unsubscribe();
    };
  }, []);

  const login = async (email: string, password: string) => {
    try {
      setLoading(true);
      setError(null);
      console.log('Attempting login...');

      // Try Supabase login first
      const { data: supabaseData, error: supabaseError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });

      if (supabaseError) {
        console.error('Supabase login failed:', supabaseError);
        
        // Fallback to FastAPI login
        console.log('Falling back to API login');
        try {
          // FastAPI expects form data for login
          const formData = new URLSearchParams();
          formData.append('username', email);
          formData.append('password', password);

          const response = await axios.post(`${API_URL}/login`, formData, {
            headers: {
              'Content-Type': 'application/x-www-form-urlencoded',
            },
          });

          const newToken = response.data.access_token;
          localStorage.setItem('token', newToken);
          setToken(newToken);
          
          // Fetch user profile
          const userResponse = await axios.get(`${API_URL}/me`, {
            headers: {
              Authorization: `Bearer ${newToken}`,
            },
          });
          
          setUser(userResponse.data);
          setIsAuthenticated(true);
          console.log('API login successful');
        } catch (apiError) {
          console.error('API login failed:', apiError);
          if (axios.isAxiosError(apiError)) {
            setError(apiError.response?.data?.detail || 'Invalid credentials');
          } else {
            setError('An unexpected error occurred');
          }
          setIsAuthenticated(false);
          throw apiError;
        }
      } else {
        // Supabase login successful
        console.log('Supabase login successful');
        const supabaseToken = supabaseData.session?.access_token;
        
        if (supabaseToken) {
          localStorage.setItem('token', supabaseToken);
          setToken(supabaseToken);
          setUser(supabaseData.user);
          setIsAuthenticated(true);
          
          // Exchange Supabase token for API token if needed
          try {
            // This depends on your backend implementation
            const response = await axios.post(`${API_URL}/token`, { supabase_token: supabaseToken });
            if (response.data.access_token) {
              localStorage.setItem('token', response.data.access_token);
              setToken(response.data.access_token);
              console.log('Exchanged Supabase token for API token');
            }
          } catch (err) {
            console.error('Failed to exchange token but login successful:', err);
          }
        } else {
          setError('Login successful but no token received');
          setIsAuthenticated(false);
        }
      }
    } catch (err) {
      console.error('Login process failed:', err);
      if (axios.isAxiosError(err)) {
        setError(err.response?.data?.detail || 'Invalid credentials');
      } else {
        setError('An unexpected error occurred');
      }
      setIsAuthenticated(false);
    } finally {
      setLoading(false);
    }
  };

  const logout = () => {
    // Supabase signout
    supabase.auth.signOut().then(() => {
      console.log('Signed out from Supabase');
    }).catch(err => {
      console.error('Error signing out from Supabase:', err);
    });
    
    // Clean up local state
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    delete axios.defaults.headers.common['Authorization'];
    console.log('Logged out and cleaned up state');
  };

  return (
    <AuthContext.Provider
      value={{
        token,
        user,
        isAuthenticated,
        login,
        logout,
        loading,
        error,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;