import axios, { AxiosInstance, InternalAxiosRequestConfig, AxiosResponse } from 'axios';
import { supabase } from './supabase';
import config from './config';

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

// ================== Debugging Tools ==================
const DEBUG = true; // Set to false in production

// Debug logger
const debug = (message: string, ...data: any[]) => {
  if (DEBUG) {
    console.log(`[AUTH] ${message}`, ...data);
  }
};

// Error logger
const logError = (message: string, error: any) => {
  if (DEBUG) {
    console.error(`[AUTH ERROR] ${message}:`, error);
    if (error.response) {
      console.error('Status:', error.response.status);
      console.error('Data:', error.response.data);
      console.error('Headers:', error.response.headers);
    }
  }
};

export const testAuth = async (): Promise<{success: boolean, message: string, details?: any}> => {
  debug('Running auth test...');
  
  // Get current token
  const token = getAuthToken();
  debug('Current token:', token ? `${token.substring(0, 10)}...` : 'null');
  
  if (!token) {
    return {
      success: false,
      message: 'No authentication token found'
    };
  }
  
  try {
    // Test with direct fetch for maximum transparency
    const testResult = await fetch(`${config.API_URL}/me`, {
      headers: {
        'Authorization': `Bearer ${token}`
      }
    });
    
    debug('Auth test status:', testResult.status);
    
    // Check response
    if (testResult.status === 401) {
      logError('Authentication test failed', {status: testResult.status});
      return {
        success: false,
        message: 'Token not accepted by server',
        details: {
          status: testResult.status,
          statusText: testResult.statusText,
          headers: {
            'content-type': testResult.headers.get('content-type'),
            'www-authenticate': testResult.headers.get('www-authenticate')
          }
        }
      };
    }
    
    const userData = await testResult.json();
    
    return {
      success: true,
      message: 'Authentication successful',
      details: {
        status: testResult.status,
        user: userData
      }
    };
  } catch (error) {
    logError('Auth test error', error);
    return {
      success: false,
      message: 'Error testing authentication',
      details: error
    };
  }
};


// Request logger
export const logRequest = (request: any) => {
  if (!DEBUG) return;
  
  const { method, url, headers, data } = request;
  console.group(`[REQUEST] ${method?.toUpperCase()} ${url}`);
  console.log('Headers:', headers);
  if (data) console.log('Data:', data);
  console.groupEnd();
};

// Response logger  
export const logResponse = (response: any) => {
  if (!DEBUG) return;
  
  const { status, config, data, headers } = response;
  console.group(`[RESPONSE] ${status} ${config?.method?.toUpperCase()} ${config?.url}`);
  console.log('Headers:', headers);
  console.log('Data:', data);
  console.groupEnd();
};

// ================== Token Management ==================

// Simple token management
export const setAuthToken = (token: string): boolean => {
  if (!token) {
    debug('Attempted to set empty token');
    return false;
  }
  
  // Store raw token without Bearer prefix
  const cleanToken = token.replace(/^Bearer\s+/i, '');
  debug('Setting auth token:', `${cleanToken.substring(0, 10)}...`);
  
  localStorage.setItem('api_token', cleanToken);
  
  // Update axios defaults
  axios.defaults.headers.common['Authorization'] = `Bearer ${cleanToken}`;
  debug('Updated axios default headers');
  
  return true;
};

export const getAuthToken = (): string | null => {
  const token = localStorage.getItem('api_token');
  debug('Retrieved token:', token ? `${token.substring(0, 10)}...` : 'null');
  return token;
};

export const clearAuthToken = (): void => {
  debug('Clearing auth token');
  localStorage.removeItem('api_token');
  delete axios.defaults.headers.common['Authorization'];
};

// ================== API Configuration ==================

// Create a custom axios instance
const api: AxiosInstance = axios.create({
  baseURL: config.API_URL,
});

// Request interceptor for API calls
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = getAuthToken();
    if (token) {
      config.headers = config.headers || {};
      config.headers['Authorization'] = `Bearer ${token}`;
      debug(`Adding authorization header to ${config.method?.toUpperCase()} ${config.url}`);
    } else {
      debug(`No token available for request to ${config.url}`);
    }
    
    logRequest(config);
    return config;
  },
  (error) => {
    logError('Request interceptor error', error);
    return Promise.reject(error);
  }
);

// Response interceptor for API calls
api.interceptors.response.use(
  (response: AxiosResponse) => {
    logResponse(response);
    return response;
  },
  async (error) => {
    logError('Response error', error);
    
    // If we get a 401, try to refresh token
    if (error.response?.status === 401) {
      debug('Received 401, attempting token refresh...');
      
      // Store original request for retry
      const originalRequest = error.config;
      
      // Only try once to prevent infinite loops
      if (!originalRequest._retry) {
        originalRequest._retry = true;
        
        try {
          // Try to refresh token
          const refreshed = await refreshToken();
          
          if (refreshed) {
            debug('Token refresh successful, retrying request');
            
            // Update the authorization header
            const token = getAuthToken();
            if (token) {
              originalRequest.headers['Authorization'] = `Bearer ${token}`;
            }
            
            // Retry the original request
            return api(originalRequest);
          } else {
            debug('Token refresh failed, redirecting to login');
            clearAuthToken();
            window.location.href = '/login';
          }
        } catch (refreshError) {
          logError('Token refresh failed', refreshError);
          clearAuthToken();
          window.location.href = '/login';
        }
      }
    }
    
    return Promise.reject(error);
  }
);

// ================== Helper Functions ==================

// Determine if a string is a valid email
const isValidEmail = (email: string): boolean => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
};

// Attempt to refresh token
const refreshToken = async (): Promise<boolean> => {
  debug('Attempting to refresh token...');
  
  try {
    // Check if we have a Supabase session to use
    const { data } = await supabase.auth.getSession();
    
    if (data.session) {
      debug('Got Supabase session, using access token');
      setAuthToken(data.session.access_token);
      return true;
    }
    
    // Try to refresh Supabase session
    const { data: refreshData, error } = await supabase.auth.refreshSession();
    
    if (error) {
      logError('Supabase refresh failed', error);
      return false;
    }
    
    if (refreshData.session) {
      debug('Supabase session refreshed successfully');
      setAuthToken(refreshData.session.access_token);
      return true;
    }
    
    return false;
  } catch (error) {
    logError('Error refreshing token', error);
    return false;
  }
};

// ================== Auth API Functions ==================

// Login with comprehensive debugging
export const login = async (credentials: LoginCredentials): Promise<TokenResponse> => {
  debug('Login attempt:', { username: credentials.username });
  
  // Clear any existing tokens
  clearAuthToken();
  
  try {
    // Try backend API login first
    debug('Attempting login with backend API...');
    const formData = new URLSearchParams();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    // Make direct request to track exactly what's happening
    const response = await axios.post(config.AUTH.LOGIN, formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    });
    
    debug('Login response status:', response.status);
    debug('Login response data:', response.data);
    
    // Verify token in response
    if (!response.data || !response.data.access_token) {
      throw new Error('Invalid response: No access token received');
    }
    
    const apiToken = response.data.access_token;
    debug('Received API token:', apiToken.substring(0, 10) + '...');
    
    // Set the token
    setAuthToken(apiToken);
    
    // Test if token works
    const testResult = await testAuth();
    debug('Authentication test result:', testResult);
    
    // Try Supabase login as well (for redundancy)
    try {
      debug('Also logging in with Supabase...');
      const loginEmail = isValidEmail(credentials.username) 
        ? credentials.username 
        : `${credentials.username}@example.com`;
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email: loginEmail,
        password: credentials.password,
      });
      
      if (error) {
        debug('Supabase login failed:', error.message);
      } else if (data?.session) {
        debug('Supabase login successful');
        localStorage.setItem('supabase_token', data.session.access_token);
      }
    } catch (supabaseError) {
      debug('Supabase login exception:', supabaseError);
      // Continue with API token only
    }
    
    return response.data;
  } catch (error: any) {
    logError('Login error', error);
    
    // Try Supabase as fallback
    debug('API login failed, trying Supabase fallback...');
    
    try {
      const loginEmail = isValidEmail(credentials.username) 
        ? credentials.username 
        : `${credentials.username}@example.com`;
      
      const { data, error } = await supabase.auth.signInWithPassword({
        email: loginEmail,
        password: credentials.password,
      });
      
      if (error) {
        throw error;
      }
      
      if (!data || !data.session) {
        throw new Error('Empty session data from Supabase');
      }
      
      debug('Supabase login successful');
      
      // Set token from Supabase
      setAuthToken(data.session.access_token);
      localStorage.setItem('supabase_token', data.session.access_token);
      
      return {
        access_token: data.session.access_token,
        token_type: 'bearer'
      };
    } catch (supabaseError: any) {
      logError('All login attempts failed', supabaseError);
      throw new Error('Login failed. Please check your credentials and try again.');
    }
  }
};

export const register = async (data: RegisterData): Promise<UserData> => {
  debug('Registration attempt:', { email: data.email, username: data.username });
  
  if (!isValidEmail(data.email)) {
    throw new Error('Please provide a valid email address');
  }
  
  try {
    // Register with API
    debug('Registering with backend API...');
    const apiResponse = await axios.post(config.AUTH.REGISTER, data);
    debug('API registration successful');
    
    // Also register with Supabase for redundancy
    try {
      debug('Also registering with Supabase...');
      const { data: supabaseData, error } = await supabase.auth.signUp({
        email: data.email,
        password: data.password,
        options: {
          data: {
            username: data.username
          }
        }
      });
      
      if (error) {
        debug('Supabase registration failed:', error.message);
      } else {
        debug('Supabase registration successful');
      }
    } catch (supabaseError) {
      debug('Supabase registration error:', supabaseError);
    }
    
    return apiResponse.data;
  } catch (apiError: any) {
    logError('API registration failed', apiError);
    
    // Try Supabase as fallback
    debug('API registration failed, trying Supabase fallback...');
    
    try {
      const { data: supabaseData, error } = await supabase.auth.signUp({
        email: data.email,
        password: data.password,
        options: {
          data: {
            username: data.username
          }
        }
      });
      
      if (error) throw error;
      if (!supabaseData || !supabaseData.user) {
        throw new Error('Registration failed: Empty user data from Supabase');
      }
      
      debug('Supabase registration successful');
      
      // Return user data from Supabase
      return {
        id: supabaseData.user.id,
        email: supabaseData.user.email || data.email,
        username: data.username,
        is_active: true,
        is_admin: false,
        created_at: new Date().toISOString()
      };
    } catch (supabaseError: any) {
      logError('All registration attempts failed', supabaseError);
      throw new Error('Registration failed: ' + (apiError.message || 'Unknown error'));
    }
  }
};

export const getCurrentUser = async (): Promise<UserData> => {
  debug('Fetching current user...');
  
  // Verify token exists
  const token = getAuthToken();
  if (!token) {
    debug('No token found while getting current user');
    throw new Error('No authentication token found');
  }
  
  try {
    // Get user from API with explicit token
    debug('Fetching user from API...');
    const response = await axios.get(config.AUTH.ME, {
      headers: { 'Authorization': `Bearer ${token}` }
    });
    
    debug('User fetch successful');
    return response.data;
  } catch (apiError) {
    logError('API user fetch failed', apiError);
    
    // Try Supabase as fallback
    debug('Attempting to get user from Supabase...');
    
    try {
      const { data, error } = await supabase.auth.getUser();
      
      if (error) throw error;
      if (!data || !data.user) {
        throw new Error('User not found or not authenticated');
      }
      
      debug('Supabase user fetch successful');
      
      // Try to get additional profile data from Supabase
      try {
        const { data: userData, error: profileError } = await supabase
          .from('profiles')
          .select('*')
          .eq('id', data.user.id)
          .single();
        
        if (!profileError && userData) {
          return {
            id: data.user.id,
            email: data.user.email || '',
            username: userData.username || data.user.user_metadata?.username || '',
            is_active: userData.is_active !== undefined ? userData.is_active : true,
            is_admin: userData.is_admin !== undefined ? userData.is_admin : false,
            created_at: userData.created_at || data.user.created_at || new Date().toISOString()
          };
        }
      } catch (profileError) {
        debug('Failed to fetch Supabase profile, using basic user data');
      }
      
      // Return basic user data if no profile
      return {
        id: data.user.id,
        email: data.user.email || '',
        username: data.user.user_metadata?.username || '',
        is_active: true,
        is_admin: false,
        created_at: data.user.created_at || new Date().toISOString()
      };
    } catch (supabaseError) {
      logError('All user fetch attempts failed', supabaseError);
      clearAuthToken();
      throw new Error('Failed to fetch user profile. Please log in again.');
    }
  }
};

export const logout = async (): Promise<void> => {
  debug('Logging out...');
  
  // Log out from Supabase
  try {
    debug('Logging out from Supabase...');
    await supabase.auth.signOut();
    debug('Supabase logout successful');
  } catch (error) {
    debug('Supabase logout error:', error);
  }
  
  // Clear tokens
  clearAuthToken();
  localStorage.removeItem('supabase_token');
  
  debug('Logout complete');
};

export const isAuthenticated = (): boolean => {
  const token = getAuthToken();
  const authenticated = !!token;
  debug('Authentication check:', authenticated);
  return authenticated;
};

// Add global axios interceptors for all requests
axios.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers = config.headers || {};
      config.headers['Authorization'] = `Bearer ${token}`;
      
      if (DEBUG) {
        console.log(`[Global] ${config.method?.toUpperCase()} ${config.url}`, 
                   'Authorization:', `Bearer ${token.substring(0, 10)}...`);
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Debug browser environment
debug('Browser environment:', {
  localStorage: !!window.localStorage,
  fetch: !!window.fetch,
  axios: !!axios
});

// Check for existing token on module load
const existingToken = getAuthToken();
if (existingToken) {
  debug('Found existing token on load');
  // Set axios defaults
  axios.defaults.headers.common['Authorization'] = `Bearer ${existingToken}`;
}

// Export the api instance for use throughout the app
export default api;