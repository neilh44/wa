import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || '';
const supabaseKey = process.env.REACT_APP_SUPABASE_KEY || '';

if (!supabaseUrl || !supabaseKey) {
  console.error('Supabase URL or key not provided in environment variables');
}

export const supabase = createClient(supabaseUrl, supabaseKey);

// Add a helper function to check if Supabase is configured correctly
export const checkSupabaseConfig = (): boolean => {
  return Boolean(supabaseUrl && supabaseKey);
};
