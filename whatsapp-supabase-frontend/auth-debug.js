// auth-debug.js - Authentication Debugging Script

import axios from 'axios';
import config from './config'; // Your API config

// Colors for console output
const colors = {
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  reset: '\x1b[0m'
};

// Logging helper
const log = {
  success: (msg) => console.log(`${colors.green}✓ ${msg}${colors.reset}`),
  error: (msg) => console.log(`${colors.red}✗ ${msg}${colors.reset}`),
  info: (msg) => console.log(`${colors.blue}ℹ ${msg}${colors.reset}`),
  warn: (msg) => console.log(`${colors.yellow}⚠ ${msg}${colors.reset}`),
  separator: () => console.log('-'.repeat(60))
};

// Debug functions
const tokenTests = {
  async checkTokenStorage() {
    log.info("Checking token storage...");
    
    const apiToken = localStorage.getItem('api_token');
    const supabaseToken = localStorage.getItem('supabase_token');
    
    if (apiToken) {
      log.success(`API token exists: ${apiToken.substring(0, 10)}...`);
    } else {
      log.error("API token not found in localStorage");
    }
    
    if (supabaseToken) {
      log.success(`Supabase token exists: ${supabaseToken.substring(0, 10)}...`);
    } else {
      log.warn("Supabase token not found in localStorage");
    }
    
    return { apiToken, supabaseToken };
  },
  
  decodeJwt(token) {
    try {
      log.info("Decoding JWT token...");
      const base64Url = token.split('.')[1];
      const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
      const jsonPayload = decodeURIComponent(atob(base64).split('').map(function(c) {
        return '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2);
      }).join(''));
      
      const payload = JSON.parse(jsonPayload);
      log.success("Token successfully decoded");
      
      // Check expiration
      if (payload.exp) {
        const expDate = new Date(payload.exp * 1000);
        const now = new Date();
        
        if (expDate > now) {
          log.success(`Token expiration: ${expDate.toISOString()} (valid)`);
        } else {
          log.error(`Token expired at: ${expDate.toISOString()}`);
        }
      }
      
      return payload;
    } catch (e) {
      log.error(`Failed to decode token: ${e.message}`);
      return null;
    }
  }
};

const apiTests = {
  async testEndpoint(endpoint, method = 'GET', data = null) {
    log.info(`Testing ${method} request to ${endpoint}...`);
    
    try {
      const token = localStorage.getItem('api_token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      
      // Capture request details
      const requestDetails = {
        method,
        url: endpoint,
        headers
      };
      
      if (data && method !== 'GET') {
        requestDetails.data = data;
      }
      
      log.info(`Request details: ${JSON.stringify(requestDetails)}`);
      
      // Make the request
      let response;
      if (method === 'GET') {
        response = await axios.get(endpoint, { headers });
      } else if (method === 'POST') {
        response = await axios.post(endpoint, data, { headers });
      }
      
      log.success(`${endpoint} responded with status ${response.status}`);
      return { success: true, status: response.status, data: response.data };
    } catch (error) {
      log.error(`${endpoint} failed: ${error.message}`);
      
      if (error.response) {
        log.error(`Response status: ${error.response.status}`);
        log.error(`Response data: ${JSON.stringify(error.response.data)}`);
        
        const requestHeaders = error.config.headers;
        log.info(`Request headers: ${JSON.stringify(requestHeaders)}`);
        
        // Check if Authorization header is present and correctly formatted
        if (requestHeaders) {
          const authHeader = requestHeaders.Authorization || requestHeaders.authorization;
          if (!authHeader) {
            log.error("No Authorization header sent with the request");
          } else if (!authHeader.startsWith('Bearer ')) {
            log.error("Authorization header does not use 'Bearer' scheme");
          }
        }
      }
      
      return { 
        success: false, 
        status: error.response?.status,
        error: error.message,
        data: error.response?.data
      };
    }
  },
  
  async testLogin(credentials) {
    log.info("Testing login...");
    
    try {
      const formData = new URLSearchParams();
      formData.append('username', credentials.username);
      formData.append('password', credentials.password);
      
      const response = await axios.post(config.AUTH.LOGIN, formData, {
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
      });
      
      log.success("Login successful");
      
      if (response.data && response.data.access_token) {
        log.success(`Received token: ${response.data.access_token.substring(0, 10)}...`);
        localStorage.setItem('api_token', response.data.access_token);
      } else {
        log.error("No access token in login response");
      }
      
      return { success: true, data: response.data };
    } catch (error) {
      log.error(`Login failed: ${error.message}`);
      return { success: false, error: error.message };
    }
  }
};

const networkTests = {
  async checkCors() {
    log.info("Testing CORS configuration...");
    
    try {
      // Make an OPTIONS request to the API
      const response = await axios({
        method: 'OPTIONS',
        url: config.AUTH.ME,
        headers: {
          'Access-Control-Request-Method': 'GET',
          'Access-Control-Request-Headers': 'authorization',
          'Origin': window.location.origin
        }
      });
      
      log.success("CORS pre-flight request succeeded");
      
      // Check CORS headers
      const corsHeaders = {
        'Access-Control-Allow-Origin': response.headers['access-control-allow-origin'],
        'Access-Control-Allow-Methods': response.headers['access-control-allow-methods'],
        'Access-Control-Allow-Headers': response.headers['access-control-allow-headers'],
        'Access-Control-Allow-Credentials': response.headers['access-control-allow-credentials']
      };
      
      log.info(`CORS Headers: ${JSON.stringify(corsHeaders)}`);
      
      return { success: true, corsHeaders };
    } catch (error) {
      log.error(`CORS check failed: ${error.message}`);
      return { success: false, error: error.message };
    }
  }
};

// Main diagnostics function
async function runAuthDiagnostics() {
  log.separator();
  log.info("STARTING AUTHENTICATION DIAGNOSTICS");
  log.separator();
  
  // 1. Check token storage
  const { apiToken, supabaseToken } = await tokenTests.checkTokenStorage();
  log.separator();
  
  // 2. Decode and analyze tokens
  if (apiToken) {
    log.info("Analyzing API token...");
    const apiPayload = tokenTests.decodeJwt(apiToken);
    if (apiPayload) {
      log.info(`Token payload: ${JSON.stringify(apiPayload)}`);
    }
    log.separator();
  }
  
  // 3. Test API endpoints
  log.info("Testing API endpoints...");
  const meResult = await apiTests.testEndpoint(config.AUTH.ME);
  log.separator();
  
  // If /me endpoint failed, try to test CORS
  if (!meResult.success && meResult.status === 401) {
    await networkTests.checkCors();
    log.separator();
  }
  
  // 4. Try test login if token is missing or invalid
  if (!apiToken || !meResult.success) {
    log.warn("Token missing or invalid, attempting test login...");
    
    const testCredentials = {
      username: prompt("Enter test username:"),
      password: prompt("Enter test password:")
    };
    
    await apiTests.testLogin(testCredentials);
    
    // After login, test the ME endpoint again
    log.info("Re-testing /me endpoint after login...");
    const afterLoginResult = await apiTests.testEndpoint(config.AUTH.ME);
    
    // If still failing, test a few more critical endpoints
    if (!afterLoginResult.success) {
      log.error("Authentication still failing after login");
      
      // Test with direct authorization header
      const directToken = localStorage.getItem('api_token');
      if (directToken) {
        log.info("Testing with direct Authorization header...");
        try {
          const response = await axios.get(config.AUTH.ME, {
            headers: {
              'Authorization': `Bearer ${directToken}`
            }
          });
          
          log.success(`Direct header test succeeded: ${response.status}`);
        } catch (error) {
          log.error(`Direct header test failed: ${error.message}`);
        }
      }
    }
  }
  
  log.separator();
  log.info("DIAGNOSTICS COMPLETE");
  log.separator();
}

// Export the diagnostics function
export default runAuthDiagnostics;