import axios from 'axios';

// Setup axios interceptors
const setupInterceptors = () => {
  // Request interceptor
  axios.interceptors.request.use(
    (config) => {
      // Get token from localStorage for every request
      const token = localStorage.getItem('token');
      
      // If token exists, add it to the request header
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      return config;
    },
    (error) => {
      return Promise.reject(error);
    }
  );

  // Response interceptor
  axios.interceptors.response.use(
    (response) => {
      return response;
    },
    (error) => {
      // Handle 401 Unauthorized errors globally
      if (error.response && error.response.status === 401) {
        console.error('Authentication failed:', error);
        
        // Check if we're not already on the login page to avoid redirect loops
        if (!window.location.pathname.includes('/login')) {
          // Clear token and redirect to login
          localStorage.removeItem('token');
          window.location.href = '/login';
          
          // Show a notification about session expiration
          alert('Your session has expired. Please log in again.');
        }
      }
      
      return Promise.reject(error);
    }
  );
};

export default setupInterceptors;