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
  try {
    // Use backend-only authentication and remove direct Supabase auth
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);

    const response = await axios.post(config.AUTH.LOGIN, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });

    const token = response.data.access_token;
    
    if (!token) {
      throw new Error('No token received from server');
    }
    
    localStorage.setItem('token', token);
    setAuthHeader(token);

    return response.data;
  } catch (error) {
    console.error('Login error:', error);
    throw error;
  }
};

export const register = async (data: RegisterData): Promise<UserData> => {
  try {
    const response = await axios.post(config.AUTH.REGISTER, data);
    return response.data;
  } catch (error) {
    console.error('Registration error:', error);
    throw error;
  }
};

export const getCurrentUser = async (): Promise<UserData> => {
  const token = getToken();
  
  if (!token) {
    throw new Error('No authentication token found');
  }
  
  setAuthHeader(token);
  
  try {
    const response = await axios.get(config.AUTH.ME);
    return response.data;
  } catch (error) {
    console.error('Error getting current user:', error);
    // Clear token if it's invalid
    if (axios.isAxiosError(error) && error.response?.status === 401) {
      localStorage.removeItem('token');
      setAuthHeader(null);
    }
    throw error;
  }
};

export const logout = (): void => {
  localStorage.removeItem('token');
  setAuthHeader(null);
};
