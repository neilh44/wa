// whatsappService.js - Service to handle WhatsApp API interactions
import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000/api';

class WhatsAppService {
  constructor() {
    this.token = localStorage.getItem('token');
    this.sessionId = null;
  }

  // Set auth token
  setToken(token) {
    this.token = token;
    localStorage.setItem('token', token);
  }

  // Get authorization header
  getAuthHeader() {
    return {
      headers: {
        'Authorization': `Bearer ${this.token}`
      }
    };
  }

  // Initialize a new WhatsApp session
  async initializeSession() {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/whatsapp/session`, 
        {}, 
        this.getAuthHeader()
      );
      
      if (response.data && response.data.session_id) {
        this.sessionId = response.data.session_id;
        return response.data;
      } else {
        throw new Error('Invalid response: No session ID received');
      }
    } catch (error) {
      console.error('Error initializing WhatsApp session:', error);
      throw error;
    }
  }

  // Check session status
  async checkSessionStatus(sessionId = null) {
    const id = sessionId || this.sessionId;
    
    if (!id) {
      throw new Error('No session ID available');
    }
    
    try {
      const response = await axios.get(
        `${API_BASE_URL}/whatsapp/session/${id}`, 
        this.getAuthHeader()
      );
      
      return response.data;
    } catch (error) {
      console.error('Error checking session status:', error);
      throw error;
    }
  }

  // Close a session
  async closeSession(sessionId = null) {
    const id = sessionId || this.sessionId;
    
    if (!id) {
      throw new Error('No session ID available');
    }
    
    try {
      const response = await axios.delete(
        `${API_BASE_URL}/whatsapp/session/${id}`, 
        this.getAuthHeader()
      );
      
      if (id === this.sessionId) {
        this.sessionId = null;
      }
      
      return response.data;
    } catch (error) {
      console.error('Error closing session:', error);
      throw error;
    }
  }

  // Download files from WhatsApp
  async downloadFiles() {
    try {
      const response = await axios.post(
        `${API_BASE_URL}/whatsapp/download`, 
        {}, 
        this.getAuthHeader()
      );
      
      return response.data.files || [];
    } catch (error) {
      console.error('Error downloading files:', error);
      throw error;
    }
  }

  // Check API availability
  async checkApiAvailability() {
    try {
      const response = await axios.get(
        `${API_BASE_URL}/`, 
        { ...this.getAuthHeader(), timeout: 5000 }
      );
      
      return true;
    } catch (error) {
      console.error('API not available:', error);
      return false;
    }
  }
}

// Export singleton instance
const whatsAppService = new WhatsAppService();
export default whatsAppService;