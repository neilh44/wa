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
