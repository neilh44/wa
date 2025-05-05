#!/bin/bash

# WhatsApp Valid QR Code Fix
# This script fixes the invalid QR code issue

echo "========== WhatsApp Valid QR Code Fix =========="
echo "Fixing invalid QR code issue..."

# Navigate to the backend directory
cd whatsapp-supabase-backend || { echo "Backend directory not found!"; exit 1; }

# 1. Update the WhatsAppService to extract the actual QR code data properly
cat > app/services/whatsapp_service.py << 'EOL'
import os
import time
import base64
import platform
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from app.utils.logger import get_logger
from app.models.session import Session, SessionStatus
from app.config import settings
from supabase import create_client, Client

logger = get_logger()
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

class WhatsAppService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id
        self.data_dir = os.path.join(settings.whatsapp_data_dir, str(user_id))
        os.makedirs(self.data_dir, exist_ok=True)
        self.driver = None
        self.session_id = None
    
    def initialize_session(self) -> Dict[str, Any]:
        """Initialize a WhatsApp session and return QR code data."""
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"--user-data-dir={self.data_dir}")
            
            # Simple driver setup that works with all webdriver-manager versions
            driver_path = ChromeDriverManager().install()
            logger.info(f"Using ChromeDriver at path: {driver_path}")
            service = Service(executable_path=driver_path)
            
            # Initialize the Chrome driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Open WhatsApp Web
            self.driver.get("https://web.whatsapp.com/")
            
            # Create a new session record
            session_data = {
                "user_id": str(self.user_id),
                "session_type": "whatsapp",
                "device_name": "Chrome",
                "status": SessionStatus.INACTIVE,
                "session_data": {}
            }
            
            # Save to database
            result = supabase.table("sessions").insert(session_data).execute()
            self.session_id = result.data[0]["id"] if result.data else None
            
            # Wait for QR code
            qr_code_element = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "canvas"))
            )
            
            # Extract the QR code image data directly as base64
            # This is the correct way to get a valid WhatsApp QR code
            try:
                qr_code_data = self.driver.execute_script("""
                    var canvas = arguments[0];
                    return canvas.toDataURL('image/png');
                """, qr_code_element)
                
                logger.info(f"QR code data length: {len(qr_code_data) if qr_code_data else 0}")
                
                # Store the QR data in the session
                supabase.table("sessions").update({
                    "session_data": {"qr_code_data": qr_code_data},
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(self.session_id)).execute()
                
                return {
                    "qr_available": True,
                    "session_id": self.session_id,
                    "qr_data": qr_code_data
                }
            except Exception as e:
                logger.error(f"Error extracting QR code data: {e}")
                return {
                    "qr_available": False,
                    "error": f"Failed to extract QR code: {str(e)}"
                }
                
        except Exception as e:
            logger.error(f"Error creating WhatsApp session: {e}")
            return {"qr_available": False, "error": str(e)}
    
    def check_session_status(self, session_id: UUID) -> Dict[str, Any]:
        """Check if the session is authenticated."""
        # Query session from database
        session_query = supabase.table("sessions").select("*").eq("id", str(session_id)).execute()
        
        if not session_query.data:
            return {"status": "not_found"}
        
        session_data = session_query.data[0]
        
        # If driver is not initialized, initialize it
        if not self.driver:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument(f"--user-data-dir={self.data_dir}")
            
            # Use a simpler approach that works with older webdriver-manager versions
            driver_path = ChromeDriverManager().install()
            service = Service(executable_path=driver_path)
            
            # Initialize the Chrome driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Open WhatsApp Web
            self.driver.get("https://web.whatsapp.com/")
        
        try:
            # Check if logged in by looking for a common element that appears after login
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "[data-icon='chat']"))
            )
            
            # Update session status in database
            supabase.table("sessions").update({
                "status": SessionStatus.ACTIVE,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(session_id)).execute()
            
            return {"status": "authenticated"}
        except Exception as e:
            logger.error(f"Session not authenticated: {e}")
            return {"status": "not_authenticated"}
    
    def download_files(self) -> List[Dict[str, Any]]:
        """Download files from WhatsApp and return file info."""
        # This is a simplified implementation
        # In a real app, you'd need to monitor for new messages and download files
        
        # Placeholder for downloaded files
        downloaded_files = []
        
        # Update files in database
        for file_info in downloaded_files:
            file_data = {
                "user_id": str(self.user_id),
                "filename": file_info["filename"],
                "phone_number": file_info["phone_number"],
                "size": file_info["size"],
                "mime_type": file_info["mime_type"],
                "storage_path": file_info["local_path"],
                "uploaded": False
            }
            
            supabase.table("files").insert(file_data).execute()
        
        return downloaded_files
    
    def close_session(self):
        """Close the WhatsApp session."""
        if self.driver:
            self.driver.quit()
            self.driver = None
        
        if self.session_id:
            # Update session status in database
            supabase.table("sessions").update({
                "status": SessionStatus.INACTIVE,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(self.session_id)).execute()
EOL

echo "✅ Updated WhatsAppService to extract QR code data properly"

# 2. Create a modified version of the frontend SessionManager to display the image QR code
cat > frontend-qr-fix.jsx << 'EOL'
// SessionManager.tsx with updated QR code handling
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
  const [qrError, setQrError] = useState<string | null>(null);

  const initializeSession = async () => {
    setLoading(true);
    setQrError(null);
    try {
      const response = await axios.post(config.WHATSAPP.SESSION);
      if (response.data.qr_available) {
        setSession({
          id: response.data.session_id,
          status: 'qr_ready',
          message: 'Please scan the QR code with your WhatsApp',
          qrData: response.data.qr_data // Get actual QR code data from backend
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

  // No need for QRCodeSVG - we'll display the data URL image directly
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
          {session.qrData ? (
            <Box sx={{ p: 2 }}>
              {/* Display the QR code as an image instead of using QRCodeSVG */}
              <img 
                src={session.qrData} 
                alt="WhatsApp QR Code" 
                style={{ width: 200, height: 200 }}
              />
              <Typography variant="body2" color="text.secondary" align="center" sx={{ mt: 1 }}>
                Scan with WhatsApp
              </Typography>
            </Box>
          ) : (
            <Paper sx={{ p: 2, width: 200, height: 200, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <CircularProgress />
            </Paper>
          )}
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

echo "✅ Created updated SessionManager component for direct QR code display"

echo -e "\n===== INSTRUCTIONS ====="
echo "1. Update your WhatsAppService in the backend:"
echo "   - Replace app/services/whatsapp_service.py with the updated version"
echo ""
echo "2. Update your SessionManager component in the frontend:"
echo "   - Copy the content from frontend-qr-fix.jsx to src/components/whatsapp/SessionManager.tsx"
echo "   - Note: This version displays the QR code directly as an image instead of using QRCodeSVG"
echo ""
echo "3. Restart your backend server:"
echo "   python -m app.main"
echo ""
echo "4. Restart your frontend development server"
echo ""
echo "WhatsApp valid QR code fix is now complete!"