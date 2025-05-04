import { supabase } from '../api/supabase';
import { store } from '../store';
import { fetchCurrentUser, logout } from '../store/slices/authSlice';

// Initialize Supabase auth state
export const initializeSupabaseAuth = async () => {
  // Check if there's an active session
  const { data } = await supabase.auth.getSession();
  
  if (data.session) {
    // If there's a session, try to fetch the current user
    store.dispatch(fetchCurrentUser());
  }
  
  // Listen for auth state changes
  supabase.auth.onAuthStateChange((event, session) => {
    if (event === 'SIGNED_IN') {
      // User signed in, fetch user data
      store.dispatch(fetchCurrentUser());
    } else if (event === 'SIGNED_OUT') {
      // User signed out
      store.dispatch(logout());
    } else if (event === 'TOKEN_REFRESHED') {
      // Token was refreshed, update local storage
      if (session) {
        localStorage.setItem('token', session.access_token);
      }
    }
  });
};
