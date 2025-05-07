#!/usr/bin/env python3
"""
WhatsApp File Sync Diagnostic Script

This script diagnoses issues with WhatsApp file synchronization when the 
session is already active but files aren't being synchronized properly.
"""

import os
import sys
import json
import requests
import time
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configuration 
API_BASE_URL = "http://localhost:8000/api"
LOG_FILE = "whatsapp_sync_debug.log"

# Set up logging
def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"{timestamp} | {message}"
    print(log_entry)
    
    with open(LOG_FILE, "a") as f:
        f.write(log_entry + "\n")

# Get authentication token
def get_auth_token() -> str:
    """Get authentication token from environment or prompt user"""
    token = os.environ.get("API_TOKEN")
    
    if not token:
        token = input("Enter your authentication token: ")
    
    return token

# Test API connectivity
def test_api_connection(token: str) -> bool:
    """Test if the API is reachable and authentication is working"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        log("Testing API connection...")
        response = requests.get(f"{API_BASE_URL}/me", headers=headers)
        
        if response.status_code == 200:
            user_data = response.json()
            log(f"API connection successful. Logged in as: {user_data.get('username', 'Unknown')}")
            return True
        else:
            log(f"API connection failed. Status code: {response.status_code}")
            log(f"Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        log(f"API connection error: {str(e)}")
        return False

# Check WhatsApp session status
def check_whatsapp_session(token: str) -> Dict[str, Any]:
    """Check if there's an active WhatsApp session"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # First, try to get all sessions
        log("Checking for active WhatsApp sessions...")
        
        # Create a new session if none exists
        response = requests.post(f"{API_BASE_URL}/whatsapp/session", headers=headers)
        
        if response.status_code == 201:
            session_data = response.json()
            log(f"Session created or already exists with ID: {session_data.get('id', 'Unknown')}")
            
            # Wait a bit to let the session initialize
            time.sleep(2)
            
            # Check session status
            session_id = session_data.get('session_id')
            if session_id:
                status_response = requests.get(
                    f"{API_BASE_URL}/whatsapp/session/{session_id}", 
                    headers=headers
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    log(f"Session status: {status_data.get('status', 'Unknown')}")
                    return status_data
            
            return session_data
        else:
            log(f"Failed to create session. Status code: {response.status_code}")
            log(f"Response: {response.text}")
            return {}
            
    except requests.RequestException as e:
        log(f"Error checking WhatsApp session: {str(e)}")
        return {}

# Check for pending files
def check_pending_files(token: str) -> List[Dict[str, Any]]:
    """Check for pending files that need to be synchronized"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        log("Checking for pending files...")
        response = requests.get(f"{API_BASE_URL}/storage/missing", headers=headers)
        
        if response.status_code == 200:
            files_data = response.json()
            
            if isinstance(files_data, list):
                log(f"Found {len(files_data)} pending files")
                return files_data
            else:
                # Some APIs return a wrapper object
                files = files_data.get('files', [])
                log(f"Found {len(files)} pending files")
                return files
        else:
            log(f"Failed to get pending files. Status code: {response.status_code}")
            log(f"Response: {response.text}")
            return []
            
    except requests.RequestException as e:
        log(f"Error checking pending files: {str(e)}")
        return []

# Download files from WhatsApp
def download_whatsapp_files(token: str) -> bool:
    """Try to download files from WhatsApp"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        log("Attempting to download files from WhatsApp...")
        response = requests.post(f"{API_BASE_URL}/whatsapp/download", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            files = result.get('files', [])
            log(f"Download successful. {len(files)} files downloaded.")
            return True
        else:
            log(f"Failed to download files. Status code: {response.status_code}")
            log(f"Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        log(f"Error downloading files: {str(e)}")
        return False

# Sync files to storage
def sync_files(token: str) -> bool:
    """Try to sync files to storage"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        log("Attempting to sync files to storage...")
        response = requests.post(f"{API_BASE_URL}/files/sync", headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            log(f"Sync result: {json.dumps(result, indent=2)}")
            return True
        else:
            log(f"Failed to sync files. Status code: {response.status_code}")
            log(f"Response: {response.text}")
            return False
            
    except requests.RequestException as e:
        log(f"Error syncing files: {str(e)}")
        return False

# Main diagnostic function
def run_diagnostics():
    """Run a complete diagnostic"""
    log("Starting WhatsApp file sync diagnostics")
    
    # Get authentication token
    token = get_auth_token()
    
    # Check API connection
    if not test_api_connection(token):
        log("ERROR: Cannot connect to API or authentication failed.")
        log("Please check that the API is running and your token is valid.")
        return
    
    # Check WhatsApp session
    session_info = check_whatsapp_session(token)
    
    if not session_info:
        log("ERROR: Failed to create or check WhatsApp session.")
        log("Please check the WhatsApp session logs on the server.")
        return
    
    # Check for pending files
    pending_files = check_pending_files(token)
    
    if not pending_files:
        log("No pending files found to sync.")
        log("Attempting to download new files from WhatsApp...")
        
        # Try to download files
        if not download_whatsapp_files(token):
            log("ERROR: Failed to download files from WhatsApp.")
            log("The WhatsApp session might not be properly authenticated or there are no new files.")
            log("Check the WhatsApp web UI to see if there are any files to download.")
            return
        
        # Check again for pending files after download
        pending_files = check_pending_files(token)
        
        if not pending_files:
            log("Still no pending files found after download attempt.")
            log("This could mean: ")
            log("1. There are no new files in your WhatsApp")
            log("2. The WhatsApp session is not properly scanning for files")
            log("3. Files were downloaded but already uploaded to storage")
            return
    
    # Try to sync files
    if sync_files(token):
        log("File synchronization was successful!")
        
        # Check if there are still pending files
        remaining_files = check_pending_files(token)
        
        if remaining_files:
            log(f"WARNING: There are still {len(remaining_files)} files pending after sync.")
            log("Some files might have failed to upload.")
        else:
            log("All files have been synchronized successfully.")
    else:
        log("ERROR: File synchronization failed.")
        log("Check the server logs for more details.")
    
    log("Diagnostic complete.")

# Run the script
if __name__ == "__main__":
    run_diagnostics()