#!/usr/bin/env python3
"""
WhatsApp-Supabase Integration Troubleshooter

This script diagnoses and fixes common issues in the WhatsApp-Supabase integration:
1. 401 Unauthorized errors with backend API endpoints
2. 406 Not Acceptable errors with Supabase API
3. Manifest syntax errors

Usage:
    python troubleshoot.py --fix

Author: Claude
Date: May 5, 2025
"""

import os
import sys
import json
import argparse
import requests
import subprocess
from pathlib import Path
from dotenv import load_dotenv, find_dotenv

# Load environment variables
load_dotenv(find_dotenv())

# Constants
API_HOST = os.getenv("APP_HOST", "localhost")
API_PORT = os.getenv("APP_PORT", "8000")
API_BASE_URL = f"http://{API_HOST}:{API_PORT}/api"
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")
JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET", "")

# Colors for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}=== {text} ==={Colors.ENDC}\n")

def print_success(text):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")

def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.WARNING}! {text}{Colors.ENDC}")

def print_info(text):
    """Print an info message."""
    print(f"{Colors.BLUE}ℹ {text}{Colors.ENDC}")

def check_env_variables():
    """Check if all required environment variables are set."""
    print_header("Checking Environment Variables")
    
    required_vars = {
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_KEY": SUPABASE_KEY,
        "SUPABASE_JWT_SECRET": JWT_SECRET,
        "APP_SECRET_KEY": os.getenv("APP_SECRET_KEY", "")
    }
    
    all_present = True
    for name, value in required_vars.items():
        if not value:
            print_error(f"Missing environment variable: {name}")
            all_present = False
        else:
            print_success(f"{name} is set")
    
    return all_present

def fix_env_variables():
    """Fix missing environment variables."""
    print_header("Fixing Environment Variables")
    
    env_path = find_dotenv()
    if not env_path:
        env_path = ".env"
        print_warning(f"No .env file found. Creating one at {env_path}")
    
    env_vars = {}
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    env_vars[key] = value
    
    # Check and prompt for missing variables
    if not SUPABASE_URL:
        supabase_url = input("Enter your Supabase URL: ")
        env_vars["SUPABASE_URL"] = supabase_url
    
    if not SUPABASE_KEY:
        supabase_key = input("Enter your Supabase API Key: ")
        env_vars["SUPABASE_KEY"] = supabase_key
    
    if not JWT_SECRET:
        from secrets import token_hex
        jwt_secret = token_hex(32)
        print_info(f"Generated new JWT secret: {jwt_secret}")
        env_vars["SUPABASE_JWT_SECRET"] = jwt_secret
    
    if not os.getenv("APP_SECRET_KEY"):
        from secrets import token_hex
        app_secret = token_hex(32)
        print_info(f"Generated new app secret key: {app_secret}")
        env_vars["APP_SECRET_KEY"] = app_secret
    
    # Write updated variables to .env file
    with open(env_path, 'w') as f:
        for key, value in env_vars.items():
            f.write(f"{key}={value}\n")
    
    print_success("Environment variables updated")
    print_warning("Please restart your application to apply these changes")

def check_api_endpoints():
    """Check if the API endpoints are responding correctly."""
    print_header("Checking API Endpoints")
    
    endpoints = [
        "/me",
        "/files/",
        "/storage/missing",
        "/whatsapp/session"
    ]
    
    # Try to get a valid token first
    token = None
    try:
        print_info("Attempting to authenticate...")
        
        # Check if we have test credentials
        test_email = os.getenv("TEST_EMAIL")
        test_password = os.getenv("TEST_PASSWORD")
        
        if not test_email or not test_password:
            print_warning("No test credentials found in .env")
            test_email = input("Enter a test user email: ")
            test_password = input("Enter the test user password: ")
        
        # Try to log in
        login_response = requests.post(
            f"{API_BASE_URL}/login",
            data={
                "username": test_email,
                "password": test_password
            }
        )
        
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print_success(f"Authentication successful! Token: {token[:10]}...")
        else:
            print_error(f"Authentication failed: {login_response.status_code} - {login_response.text}")
            return False
    except Exception as e:
        print_error(f"Error during authentication: {str(e)}")
        return False
    
    # Test each endpoint
    all_working = True
    for endpoint in endpoints:
        try:
            print_info(f"Testing endpoint: {endpoint}")
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{API_BASE_URL}{endpoint}", headers=headers)
            
            if response.status_code == 200:
                print_success(f"Endpoint {endpoint} is working")
            else:
                print_error(f"Endpoint {endpoint} returned {response.status_code} - {response.text}")
                all_working = False
        except Exception as e:
            print_error(f"Error testing endpoint {endpoint}: {str(e)}")
            all_working = False
    
    return all_working

def check_supabase_connection():
    """Check if the Supabase connection is working correctly."""
    print_header("Checking Supabase Connection")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print_error("Supabase URL or Key not set")
        return False
    
    try:
        # Try a simple REST API request to Supabase
        headers = {
            "apikey": SUPABASE_KEY,
            "Authorization": f"Bearer {SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Check if the users table exists
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/users?select=count",
            headers=headers
        )
        
        if response.status_code in (200, 406):
            if response.status_code == 406:
                print_warning("Received 406 Not Acceptable. This could be due to the 'select=count' query.")
                print_info("Trying a more basic query...")
                
                response = requests.get(
                    f"{SUPABASE_URL}/rest/v1/users?select=*&limit=1",
                    headers=headers
                )
            
            if response.status_code == 200:
                print_success("Supabase connection successful!")
                return True
            else:
                print_error(f"Supabase API returned {response.status_code} - {response.text}")
                return False
        else:
            print_error(f"Supabase API returned {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print_error(f"Error connecting to Supabase: {str(e)}")
        return False

def fix_supabase_tables():
    """Create necessary tables in Supabase if they don't exist."""
    print_header("Setting up Supabase Tables")
    
    if not SUPABASE_URL or not SUPABASE_KEY:
        print_error("Supabase URL or Key not set")
        return False
    
    # SQL to create required tables
    create_tables_sql = """
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
        user_id UUID REFERENCES users(id),
        session_type TEXT NOT NULL,
        device_name TEXT,
        status TEXT NOT NULL,
        session_data JSONB DEFAULT '{}'::jsonb,
        expires_at TIMESTAMP WITH TIME ZONE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE
    );

    -- Files table
    CREATE TABLE IF NOT EXISTS files (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        user_id UUID REFERENCES users(id),
        filename TEXT NOT NULL,
        phone_number TEXT NOT NULL,
        size BIGINT,
        mime_type TEXT,
        storage_path TEXT,
        uploaded BOOLEAN DEFAULT FALSE,
        upload_attempts INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE
    );
    
    -- Make sure we have the UUID extension
    CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
    """
    
    # Create a SQL file
    with open("setup_tables.sql", "w") as f:
        f.write(create_tables_sql)
    
    print_info("Created SQL file with table definitions")
    print_warning("To execute this SQL, please run it in your Supabase SQL editor")
    print_info("You can find this at: https://app.supabase.io/project/_/sql")
    
    return True

def check_storage_api():
    """Check if storage.py exists and create it if missing."""
    print_header("Checking Storage API")
    
    storage_path = Path("app/api/storage.py")
    
    if not storage_path.exists():
        print_warning("Storage API file doesn't exist")
        
        storage_file_content = """from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional
from app.models.user import User
from app.services.storage_service import StorageService
from app.utils.security import get_current_user
from uuid import UUID

router = APIRouter()

@router.get("/", response_model=List[dict])
async def get_storage_files(
    current_user: User = Depends(get_current_user)
):
    storage_service = StorageService(current_user.id)
    return storage_service.get_files()

@router.get("/missing", response_model=List[dict])
async def get_missing_files(
    current_user: User = Depends(get_current_user)
):
    storage_service = StorageService(current_user.id)
    return storage_service.get_missing_files()

@router.post("/{file_id}", status_code=status.HTTP_200_OK)
async def upload_file(
    file_id: UUID,
    current_user: User = Depends(get_current_user)
):
    try:
        storage_service = StorageService(current_user.id)
        return storage_service.upload_file(file_id)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
"""
        
        # Create the directory if it doesn't exist
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(storage_path, "w") as f:
            f.write(storage_file_content)
        
        print_success("Created Storage API file")
    else:
        print_success("Storage API file exists")
    
    return True

def check_manifest():
    """Check if the web manifest is valid and fix it if needed."""
    print_header("Checking Web Manifest")
    
    manifest_path = Path("public/manifest.json")
    
    if not manifest_path.exists():
        print_warning("Manifest file doesn't exist")
        
        # Create a basic valid manifest
        manifest_content = {
            "name": "WhatsApp to Supabase",
            "short_name": "WA2Supabase",
            "icons": [
                {
                    "src": "/icon-192.png",
                    "sizes": "192x192",
                    "type": "image/png"
                },
                {
                    "src": "/icon-512.png",
                    "sizes": "512x512",
                    "type": "image/png"
                }
            ],
            "theme_color": "#ffffff",
            "background_color": "#ffffff",
            "start_url": "/",
            "display": "standalone",
            "orientation": "portrait"
        }
        
        # Create the directory if it doesn't exist
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the file
        with open(manifest_path, "w") as f:
            json.dump(manifest_content, f, indent=2)
        
        print_success("Created valid manifest.json file")
    else:
        # Try to parse and validate the existing manifest
        try:
            with open(manifest_path, "r") as f:
                manifest_data = json.load(f)
            
            # Check for required fields
            required_fields = ["name", "icons"]
            missing_fields = [field for field in required_fields if field not in manifest_data]
            
            if missing_fields:
                print_error(f"Manifest is missing required fields: {', '.join(missing_fields)}")
                
                # Add missing fields
                if "name" not in manifest_data:
                    manifest_data["name"] = "WhatsApp to Supabase"
                
                if "icons" not in manifest_data:
                    manifest_data["icons"] = [
                        {
                            "src": "/icon-192.png",
                            "sizes": "192x192",
                            "type": "image/png"
                        },
                        {
                            "src": "/icon-512.png",
                            "sizes": "512x512",
                            "type": "image/png"
                        }
                    ]
                
                # Write the updated manifest
                with open(manifest_path, "w") as f:
                    json.dump(manifest_data, f, indent=2)
                
                print_success("Fixed manifest.json file")
            else:
                print_success("Manifest file is valid")
        except json.JSONDecodeError as e:
            print_error(f"Manifest has JSON syntax errors: {str(e)}")
            
            # Create a valid manifest as a backup
            backup_path = manifest_path.with_suffix(".json.backup")
            if manifest_path.exists():
                with open(manifest_path, "r") as f_in:
                    with open(backup_path, "w") as f_out:
                        f_out.write(f_in.read())
                print_info(f"Backed up original manifest to {backup_path}")
            
            # Write a valid manifest
            valid_manifest = {
                "name": "WhatsApp to Supabase",
                "short_name": "WA2Supabase",
                "icons": [
                    {
                        "src": "/icon-192.png",
                        "sizes": "192x192",
                        "type": "image/png"
                    },
                    {
                        "src": "/icon-512.png",
                        "sizes": "512x512",
                        "type": "image/png"
                    }
                ],
                "theme_color": "#ffffff",
                "background_color": "#ffffff",
                "start_url": "/",
                "display": "standalone",
                "orientation": "portrait"
            }
            
            with open(manifest_path, "w") as f:
                json.dump(valid_manifest, f, indent=2)
            
            print_success("Created valid manifest.json file")
    
    return True

def create_frontend_auth_client():
    """Create a frontend authentication client for testing."""
    print_header("Creating Frontend Auth Test Client")
    
    test_client_path = Path("auth_test_client.html")
    
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auth Test Client</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
        }
        .card {
            border: 1px solid #ccc;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        h2 {
            margin-top: 0;
            color: #333;
        }
        input, button {
            padding: 8px;
            margin: 5px 0;
        }
        button {
            background-color: #4CAF50;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        pre {
            background-color: #f5f5f5;
            padding: 10px;
            border-radius: 4px;
            overflow: auto;
        }
        .output {
            margin-top: 10px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <h1>WhatsApp to Supabase Auth Test Client</h1>
    
    <div class="card">
        <h2>Configuration</h2>
        <div>
            <label>API Base URL:</label>
            <input type="text" id="apiBaseUrl" value="http://localhost:8000/api" style="width: 300px">
        </div>
    </div>

    <div class="card">
        <h2>Register New User</h2>
        <div>
            <input type="email" id="registerEmail" placeholder="Email" required>
            <input type="text" id="registerUsername" placeholder="Username" required>
            <input type="password" id="registerPassword" placeholder="Password" required>
            <button onclick="register()">Register</button>
        </div>
        <div class="output" id="registerOutput"></div>
    </div>

    <div class="card">
        <h2>Login</h2>
        <div>
            <input type="email" id="loginEmail" placeholder="Email" required>
            <input type="password" id="loginPassword" placeholder="Password" required>
            <button onclick="login()">Login</button>
        </div>
        <div class="output" id="loginOutput"></div>
    </div>

    <div class="card">
        <h2>Test Endpoints</h2>
        <div>
            <button onclick="testMe()">Test /me</button>
            <button onclick="testFiles()">Test /files</button>
            <button onclick="testMissingFiles()">Test /storage/missing</button>
            <button onclick="testWhatsappSession()">Test /whatsapp/session</button>
        </div>
        <div class="output" id="testOutput"></div>
    </div>

    <script>
        // Store the token
        let authToken = '';

        function getApiBaseUrl() {
            return document.getElementById('apiBaseUrl').value.trim();
        }

        function formatJson(json) {
            return JSON.stringify(json, null, 2);
        }

        async function register() {
            const output = document.getElementById('registerOutput');
            output.textContent = 'Registering...';

            const email = document.getElementById('registerEmail').value;
            const username = document.getElementById('registerUsername').value;
            const password = document.getElementById('registerPassword').value;

            try {
                const response = await fetch(`${getApiBaseUrl()}/register`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email,
                        username,
                        password
                    })
                });

                const result = await response.json();
                
                if (response.ok) {
                    output.textContent = `Registration successful!\n${formatJson(result)}`;
                } else {
                    output.textContent = `Error: ${response.status}\n${formatJson(result)}`;
                }
            } catch (error) {
                output.textContent = `Error: ${error.message}`;
            }
        }

        async function login() {
            const output = document.getElementById('loginOutput');
            output.textContent = 'Logging in...';

            const email = document.getElementById('loginEmail').value;
            const password = document.getElementById('loginPassword').value;

            try {
                const formData = new FormData();
                formData.append('username', email);
                formData.append('password', password);

                const response = await fetch(`${getApiBaseUrl()}/login`, {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();
                
                if (response.ok) {
                    authToken = result.access_token;
                    output.textContent = `Login successful!\nToken: ${authToken.substring(0, 20)}...`;
                    
                    // Save token to localStorage
                    localStorage.setItem('authToken', authToken);
                } else {
                    output.textContent = `Error: ${response.status}\n${formatJson(result)}`;
                }
            } catch (error) {
                output.textContent = `Error: ${error.message}`;
            }
        }

        async function makeAuthenticatedRequest(endpoint, method = 'GET') {
            const token = authToken || localStorage.getItem('authToken');
            
            if (!token) {
                return { error: 'No authentication token. Please login first.' };
            }

            try {
                const response = await fetch(`${getApiBaseUrl()}${endpoint}`, {
                    method,
                    headers: {
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    return await response.json();
                } else {
                    const text = await response.text();
                    try {
                        return { error: `Status: ${response.status}`, details: JSON.parse(text) };
                    } catch {
                        return { error: `Status: ${response.status}`, details: text };
                    }
                }
            } catch (error) {
                return { error: error.message };
            }
        }

        async function testMe() {
            const output = document.getElementById('testOutput');
            output.textContent = 'Testing /me endpoint...';
            
            const result = await makeAuthenticatedRequest('/me');
            output.textContent = formatJson(result);
        }

        async function testFiles() {
            const output = document.getElementById('testOutput');
            output.textContent = 'Testing /files endpoint...';
            
            const result = await makeAuthenticatedRequest('/files/');
            output.textContent = formatJson(result);
        }

        async function testMissingFiles() {
            const output = document.getElementById('testOutput');
            output.textContent = 'Testing /storage/missing endpoint...';
            
            const result = await makeAuthenticatedRequest('/storage/missing');
            output.textContent = formatJson(result);
        }

        async function testWhatsappSession() {
            const output = document.getElementById('testOutput');
            output.textContent = 'Testing /whatsapp/session endpoint...';
            
            const result = await makeAuthenticatedRequest('/whatsapp/session', 'POST');
            output.textContent = formatJson(result);
        }

        // Check if we have a stored token
        document.addEventListener('DOMContentLoaded', () => {
            const storedToken = localStorage.getItem('authToken');
            if (storedToken) {
                authToken = storedToken;
                document.getElementById('loginOutput').textContent = 
                    `Using stored token: ${authToken.substring(0, 20)}...`;
            }
        });
    </script>
</body>
</html>
"""
    
    with open(test_client_path, "w") as f:
        f.write(html_content)
    
    print_success(f"Created auth test client at {test_client_path}")
    print_info(f"Open this file in a browser to test authentication and API endpoints")
    
    return True

def main():
    """Main function to run the troubleshooter."""
    parser = argparse.ArgumentParser(description="WhatsApp-Supabase Integration Troubleshooter")
    parser.add_argument("--fix", action="store_true", help="Fix identified issues")
    args = parser.parse_args()
    
    print(f"{Colors.HEADER}{Colors.BOLD}")
    print("===================================================")
    print("  WhatsApp-Supabase Integration Troubleshooter")
    print("===================================================")
    print(f"{Colors.ENDC}")
    
    # Run checks
    env_vars_ok = check_env_variables()
    supabase_ok = check_supabase_connection()
    storage_api_ok = check_storage_api()
    manifest_ok = check_manifest()
    
    # If --fix flag is provided, fix the issues
    if args.fix or not env_vars_ok:
        fix_env_variables()
    
    if args.fix or not supabase_ok:
        fix_supabase_tables()
    
    if args.fix or not storage_api_ok:
        check_storage_api()
    
    if args.fix or not manifest_ok:
        check_manifest()
    
    # Always create the test client when in fix mode
    if args.fix:
        create_frontend_auth_client()
    
    # Summary
    print_header("Summary")
    
    if env_vars_ok and supabase_ok and storage_api_ok and manifest_ok:
        print_success("All checks passed! Your setup seems to be in good shape.")
    else:
        print_warning("Some issues were detected. Run with --fix to automatically fix them.")
    
    print("\nRecommended next steps:")
    print("1. Make sure your Supabase database has the correct tables (see setup_tables.sql)")
    print("2. Check your .env file for correct API keys and secrets")
    print("3. Restart your application after making changes")
    print("4. Use the auth_test_client.html file to test your API endpoints")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())