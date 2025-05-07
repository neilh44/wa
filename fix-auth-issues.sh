#!/bin/bash

# Script to fix authentication issues in WhatsApp-Supabase integration
echo "Starting authentication fix script..."

# Create directories if they don't exist
mkdir -p fixes/frontend
mkdir -p fixes/backend

# Fix 1: Create a valid manifest.json
cat > fixes/frontend/manifest.json << 'EOL'
{
  "short_name": "WhatsApp-Supabase",
  "name": "WhatsApp to Supabase File Management",
  "icons": [
    {
      "src": "favicon.ico",
      "sizes": "64x64 32x32 24x24 16x16",
      "type": "image/x-icon"
    }
  ],
  "start_url": ".",
  "display": "standalone",
  "theme_color": "#25D366",
  "background_color": "#ffffff"
}
EOL
echo "✅ Created fixed manifest.json"

# Fix 2: Update auth.ts to fix Supabase authentication
cat > fixes/frontend/auth.ts << 'EOL'
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
EOL
echo "✅ Updated auth.ts to fix authentication flow"

# Fix 3: Create a proper .env file
cat > fixes/frontend/.env.local << 'EOL'
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_SUPABASE_URL=https://your-project-id.supabase.co
REACT_APP_SUPABASE_KEY=your-supabase-anon-key
EOL
echo "✅ Created .env.local template (update with your Supabase credentials)"

# Fix 4: Update supabase.ts
cat > fixes/frontend/supabase.ts << 'EOL'
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
EOL
echo "✅ Updated supabase.ts with configuration check"

# Fix 5: Update the backend auth_service.py
cat > fixes/backend/auth_service.py << 'EOL'
from typing import Optional
from uuid import UUID
import os
from app.models.user import User, UserCreate, UserLogin, Token
from app.utils.security import hash_password, verify_password, create_access_token
from datetime import timedelta
from app.config import settings
from supabase import create_client, Client
from app.utils.logger import get_logger
import httpx

logger = get_logger()

# Add error handling for Supabase connection
try:
    supabase: Client = create_client(settings.supabase_url, settings.supabase_key)
    logger.info("Supabase client initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Supabase client: {e}")
    supabase = None

def register_user(user_data: UserCreate) -> User:
    """Register a new user."""
    if not supabase:
        logger.error("Supabase client not initialized")
        raise Exception("Database connection error")
    
    try:
        # Check if user already exists
        user_query = supabase.table("users").select("*").eq("email", user_data.email).execute()
        
        if user_query.data:
            raise ValueError("User with this email already exists")
        
        # Create new user
        hashed_password = hash_password(user_data.password)
        
        user_dict = user_data.dict()
        user_dict.pop("password")  # Don't store plain password
        user_dict["hashed_password"] = hashed_password
        
        # Insert into Supabase
        result = supabase.table("users").insert(user_dict).execute()
        
        if not result.data:
            logger.error("Failed to create user")
            raise Exception("Failed to create user")
        
        return User(**result.data[0])
    except Exception as e:
        logger.error(f"Error in register_user: {e}")
        raise

def authenticate_user(user_login: UserLogin) -> Optional[User]:
    """Authenticate a user and return user if credentials are valid."""
    if not supabase:
        logger.error("Supabase client not initialized")
        raise Exception("Database connection error")
    
    try:
        user_query = supabase.table("users").select("*").eq("email", user_login.email).execute()
        
        if not user_query.data:
            logger.warning(f"No user found with email: {user_login.email}")
            return None
        
        user_data = user_query.data[0]
        
        if not verify_password(user_login.password, user_data.get("hashed_password", "")):
            logger.warning(f"Invalid password for user: {user_login.email}")
            return None
        
        return User(**user_data)
    except Exception as e:
        logger.error(f"Error in authenticate_user: {e}")
        raise

def create_user_token(user: User) -> Token:
    """Create a JWT token for the user."""
    try:
        access_token_expires = timedelta(minutes=settings.jwt_expires_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id), "username": user.username},
            expires_delta=access_token_expires
        )
        return Token(access_token=access_token)
    except Exception as e:
        logger.error(f"Error in create_user_token: {e}")
        raise

def get_user_by_id(user_id: str) -> Optional[User]:
    """Get a user by ID."""
    if not supabase:
        logger.error("Supabase client not initialized")
        raise Exception("Database connection error")
    
    try:
        user_query = supabase.table("users").select("*").eq("id", user_id).execute()
        
        if not user_query.data:
            return None
        
        return User(**user_query.data[0])
    except Exception as e:
        logger.error(f"Error in get_user_by_id: {e}")
        raise
EOL
echo "✅ Updated auth_service.py with better error handling"

# Fix 6: Create a script to setup database tables in Supabase
cat > fixes/supabase-setup.sql << 'EOL'
-- Create tables for WhatsApp to Supabase integration

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Sessions table
CREATE TABLE IF NOT EXISTS sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    session_type TEXT NOT NULL,
    device_name TEXT,
    status TEXT NOT NULL,
    session_data JSONB DEFAULT '{}'::JSONB,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT valid_session_type CHECK (session_type IN ('whatsapp'))
);

-- Files table
CREATE TABLE IF NOT EXISTS files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    size INTEGER,
    mime_type TEXT,
    storage_path TEXT NOT NULL,
    uploaded BOOLEAN DEFAULT FALSE,
    upload_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Storage bucket setup (run this in Supabase dashboard or via API)
-- CREATE BUCKET whatsapp_files;
EOL
echo "✅ Created Supabase setup SQL script"

# Fix 7: Configuration validation script
cat > fixes/config-validation.js << 'EOL'
// Run this with Node.js to validate your configuration before deploying
const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

console.log('Validating configuration for WhatsApp-Supabase integration...');

// Check if .env files exist
const frontendEnvPath = path.join(process.cwd(), '.env.local');
const backendEnvPath = path.join(process.cwd(), '.env');

let hasErrors = false;

// Check frontend env
if (!fs.existsSync(frontendEnvPath)) {
  console.error('❌ Frontend .env.local file missing');
  hasErrors = true;
} else {
  const frontendEnv = fs.readFileSync(frontendEnvPath, 'utf8');
  
  if (!frontendEnv.includes('REACT_APP_SUPABASE_URL=')) {
    console.error('❌ REACT_APP_SUPABASE_URL missing in frontend .env.local');
    hasErrors = true;
  } else if (frontendEnv.includes('REACT_APP_SUPABASE_URL=your-project-id')) {
    console.error('❌ REACT_APP_SUPABASE_URL not configured in frontend .env.local');
    hasErrors = true;
  }
  
  if (!frontendEnv.includes('REACT_APP_SUPABASE_KEY=')) {
    console.error('❌ REACT_APP_SUPABASE_KEY missing in frontend .env.local');
    hasErrors = true;
  } else if (frontendEnv.includes('REACT_APP_SUPABASE_KEY=your-supabase-anon-key')) {
    console.error('❌ REACT_APP_SUPABASE_KEY not configured in frontend .env.local');
    hasErrors = true;
  }
}

// Check backend env
if (!fs.existsSync(backendEnvPath)) {
  console.error('❌ Backend .env file missing');
  hasErrors = true;
} else {
  const backendEnv = fs.readFileSync(backendEnvPath, 'utf8');
  
  if (!backendEnv.includes('SUPABASE_URL=')) {
    console.error('❌ SUPABASE_URL missing in backend .env');
    hasErrors = true;
  } else if (backendEnv.includes('SUPABASE_URL=your_supabase_url')) {
    console.error('❌ SUPABASE_URL not configured in backend .env');
    hasErrors = true;
  }
  
  if (!backendEnv.includes('SUPABASE_KEY=')) {
    console.error('❌ SUPABASE_KEY missing in backend .env');
    hasErrors = true;
  } else if (backendEnv.includes('SUPABASE_KEY=your_supabase_key')) {
    console.error('❌ SUPABASE_KEY not configured in backend .env');
    hasErrors = true;
  }
  
  if (!backendEnv.includes('SUPABASE_JWT_SECRET=')) {
    console.error('❌ SUPABASE_JWT_SECRET missing in backend .env');
    hasErrors = true;
  }
  
  if (!backendEnv.includes('APP_SECRET_KEY=')) {
    console.error('❌ APP_SECRET_KEY missing in backend .env');
    hasErrors = true;
  }
}

// Render specific checks
console.log('\nChecking Render deployment compatibility...');

// Check if a render.yaml exists
const renderYamlPath = path.join(process.cwd(), 'render.yaml');
if (!fs.existsSync(renderYamlPath)) {
  console.warn('⚠️ render.yaml not found - you will need to configure your Render services manually');
} else {
  console.log('✅ render.yaml found');
}

// Print summary
if (hasErrors) {
  console.log('\n❌ Configuration validation failed. Please fix the errors before deploying.');
} else {
  console.log('\n✅ Configuration validation passed. Your application should be ready for deployment.');
}

// Provide deployment instructions
console.log('\n--- DEPLOYMENT INSTRUCTIONS ---');
console.log('1. Fix any configuration errors shown above');
console.log('2. Apply the SQL schema to your Supabase project');
console.log('3. Set up the following environment variables in Render:');
console.log('   - SUPABASE_URL');
console.log('   - SUPABASE_KEY');
console.log('   - SUPABASE_JWT_SECRET');
console.log('   - APP_SECRET_KEY');
console.log('   - APP_DEBUG (set to false for production)');
console.log('4. Link your GitHub repository in Render');
console.log('5. Deploy both frontend and backend services');
EOL
echo "✅ Created configuration validation script"

# Fix 8: Create a Render deployment file
cat > fixes/render.yaml << 'EOL'
services:
  # Backend API service
  - type: web
    name: whatsapp-supabase-backend
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_KEY
        sync: false
      - key: SUPABASE_JWT_SECRET
        sync: false
      - key: APP_SECRET_KEY
        sync: false
      - key: APP_DEBUG
        value: false
      - key: APP_HOST
        value: 0.0.0.0
      - key: APP_PORT
        fromService:
          type: web
          name: whatsapp-supabase-backend
          envVarKey: PORT
      - key: WHATSAPP_DATA_DIR
        value: ./whatsapp_data
    autoDeploy: true

  # Frontend React app
  - type: web
    name: whatsapp-supabase-frontend
    env: static
    buildCommand: npm install && npm run build
    staticPublishPath: ./build
    envVars:
      - key: REACT_APP_API_URL
        fromService:
          type: web
          name: whatsapp-supabase-backend
          value: https://whatsapp-supabase-backend.onrender.com/api
      - key: REACT_APP_SUPABASE_URL
        sync: false
      - key: REACT_APP_SUPABASE_KEY
        sync: false
    autoDeploy: true
EOL
echo "✅ Created Render deployment configuration"

# Fix 9: Create installation script
cat > install-fixes.sh << 'EOL'
#!/bin/bash

# Script to apply fixes to the WhatsApp-Supabase project
echo "Applying authentication fixes..."

# Apply frontend fixes
echo "Applying frontend fixes..."
cp fixes/frontend/manifest.json public/manifest.json
cp fixes/frontend/auth.ts src/api/auth.ts
cp fixes/frontend/supabase.ts src/api/supabase.ts
cp fixes/frontend/.env.local .env.local

# Apply backend fixes
echo "Applying backend fixes..."
cp fixes/backend/auth_service.py app/services/auth_service.py

# Copy configuration files
echo "Copying configuration files..."
cp fixes/render.yaml render.yaml

echo "✅ Fixes applied successfully!"
echo ""
echo "Next steps:"
echo "1. Update .env.local with your Supabase credentials"
echo "2. Update .env with your Supabase credentials"
echo "3. Run the Supabase SQL script in your Supabase SQL editor"
echo "4. Run 'node fixes/config-validation.js' to validate your configuration"
echo "5. Follow the deployment instructions for Render"
EOL
chmod +x install-fixes.sh
echo "✅ Created installation script"

# Fix 10: README with instructions
cat > fixes/README.md << 'EOL'
# WhatsApp-Supabase Authentication Fix

This directory contains fixes for the authentication issues in the WhatsApp-Supabase integration.

## Common Authentication Issues

1. **Invalid Manifest**: The application's manifest.json has syntax errors.
2. **Supabase Authentication Error**: Invalid login credentials or configuration.
3. **Backend Authentication Error**: 401 Unauthorized from the backend API.
4. **Missing Auth Session**: No active authentication session in Supabase.

## How to Apply Fixes

Run the installation script:

```bash
./install-fixes.sh
```

## Required Environment Variables

### Frontend (.env.local)
```
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_SUPABASE_URL=https://your-project-id.supabase.co
REACT_APP_SUPABASE_KEY=your-supabase-anon-key
```

### Backend (.env)
```
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_JWT_SECRET=your-jwt-secret
APP_SECRET_KEY=your-app-secret-key
APP_DEBUG=true
APP_HOST=0.0.0.0
APP_PORT=8000
WHATSAPP_DATA_DIR=./whatsapp_data
```

## Deploying to Render

1. Make sure your configuration is valid by running:
   ```
   node fixes/config-validation.js
   ```

2. Set up your database schema in Supabase:
   - Run the SQL in `fixes/supabase-setup.sql` in the Supabase SQL Editor
   - Create a storage bucket named `whatsapp_files` in Supabase

3. Connect your GitHub repository to Render and deploy using the `render.yaml` configuration

4. Set up the required environment variables in Render as specified in the validation script output

## Troubleshooting

If you experience issues after applying these fixes:

1. Check the browser console for errors
2. Verify your Supabase credentials
3. Confirm your backend API is accessible
4. Review the backend logs for detailed error messages
5. Ensure your Supabase tables are properly created
EOL
echo "✅ Created README with instructions"

echo ""
echo "Fix script completed successfully!"
echo "To apply the fixes, run: ./install-fixes.sh"
echo "See fixes/README.md for detailed instructions."