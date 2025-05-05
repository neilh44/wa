// supabaseService.js - Service to handle Supabase interactions
import { createClient } from '@supabase/supabase-js';

// Initialize Supabase client
const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || '';
const supabaseKey = process.env.REACT_APP_SUPABASE_KEY || '';
const supabase = createClient(supabaseUrl, supabaseKey);

class SupabaseService {
  // Authentication methods
  async signIn(email, password) {
    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      
      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error signing in:', error);
      throw error;
    }
  }

  async signUp(email, password, userData = {}) {
    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: userData
        }
      });
      
      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error signing up:', error);
      throw error;
    }
  }

  async signOut() {
    try {
      const { error } = await supabase.auth.signOut();
      if (error) throw error;
    } catch (error) {
      console.error('Error signing out:', error);
      throw error;
    }
  }

  // Session management
  async getSession() {
    try {
      const { data, error } = await supabase.auth.getSession();
      if (error) throw error;
      return data.session;
    } catch (error) {
      console.error('Error getting session:', error);
      return null;
    }
  }

  // Get current user
  async getCurrentUser() {
    try {
      const { data, error } = await supabase.auth.getUser();
      if (error) throw error;
      return data.user;
    } catch (error) {
      console.error('Error getting user:', error);
      return null;
    }
  }

  // WhatsApp sessions
  async getWhatsAppSessions(userId) {
    try {
      const { data, error } = await supabase
        .from('sessions')
        .select('*')
        .eq('user_id', userId)
        .eq('session_type', 'whatsapp')
        .order('created_at', { ascending: false });
      
      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error fetching WhatsApp sessions:', error);
      throw error;
    }
  }

  async createWhatsAppSession(userId, sessionData) {
    try {
      const { data, error } = await supabase
        .from('sessions')
        .insert([
          { 
            user_id: userId,
            session_type: 'whatsapp',
            session_data: sessionData,
            status: 'inactive'
          }
        ])
        .select();
      
      if (error) throw error;
      return data[0];
    } catch (error) {
      console.error('Error creating WhatsApp session:', error);
      throw error;
    }
  }

  async updateWhatsAppSession(sessionId, updateData) {
    try {
      const { data, error } = await supabase
        .from('sessions')
        .update(updateData)
        .eq('id', sessionId)
        .select();
      
      if (error) throw error;
      return data[0];
    } catch (error) {
      console.error('Error updating WhatsApp session:', error);
      throw error;
    }
  }

  // Files management
  async getFiles(userId, phoneNumber = null) {
    try {
      let query = supabase
        .from('files')
        .select('*')
        .eq('user_id', userId);
      
      if (phoneNumber) {
        query = query.eq('phone_number', phoneNumber);
      }
      
      const { data, error } = await query.order('created_at', { ascending: false });
      
      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error fetching files:', error);
      throw error;
    }
  }

  async getFileDetails(fileId) {
    try {
      const { data, error } = await supabase
        .from('files')
        .select('*')
        .eq('id', fileId)
        .single();
      
      if (error) throw error;
      return data;
    } catch (error) {
      console.error('Error fetching file details:', error);
      throw error;
    }
  }

  // Storage functions
  async getFileUrl(path) {
    try {
      const { data, error } = await supabase.storage
        .from('whatsapp_files')
        .createSignedUrl(path, 3600); // 1 hour expiry
      
      if (error) throw error;
      return data.signedUrl;
    } catch (error) {
      console.error('Error getting file URL:', error);
      throw error;
    }
  }
}

// Export singleton instance
const supabaseService = new SupabaseService();
export default supabaseService;