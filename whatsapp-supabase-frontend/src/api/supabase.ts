import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || '';
const supabaseAnonKey = process.env.REACT_APP_SUPABASE_ANON_KEY || '';

// Debug info for Supabase configuration
console.log('Supabase initialization with URL:', supabaseUrl ? 'URL is set' : 'URL is missing');
console.log('Supabase anon key provided:', supabaseAnonKey ? 'Key is set' : 'Key is missing');

// Check if we're in a development environment and warn if config is missing
if (process.env.NODE_ENV === 'development') {
  if (!supabaseUrl || !supabaseAnonKey) {
    console.error('WARNING: Supabase configuration is incomplete or missing!');
    console.error('Please check your .env file and ensure REACT_APP_SUPABASE_URL and REACT_APP_SUPABASE_ANON_KEY are set.');
  }
}

// Create the Supabase client with debugging options
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
    debug: process.env.NODE_ENV === 'development',
  },
  global: {
    fetch: (...args) => {
      // Debug middleware for Supabase requests
      console.log('Supabase API request:', args[0]);
      return fetch(...args).then(response => {
        if (!response.ok) {
          console.warn('Supabase request failed:', response.status, response.statusText, args[0]);
        }
        return response;
      }).catch(error => {
        console.error('Supabase fetch error:', error);
        throw error;
      });
    }
  }
});

// Export a testing function to verify Supabase connectivity
export const testSupabaseConnection = async () => {
  try {
    // A simple query to test connectivity
    const { data, error } = await supabase.from('test').select('*').limit(1).maybeSingle();
    
    if (error && error.code !== 'PGRST116') {
      return { ok: false, message: error.message };
    }
    
    // Test auth functionality
    const { data: authData, error: authError } = await supabase.auth.getSession();
    
    if (authError) {
      return { ok: false, message: `Auth service error: ${authError.message}` };
    }
    
    return { ok: true, message: 'Supabase connection successful!' };
  } catch (error: any) {
    return { ok: false, message: `Exception: ${error.message}` };
  }
};
