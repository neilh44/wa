#!/bin/bash

# Script to create and populate frontend code files
echo "Creating and populating frontend code files..."

# Navigate to the frontend directory
cd whatsapp-supabase-frontend || { echo "Frontend directory not found!"; exit 1; }

# Create package.json
cat > package.json << 'EOL'
{
  "name": "whatsapp-supabase-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "@emotion/react": "^11.11.0",
    "@emotion/styled": "^11.11.0",
    "@mui/icons-material": "^5.11.16",
    "@mui/material": "^5.13.0",
    "@reduxjs/toolkit": "^1.9.5",
    "@supabase/supabase-js": "^2.21.0",
    "@testing-library/jest-dom": "^5.16.5",
    "@testing-library/react": "^13.4.0",
    "@testing-library/user-event": "^13.5.0",
    "@types/jest": "^27.5.2",
    "@types/node": "^16.18.30",
    "@types/react": "^18.2.6",
    "@types/react-dom": "^18.2.4",
    "axios": "^1.4.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-redux": "^8.0.5",
    "react-router-dom": "^6.11.1",
    "react-scripts": "5.0.1",
    "typescript": "^4.9.5",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  }
}
EOL

# Create tsconfig.json
cat > tsconfig.json << 'EOL'
{
  "compilerOptions": {
    "target": "es5",
    "lib": [
      "dom",
      "dom.iterable",
      "esnext"
    ],
    "allowJs": true,
    "skipLibCheck": true,
    "esModuleInterop": true,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noFallthroughCasesInSwitch": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx"
  },
  "include": [
    "src"
  ]
}
EOL

# Create public/index.html
mkdir -p public
cat > public/index.html << 'EOL'
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <link rel="icon" href="%PUBLIC_URL%/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <meta name="theme-color" content="#000000" />
    <meta
      name="description"
      content="WhatsApp to Supabase File Management System"
    />
    <link rel="apple-touch-icon" href="%PUBLIC_URL%/logo192.png" />
    <link rel="manifest" href="%PUBLIC_URL%/manifest.json" />
    <title>WhatsApp to Supabase</title>
  </head>
  <body>
    <noscript>You need to enable JavaScript to run this app.</noscript>
    <div id="root"></div>
  </body>
</html>
EOL

# Create src/index.tsx
mkdir -p src
cat > src/index.tsx << 'EOL'
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import { store } from './store';
import { Provider } from 'react-redux';
import { BrowserRouter } from 'react-router-dom';
import './index.css';

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);

root.render(
  <React.StrictMode>
    <Provider store={store}>
      <BrowserRouter>
        <App />
      </BrowserRouter>
    </Provider>
  </React.StrictMode>
);
EOL

# Create src/App.tsx
cat > src/App.tsx << 'EOL'
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useSelector } from 'react-redux';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Files from './pages/Files';
import Settings from './pages/Settings';
import { RootState } from './store';
import MainLayout from './components/common/MainLayout';

const theme = createTheme({
  palette: {
    mode: 'light',
    primary: {
      main: '#25D366', // WhatsApp green
    },
    secondary: {
      main: '#34B7F1', // WhatsApp blue
    },
  },
});

const App: React.FC = () => {
  const { isAuthenticated } = useSelector((state: RootState) => state.auth);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Routes>
        <Route path="/login" element={!isAuthenticated ? <Login /> : <Navigate to="/" />} />
        <Route path="/" element={isAuthenticated ? <MainLayout /> : <Navigate to="/login" />}>
          <Route index element={<Dashboard />} />
          <Route path="files" element={<Files />} />
          <Route path="settings" element={<Settings />} />
        </Route>
      </Routes>
    </ThemeProvider>
  );
};

export default App;
EOL

# Create src/index.css
cat > src/index.css << 'EOL'
body {
  margin: 0;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

code {
  font-family: source-code-pro, Menlo, Monaco, Consolas, 'Courier New',
    monospace;
}
EOL

# Create API configuration
mkdir -p src/api
cat > src/api/config.ts << 'EOL'
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

export default {
  API_URL,
  AUTH: {
    LOGIN: `${API_URL}/login`,
    REGISTER: `${API_URL}/register`,
    ME: `${API_URL}/me`,
  },
  FILES: {
    BASE: `${API_URL}/files`,
    SYNC: `${API_URL}/files/sync`,
  },
  WHATSAPP: {
    SESSION: `${API_URL}/whatsapp/session`,
    DOWNLOAD: `${API_URL}/whatsapp/download`,
  },
  STORAGE: {
    UPLOAD: `${API_URL}/storage/upload`,
    MISSING: `${API_URL}/storage/missing`,
  },
};
EOL

# Create Supabase client
cat > src/api/supabase.ts << 'EOL'
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.REACT_APP_SUPABASE_URL || '';
const supabaseKey = process.env.REACT_APP_SUPABASE_KEY || '';

if (!supabaseUrl || !supabaseKey) {
  console.error('Supabase URL or key not provided');
}

export const supabase = createClient(supabaseUrl, supabaseKey);
EOL

# Create auth API
cat > src/api/auth.ts << 'EOL'
import axios from 'axios';
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
  const response = await axios.post(config.AUTH.REGISTER, data);
  return response.data;
};

export const getCurrentUser = async (): Promise<UserData> => {
  const token = getToken();
  
  if (!token) {
    throw new Error('No authentication token found');
  }
  
  setAuthHeader(token);
  const response = await axios.get(config.AUTH.ME);
  return response.data;
};

export const logout = (): void => {
  localStorage.removeItem('token');
  setAuthHeader(null);
};
EOL

# Create files API
cat > src/api/files.ts << 'EOL'
import axios from 'axios';
import config from './config';

// Types
export interface FileData {
  id: string;
  filename: string;
  phone_number: string;
  size?: number;
  mime_type?: string;
  storage_path: string;
  uploaded: boolean;
  created_at: string;
}

export interface FileCreateData {
  filename: string;
  phone_number: string;
  size?: number;
  mime_type?: string;
}

export interface SyncResult {
  message: string;
  files_synced: number;
  total_missing: number;
}

// Files API functions
export const getFiles = async (phoneNumber?: string): Promise<FileData[]> => {
  const params = phoneNumber ? { phone_number: phoneNumber } : {};
  const response = await axios.get(config.FILES.BASE, { params });
  return response.data;
};

export const createFile = async (fileData: FileCreateData): Promise<FileData> => {
  const response = await axios.post(config.FILES.BASE, fileData);
  return response.data;
};

export const syncFiles = async (): Promise<SyncResult> => {
  const response = await axios.post(config.FILES.SYNC);
  return response.data;
};
EOL

# Create store files
mkdir -p src/store/slices
cat > src/store/index.ts << 'EOL'
import { configureStore } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import filesReducer from './slices/filesSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    files: filesReducer,
  },
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
EOL

# Create auth slice
cat > src/store/slices/authSlice.ts << 'EOL'
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { login as loginApi, register as registerApi, getCurrentUser, logout as logoutApi, LoginCredentials, RegisterData, UserData } from '../../api/auth';

interface AuthState {
  user: UserData | null;
  isAuthenticated: boolean;
  loading: boolean;
  error: string | null;
}

const initialState: AuthState = {
  user: null,
  isAuthenticated: localStorage.getItem('token') ? true : false,
  loading: false,
  error: null,
};

export const login = createAsyncThunk(
  'auth/login',
  async (credentials: LoginCredentials, { rejectWithValue }) => {
    try {
      await loginApi(credentials);
      const user = await getCurrentUser();
      return user;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Login failed');
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async (data: RegisterData, { rejectWithValue }) => {
    try {
      return await registerApi(data);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Registration failed');
    }
  }
);

export const fetchCurrentUser = createAsyncThunk(
  'auth/fetchCurrentUser',
  async (_, { rejectWithValue }) => {
    try {
      return await getCurrentUser();
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch user');
    }
  }
);

export const logout = createAsyncThunk(
  'auth/logout',
  async () => {
    logoutApi();
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action: PayloadAction<UserData>) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload;
      })
      .addCase(login.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Register
      .addCase(register.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state) => {
        state.loading = false;
      })
      .addCase(register.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Fetch current user
      .addCase(fetchCurrentUser.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchCurrentUser.fulfilled, (state, action: PayloadAction<UserData>) => {
        state.loading = false;
        state.isAuthenticated = true;
        state.user = action.payload;
      })
      .addCase(fetchCurrentUser.rejected, (state, action) => {
        state.loading = false;
        state.isAuthenticated = false;
        state.user = null;
        state.error = action.payload as string;
      })
      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.isAuthenticated = false;
        state.user = null;
      });
  },
});

export const { clearError } = authSlice.actions;
export default authSlice.reducer;
EOL

# Create files slice
cat > src/store/slices/filesSlice.ts << 'EOL'
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import { getFiles as getFilesApi, createFile as createFileApi, syncFiles as syncFilesApi, FileData, FileCreateData, SyncResult } from '../../api/files';

interface FilesState {
  files: FileData[];
  loading: boolean;
  error: string | null;
  syncStatus: {
    syncing: boolean;
    lastSynced: string | null;
    result: SyncResult | null;
  };
}

const initialState: FilesState = {
  files: [],
  loading: false,
  error: null,
  syncStatus: {
    syncing: false,
    lastSynced: null,
    result: null,
  },
};

export const getFiles = createAsyncThunk(
  'files/getFiles',
  async (phoneNumber: string | undefined, { rejectWithValue }) => {
    try {
      return await getFilesApi(phoneNumber);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to fetch files');
    }
  }
);

export const createFile = createAsyncThunk(
  'files/createFile',
  async (fileData: FileCreateData, { rejectWithValue }) => {
    try {
      return await createFileApi(fileData);
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to create file');
    }
  }
);

export const syncFiles = createAsyncThunk(
  'files/syncFiles',
  async (_, { rejectWithValue }) => {
    try {
      return await syncFilesApi();
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.detail || 'Failed to sync files');
    }
  }
);

const filesSlice = createSlice({
  name: 'files',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Get Files
      .addCase(getFiles.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(getFiles.fulfilled, (state, action: PayloadAction<FileData[]>) => {
        state.loading = false;
        state.files = action.payload;
      })
      .addCase(getFiles.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Create File
      .addCase(createFile.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createFile.fulfilled, (state, action: PayloadAction<FileData>) => {
        state.loading = false;
        state.files.push(action.payload);
      })
      .addCase(createFile.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      })
      // Sync Files
      .addCase(syncFiles.pending, (state) => {
        state.syncStatus.syncing = true;
        state.error = null;
      })
      .addCase(syncFiles.fulfilled, (state, action: PayloadAction<SyncResult>) => {
        state.syncStatus.syncing = false;
        state.syncStatus.lastSynced = new Date().toISOString();
        state.syncStatus.result = action.payload;
      })
      .addCase(syncFiles.rejected, (state, action) => {
        state.syncStatus.syncing = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError } = filesSlice.actions;
export default filesSlice.reducer;
EOL

# Create utils
mkdir -p src/utils
cat > src/utils/formatters.ts << 'EOL'
export const formatDate = (dateString: string): string => {
  const date = new Date(dateString);
  return date.toLocaleString();
};

export const formatFileSize = (bytes?: number): string => {
  if (!bytes) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const formatPhoneNumber = (phone: string): string => {
  if (!phone) return '';
  
  // Remove any non-numeric characters
  const cleaned = phone.replace(/\D/g, '');
  
  // Format based on length
  if (cleaned.length === 10) {
    return `(${cleaned.slice(0, 3)}) ${cleaned.slice(3, 6)}-${cleaned.slice(6)}`;
  } else if (cleaned.length === 11 && cleaned.startsWith('1')) {
    return `+1 (${cleaned.slice(1, 4)}) ${cleaned.slice(4, 7)}-${cleaned.slice(7)}`;
  } else if (cleaned.length > 10) {
    return `+${cleaned.slice(0, cleaned.length - 10)} ${cleaned.slice(-10, -7)} ${cleaned.slice(-7, -4)}-${cleaned.slice(-4)}`;
  }
  
  return phone;
};
EOL

# Create components
mkdir -p src/components/common
mkdir -p src/components/auth
mkdir -p src/components/files
mkdir -p src/components/whatsapp
mkdir -p src/components/storage

# Common components
cat > src/components/common/Button.tsx << 'EOL'
import React from 'react';
import { Button as MuiButton, ButtonProps as MuiButtonProps } from '@mui/material';

interface ButtonProps extends MuiButtonProps {
  loading?: boolean;
}

const Button: React.FC<ButtonProps> = ({ children, loading, ...props }) => {
  return (
    <MuiButton
      variant="contained"
      disabled={loading || props.disabled}
      {...props}
    >
      {loading ? 'Loading...' : children}
    </MuiButton>
  );
};

export default Button;
EOL

cat > src/components/common/Navbar.tsx << 'EOL'
import React from 'react';
import { AppBar, Toolbar, Typography, Button, Box, IconButton } from '@mui/material';
import { Link, useNavigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import MenuIcon from '@mui/icons-material/Menu';
import { logout } from '../../store/slices/authSlice';
import { AppDispatch } from '../../store';

interface NavbarProps {
  toggleSidebar: () => void;
}

const Navbar: React.FC<NavbarProps> = ({ toggleSidebar }) => {
  const dispatch = useDispatch<AppDispatch>();
  const navigate = useNavigate();

  const handleLogout = async () => {
    await dispatch(logout());
    navigate('/login');
  };

  return (
    <AppBar position="fixed">
      <Toolbar>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={toggleSidebar}
          sx={{ mr: 2, display: { sm: 'none' } }}
        >
          <MenuIcon />
        </IconButton>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          WhatsApp to Supabase
        </Typography>
        <Box sx={{ display: { xs: 'none', sm: 'block' } }}>
          <Button color="inherit" component={Link} to="/">
            Dashboard
          </Button>
          <Button color="inherit" component={Link} to="/files">
            Files
          </Button>
          <Button color="inherit" component={Link} to="/settings">
            Settings
          </Button>
        </Box>
        <Button color="inherit" onClick={handleLogout}>
          Logout
        </Button>
      </Toolbar>
    </AppBar>
  );
};

export default Navbar;
EOL

cat > src/components/common/MainLayout.tsx << 'EOL'
import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { Box, Drawer, List, ListItem, ListItemIcon, ListItemText, Toolbar, Divider } from '@mui/material';
import { useDispatch, useSelector } from 'react-redux';
import { Link } from 'react-router-dom';
import DashboardIcon from '@mui/icons-material/Dashboard';
import FolderIcon from '@mui/icons-material/Folder';
import SettingsIcon from '@mui/icons-material/Settings';
import { fetchCurrentUser } from '../../store/slices/authSlice';
import { AppDispatch, RootState } from '../../store';
import Navbar from './Navbar';

const drawerWidth = 240;

const MainLayout: React.FC = () => {
  const [mobileOpen, setMobileOpen] = useState(false);
  const dispatch = useDispatch<AppDispatch>();
  const { user } = useSelector((state: RootState) => state.auth);

  useEffect(() => {
    if (!user) {
      dispatch(fetchCurrentUser());
    }
  }, [dispatch, user]);

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawer = (
    <div>
      <Toolbar />
      <Divider />
      <List>
        <ListItem button component={Link} to="/">
          <ListItemIcon>
            <DashboardIcon />
          </ListItemIcon>
          <ListItemText primary="Dashboard" />
        </ListItem>
        <ListItem button component={Link} to="/files">
          <ListItemIcon>
            <FolderIcon />
          </ListItemIcon>
          <ListItemText primary="Files" />
        </ListItem>
        <ListItem button component={Link} to="/settings">
          <ListItemIcon>
            <SettingsIcon />
          </ListItemIcon>
          <ListItemText primary="Settings" />
        </ListItem>
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <Navbar toggleSidebar={handleDrawerToggle} />
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{ flexGrow: 1, p: 3, width: { sm: `calc(100% - ${drawerWidth}px)` } }}
      >
        <Toolbar />
        <Outlet />
      </Box>
    </Box>
  );
};

export default MainLayout;
EOL

# Create auth components
cat > src/components/auth/LoginForm.tsx << 'EOL'
import React, { useState } from 'react';
import { TextField, Box, Typography, Alert } from '@mui/material';
import { useDispatch, useSelector } from 'react-redux';
import { login, clearError } from '../../store/slices/authSlice';
import { AppDispatch, RootState } from '../../store';
import Button from '../common/Button';

const LoginForm: React.FC = () => {
  const [formData, setFormData] = useState({
    username: '',
    password: '',
  });
  const dispatch = useDispatch<AppDispatch>();
  const { loading, error } = useSelector((state: RootState) => state.auth);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData({
      ...formData,
      [name]: value,
    });
    if (error) {
      dispatch(clearError());
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    dispatch(login(formData));
  };

  return (
    <Box component="form" onSubmit={handleSubmit} sx={{ width: '100%', maxWidth: 400 }}>
      <Typography variant="h5" component="h1" gutterBottom>
        Login
      </Typography>
      
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      
      <TextField
        margin="normal"
        required
        fullWidth
        id="username"
        label="Email Address"
        name="username"
        autoComplete="email"
        autoFocus
        value={formData.username}
        onChange={handleChange}
      />
      
      <TextField
        margin="normal"
        required
        fullWidth
        name="password"
        label="Password"
        type="password"
        id="password"
        autoComplete="current-password"
        value={formData.password}
        onChange={handleChange}
      />
      
      <Button
        type="submit"
        fullWidth
        variant="contained"
        sx={{ mt: 3, mb: 2 }}
        loading={loading}
      >
        Sign In
      </Button>
    </Box>
  );
};

export default LoginForm;
EOL

# Create files components
cat > src/components# Create files components
cat > src/components/files/FileList.tsx << 'EOL'
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper, 
  Typography, 
  TextField, 
  InputAdornment,
  IconButton,
  Box,
  Chip
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import RefreshIcon from '@mui/icons-material/Refresh';
import { getFiles } from '../../store/slices/filesSlice';
import { AppDispatch, RootState } from '../../store';
import { formatDate, formatFileSize, formatPhoneNumber } from '../../utils/formatters';
import Button from '../common/Button';

const FileList: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { files, loading } = useSelector((state: RootState) => state.files);
  const [phoneFilter, setPhoneFilter] = useState('');
  const [searchText, setSearchText] = useState('');

  useEffect(() => {
    dispatch(getFiles(undefined));
  }, [dispatch]);

  const handleRefresh = () => {
    dispatch(getFiles(phoneFilter || undefined));
  };

  const handlePhoneSearch = () => {
    setPhoneFilter(searchText);
    dispatch(getFiles(searchText || undefined));
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchText(e.target.value);
  };

  const handleSearchKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handlePhoneSearch();
    }
  };

  const filteredFiles = files.filter(file => 
    !phoneFilter || file.phone_number.includes(phoneFilter)
  );

  return (
    <div>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" component="h2" gutterBottom>
          Files
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <TextField
            placeholder="Search by phone number"
            size="small"
            value={searchText}
            onChange={handleSearchChange}
            onKeyPress={handleSearchKeyPress}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
              endAdornment: (
                <InputAdornment position="end">
                  <IconButton onClick={handlePhoneSearch}>
                    <SearchIcon />
                  </IconButton>
                </InputAdornment>
              )
            }}
          />
          <Button 
            variant="outlined" 
            startIcon={<RefreshIcon />} 
            onClick={handleRefresh}
            loading={loading}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {phoneFilter && (
        <Box sx={{ mb: 2 }}>
          <Chip 
            label={`Filtering by: ${formatPhoneNumber(phoneFilter)}`} 
            onDelete={() => {
              setPhoneFilter('');
              setSearchText('');
              dispatch(getFiles(undefined));
            }} 
          />
        </Box>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>File Name</TableCell>
              <TableCell>Phone Number</TableCell>
              <TableCell>Size</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Upload Status</TableCell>
              <TableCell>Date</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredFiles.length > 0 ? (
              filteredFiles.map((file) => (
                <TableRow key={file.id}>
                  <TableCell>{file.filename}</TableCell>
                  <TableCell>{formatPhoneNumber(file.phone_number)}</TableCell>
                  <TableCell>{formatFileSize(file.size)}</TableCell>
                  <TableCell>{file.mime_type || 'Unknown'}</TableCell>
                  <TableCell>
                    <Chip 
                      label={file.uploaded ? 'Uploaded' : 'Pending'} 
                      color={file.uploaded ? 'success' : 'warning'} 
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{formatDate(file.created_at)}</TableCell>
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  No files found
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </div>
  );
};

export default FileList;
EOL

# Create WhatsApp components
cat > src/components/whatsapp/SessionManager.tsx << 'EOL'
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Box, Paper, Typography, CircularProgress, Alert, Divider } from '@mui/material';
import config from '../../api/config';
import Button from '../common/Button';

interface SessionState {
  id: string | null;
  status: 'initializing' | 'qr_ready' | 'authenticated' | 'not_authenticated' | 'error';
  message: string;
  qrData?: string;
}

const SessionManager: React.FC = () => {
  const [session, setSession] = useState<SessionState>({
    id: null,
    status: 'not_authenticated',
    message: 'No active WhatsApp session'
  });
  const [loading, setLoading] = useState(false);

  const initializeSession = async () => {
    setLoading(true);
    try {
      const response = await axios.post(config.WHATSAPP.SESSION);
      if (response.data.qr_available) {
        setSession({
          id: response.data.session_id,
          status: 'qr_ready',
          message: 'Please scan the QR code with your WhatsApp',
          qrData: 'QR_DATA_PLACEHOLDER' // In a real app, you'd use the actual QR data
        });
      } else {
        setSession({
          id: null,
          status: 'error',
          message: response.data.error || 'Failed to initialize session'
        });
      }
    } catch (error) {
      setSession({
        id: null,
        status: 'error',
        message: 'An error occurred while initializing the session'
      });
    } finally {
      setLoading(false);
    }
  };

  const checkSessionStatus = async () => {
    if (!session.id) return;
    
    setLoading(true);
    try {
      const response = await axios.get(`${config.WHATSAPP.SESSION}/${session.id}`);
      if (response.data.status === 'authenticated') {
        setSession({
          ...session,
          status: 'authenticated',
          message: 'WhatsApp session is active'
        });
      } else {
        setSession({
          ...session,
          status: 'not_authenticated',
          message: 'Session is not authenticated, please rescan the QR code'
        });
      }
    } catch (error) {
      setSession({
        ...session,
        status: 'error',
        message: 'An error occurred while checking the session'
      });
    } finally {
      setLoading(false);
    }
  };

  const closeSession = async () => {
    if (!session.id) return;
    
    setLoading(true);
    try {
      await axios.delete(`${config.WHATSAPP.SESSION}/${session.id}`);
      setSession({
        id: null,
        status: 'not_authenticated',
        message: 'Session has been closed'
      });
    } catch (error) {
      setSession({
        ...session,
        status: 'error',
        message: 'An error occurred while closing the session'
      });
    } finally {
      setLoading(false);
    }
  };

  const downloadFiles = async () => {
    setLoading(true);
    try {
      const response = await axios.post(config.WHATSAPP.DOWNLOAD);
      if (response.data.files && response.data.files.length > 0) {
        setSession({
          ...session,
          message: `Downloaded ${response.data.files.length} files`
        });
      } else {
        setSession({
          ...session,
          message: 'No new files found'
        });
      }
    } catch (error) {
      setSession({
        ...session,
        status: 'error',
        message: 'An error occurred while downloading files'
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Check session status periodically if there's an active session
    let interval: NodeJS.Timeout;
    
    if (session.id && session.status === 'qr_ready') {
      interval = setInterval(checkSessionStatus, 5000);
    }
    
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [session.id, session.status]);

  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h6" gutterBottom>
        WhatsApp Session
      </Typography>
      
      <Divider sx={{ mb: 2 }} />
      
      <Box sx={{ mb: 3 }}>
        <Alert 
          severity={
            session.status === 'authenticated' ? 'success' : 
            session.status === 'error' ? 'error' : 
            session.status === 'qr_ready' ? 'info' : 'warning'
          }
        >
          {session.message}
        </Alert>
      </Box>
      
      {session.status === 'qr_ready' && (
        <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
          {/* In a real app, you'd display an actual QR code here */}
          <Paper sx={{ p: 2, width: 200, height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Typography variant="body2" color="text.secondary" align="center">
              QR Code placeholder<br />
              Scan with WhatsApp
            </Typography>
          </Paper>
        </Box>
      )}
      
      <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
        {!session.id && (
          <Button
            variant="contained"
            onClick={initializeSession}
            loading={loading}
          >
            Start WhatsApp Session
          </Button>
        )}
        
        {session.id && session.status !== 'authenticated' && (
          <Button
            variant="outlined"
            onClick={checkSessionStatus}
            loading={loading}
          >
            Check Status
          </Button>
        )}
        
        {session.id && (
          <Button
            variant="outlined"
            color="error"
            onClick={closeSession}
            loading={loading}
          >
            Close Session
          </Button>
        )}
        
        {session.status === 'authenticated' && (
          <Button
            variant="contained"
            color="secondary"
            onClick={downloadFiles}
            loading={loading}
          >
            Download Files
          </Button>
        )}
      </Box>
    </Paper>
  );
};

export default SessionManager;
EOL

# Create storage components
cat > src/components/storage/FileUploader.tsx << 'EOL'
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useDispatch } from 'react-redux';
import { Box, Paper, Typography, Alert, LinearProgress, Divider, List, ListItem, ListItemText } from '@mui/material';
import { syncFiles } from '../../store/slices/filesSlice';
import { AppDispatch } from '../../store';
import config from '../../api/config';
import Button from '../common/Button';
import { formatFileSize, formatPhoneNumber } from '../../utils/formatters';

interface FileInfo {
  id: string;
  filename: string;
  phone_number: string;
  size?: number;
  mime_type?: string;
  uploaded: boolean;
}

const FileUploader: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const [loading, setLoading] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [message, setMessage] = useState<{ type: 'info' | 'success' | 'error' | 'warning', text: string } | null>(null);
  const [missingFiles, setMissingFiles] = useState<FileInfo[]>([]);

  const getMissingFiles = async () => {
    setLoading(true);
    try {
      const response = await axios.get(config.STORAGE.MISSING);
      setMissingFiles(response.data.files || []);
      setMessage({
        type: 'info',
        text: `Found ${response.data.files.length} files pending upload`
      });
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Failed to fetch missing files'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setSyncing(true);
    try {
      await dispatch(syncFiles());
      setMessage({
        type: 'success',
        text: 'Files synchronized successfully'
      });
      // Refresh the missing files list
      await getMissingFiles();
    } catch (error) {
      setMessage({
        type: 'error',
        text: 'Failed to synchronize files'
      });
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    // Get missing files on initial load
    getMissingFiles();
  }, []);

  return (
    <Paper elevation={3} sx={{ p: 3, maxWidth: 600, mx: 'auto' }}>
      <Typography variant="h6" gutterBottom>
        File Synchronization
      </Typography>
      
      <Divider sx={{ mb: 2 }} />
      
      {message && (
        <Box sx={{ mb: 3 }}>
          <Alert severity={message.type}>
            {message.text}
          </Alert>
        </Box>
      )}
      
      {(loading || syncing) && (
        <Box sx={{ width: '100%', mb: 3 }}>
          <LinearProgress />
        </Box>
      )}
      
      <Box sx={{ mb: 3 }}>
        {missingFiles.length > 0 ? (
          <List>
            {missingFiles.slice(0, 5).map((file) => (
              <ListItem key={file.id} divider>
                <ListItemText
                  primary={file.filename}
                  secondary={`${formatPhoneNumber(file.phone_number)} - ${formatFileSize(file.size)}`}
                />
              </ListItem>
            ))}
            {missingFiles.length > 5 && (
              <ListItem>
                <ListItemText
                  primary={`${missingFiles.length - 5} more files...`}
                />
              </ListItem>
            )}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary" align="center">
            No pending files
          </Typography>
        )}
      </Box>
      
      <Box sx={{ display: 'flex', gap: 2 }}>
        <Button
          variant="outlined"
          onClick={getMissingFiles}
          loading={loading}
        >
          Check Pending Files
        </Button>
        
        <Button
          variant="contained"
          onClick={handleSync}
          loading={syncing}
          disabled={missingFiles.length === 0}
        >
          Synchronize Files
        </Button>
      </Box>
    </Paper>
  );
};

export default FileUploader;
EOL

# Create pages
mkdir -p src/pages

cat > src/pages/Login.tsx << 'EOL'
import React from 'react';
import { Box, Container, Paper, Typography } from '@mui/material';
import LoginForm from '../components/auth/LoginForm';

const Login: React.FC = () => {
  return (
    <Container component="main" maxWidth="xs">
      <Box
        sx={{
          marginTop: 8,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
        }}
      >
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Box
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: 'center',
              mb: 4,
            }}
          >
            <Typography component="h1" variant="h4" align="center" gutterBottom>
              WhatsApp to Supabase
            </Typography>
            <Typography variant="body2" color="text.secondary" align="center">
              File Management System
            </Typography>
          </Box>
          <LoginForm />
        </Paper>
      </Box>
    </Container>
  );
};

export default Login;
EOL

cat > src/pages/Dashboard.tsx << 'EOL'
import React, { useEffect, useState } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import { Typography, Grid, Paper, Box, Alert } from '@mui/material';
import { getFiles } from '../store/slices/filesSlice';
import { AppDispatch, RootState } from '../store';
import SessionManager from '../components/whatsapp/SessionManager';
import FileUploader from '../components/storage/FileUploader';

const Dashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>();
  const { files } = useSelector((state: RootState) => state.files);
  const { user } = useSelector((state: RootState) => state.auth);
  const [stats, setStats] = useState({
    totalFiles: 0,
    uploadedFiles: 0,
    pendingFiles: 0,
    uniquePhoneNumbers: 0
  });

  useEffect(() => {
    dispatch(getFiles(undefined));
  }, [dispatch]);

  useEffect(() => {
    if (files.length > 0) {
      const uploadedFiles = files.filter(file => file.uploaded).length;
      const pendingFiles = files.length - uploadedFiles;
      const uniquePhoneNumbers = new Set(files.map(file => file.phone_number)).size;
      
      setStats({
        totalFiles: files.length,
        uploadedFiles,
        pendingFiles,
        uniquePhoneNumbers
      });
    }
  }, [files]);

  return (
    <div>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      
      {user && (
        <Box sx={{ mb: 3 }}>
          <Alert severity="info">
            Welcome, {user.username}! Your WhatsApp to Supabase integration is ready.
          </Alert>
        </Box>
      )}
      
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              Total Files
            </Typography>
            <Typography component="p" variant="h4">
              {stats.totalFiles}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              Uploaded
            </Typography>
            <Typography component="p" variant="h4">
              {stats.uploadedFiles}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              Pending
            </Typography>
            <Typography component="p" variant="h4">
              {stats.pendingFiles}
            </Typography>
          </Paper>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Paper sx={{ p: 2, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              Phone Numbers
            </Typography>
            <Typography component="p" variant="h4">
              {stats.uniquePhoneNumbers}
            </Typography>
          </Paper>
        </Grid>
      </Grid>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <SessionManager />
        </Grid>
        <Grid item xs={12} md={6}>
          <FileUploader />
        </Grid>
      </Grid>
    </div>
  );
};

export default Dashboard;
EOL

cat > src/pages/Files.tsx << 'EOL'
import React from 'react';
import { Typography, Box } from '@mui/material';
import FileList from '../components/files/FileList';

const Files: React.FC = () => {
  return (
    <div>
      <Typography variant="h4" component="h1" gutterBottom>
        File Management
      </Typography>
      <Box sx={{ mb: 4 }}>
        <Typography variant="body1" color="text.secondary" paragraph>
          Manage files downloaded from WhatsApp. Files are organized by phone number and automatically uploaded to Supabase storage.
        </Typography>
      </Box>
      <FileList />
    </div>
  );
};

export default Files;
EOL

cat > src/pages/Settings.tsx << 'EOL'
import React, { useEffect, useState } from 'react';
import { useSelector } from 'react-redux';
import { 
  Typography, 
  Box, 
  Paper, 
  Divider, 
  List, 
  ListItem, 
  ListItemText, 
  Switch, 
  TextField, 
  Grid,
  Alert,
  Snackbar
} from '@mui/material';
import { RootState } from '../store';
import Button from '../components/common/Button';

const Settings: React.FC = () => {
  const { user } = useSelector((state: RootState) => state.auth);
  const [settings, setSettings] = useState({
    autoDownload: true,
    autoUpload: true,
    notifyOnError: true,
    maxFileSize: 10,
    downloadInterval: 5
  });
  const [open, setOpen] = useState(false);

  const handleToggle = (setting: string) => () => {
    setSettings({
      ...settings,
      [setting]: !settings[setting as keyof typeof settings]
    });
  };

  const handleNumberChange = (setting: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value) || 0;
    setSettings({
      ...settings,
      [setting]: value
    });
  };

  const handleSave = () => {
    // In a real app, you'd save these settings to the backend
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <div>
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Account Information
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            {user && (
              <List>
                <ListItem>
                  <ListItemText primary="Username" secondary={user.username} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Email" secondary={user.email} />
                </ListItem>
                <ListItem>
                  <ListItemText primary="Account Type" secondary={user.is_admin ? 'Administrator' : 'User'} />
                </ListItem>
              </List>
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              App Settings
            </Typography>
            <Divider sx={{ mb: 2 }} />
            
            <List>
              <ListItem>
                <ListItemText 
                  primary="Auto Download Files" 
                  secondary="Automatically download files from WhatsApp" 
                />
                <Switch 
                  edge="end"
                  checked={settings.autoDownload}
                  onChange={handleToggle('autoDownload')}
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Auto Upload Files" 
                  secondary="Automatically upload files to Supabase" 
                />
                <Switch 
                  edge="end"
                  checked={settings.autoUpload}
                  onChange={handleToggle('autoUpload')}
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Error Notifications" 
                  secondary="Receive notifications on errors" 
                />
                <Switch 
                  edge="end"
                  checked={settings.notifyOnError}
                  onChange={handleToggle('notifyOnError')}
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Max File Size (MB)" 
                  secondary="Maximum file size to process" 
                />
                <TextField
                  type="number"
                  value={settings.maxFileSize}
                  onChange={handleNumberChange('maxFileSize')}
                  sx={{ width: 70 }}
                  size="small"
                />
              </ListItem>
              
              <ListItem>
                <ListItemText 
                  primary="Download Interval (minutes)" 
                  secondary="How often to check for new files" 
                />
                <TextField
                  type="number"
                  value={settings.downloadInterval}
                  onChange={handleNumberChange('downloadInterval')}
                  sx={{ width: 70 }}
                  size="small"
                />
              </ListItem>
            </List>
            
            <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
              <Button variant="contained" onClick={handleSave}>
                Save Settings
              </Button>
            </Box>
          </Paper>
        </Grid>
      </Grid>
      
      <Snackbar open={open} autoHideDuration={6000} onClose={handleClose}>
        <Alert onClose={handleClose} severity="success" sx={{ width: '100%' }}>
          Settings saved successfully
        </Alert>
      </Snackbar>
    </div>
  );
};

export default Settings;
EOL

# Create .env.example
cat > .env.example << 'EOL'
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_SUPABASE_URL=your_supabase_url
REACT_APP_SUPABASE_KEY=your_supabase_key
EOL

echo "Frontend code creation completed successfully!"