#!/bin/bash

# WhatsApp Authentication Detection Fix
# This script modifies the WhatsAppService to better detect authentication changes

echo "========== WhatsApp Authentication Detection Fix =========="
echo "Enhancing authentication detection in WhatsAppService..."

# Navigate to the backend directory
cd whatsapp-supabase-backend || { echo "Backend directory not found!"; exit 1; }

# 1. Update the WhatsAppService with improved authentication detection
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
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
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
    
    def _get_session_data(self, session_id: str) -> Dict[str, Any]:
        """Get session data from database."""
        try:
            session_query = supabase.table("sessions").select("*").eq("id", session_id).execute()
            
            if not session_query.data:
                logger.warning(f"Session not found: {session_id}")
                return {}
            
            return session_query.data[0].get("session_data", {}) or {}
        except Exception as e:
            logger.error(f"Error retrieving session data: {e}")
            return {}
    
    def _update_session_data(self, session_id: str, data: Dict[str, Any]) -> bool:
        """Update session data in database."""
        try:
            # Get current session data
            current_data = self._get_session_data(session_id)
            
            # Merge with new data
            merged_data = {**current_data, **data}
            
            # Update in database
            supabase.table("sessions").update({
                "session_data": merged_data,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", session_id).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error updating session data: {e}")
            return False
    
    def _is_authenticated(self) -> bool:
        """Check if the WhatsApp session is authenticated by looking for multiple indicators."""
        try:
            # Method 1: Check for chat list or main screen elements
            try:
                chat_icon = self.driver.find_element(By.CSS_SELECTOR, "[data-icon='chat']")
                if chat_icon:
                    logger.info("Authentication detected via chat icon")
                    return True
            except NoSuchElementException:
                pass
            
            # Method 2: Check for side panel (contact list)
            try:
                side_panel = self.driver.find_element(By.ID, "pane-side")
                if side_panel:
                    logger.info("Authentication detected via side panel")
                    return True
            except NoSuchElementException:
                pass
                
            # Method 3: Check for absence of QR code
            try:
                qr_code = self.driver.find_element(By.CSS_SELECTOR, "canvas")
                # If QR code is found, not authenticated
                return False
            except NoSuchElementException:
                # If QR code is not found, check for other authentication indicators
                try:
                    # Check for profile or menu buttons that appear after login
                    profile_button = self.driver.find_element(By.CSS_SELECTOR, "[data-icon='menu']")
                    if profile_button:
                        logger.info("Authentication detected via menu icon")
                        return True
                except NoSuchElementException:
                    pass
            
            # Method 4: Check page title
            if "WhatsApp" in self.driver.title and "Login" not in self.driver.title:
                # Take a screenshot for debugging
                try:
                    screenshot_path = os.path.join(self.data_dir, "debug_screenshot.png")
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Saved debug screenshot to {screenshot_path}")
                except Exception as e:
                    logger.error(f"Error saving screenshot: {e}")
                
                # Check page source for indicators
                if "WhatsApp is ready" in self.driver.page_source:
                    logger.info("Authentication detected via page content")
                    return True
                
                # Last resort: check if URL changed from login page
                if "/accept" in self.driver.current_url:
                    logger.info("Authentication detected via URL change")
                    return True
            
            return False
        except Exception as e:
            logger.error(f"Error checking authentication status: {e}")
            return False
    
    def initialize_session(self) -> Dict[str, Any]:
        """Initialize a WhatsApp session and return QR code data."""
        try:
            logger.info(f"Initializing WhatsApp session for user: {self.user_id}")
            
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
            
            # Add a small delay to ensure page loads
            time.sleep(2)
            
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
            
            if not self.session_id:
                logger.error("Failed to create session record")
                return {"qr_available": False, "error": "Failed to create session record"}
            
            # Check if already authenticated
            if self._is_authenticated():
                logger.info("Already authenticated in initialize_session")
                
                # Update session status
                supabase.table("sessions").update({
                    "status": SessionStatus.ACTIVE,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(self.session_id)).execute()
                
                return {
                    "qr_available": False,
                    "session_id": self.session_id,
                    "already_authenticated": True
                }
            
            # Wait for QR code
            try:
                qr_code_element = WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "canvas"))
                )
                
                # Extract the QR code image data directly as base64
                qr_code_data = self.driver.execute_script("""
                    var canvas = arguments[0];
                    return canvas.toDataURL('image/png');
                """, qr_code_element)
                
                logger.info(f"QR code data length: {len(qr_code_data) if qr_code_data else 0}")
                
                # Store the QR data in the session
                self._update_session_data(self.session_id, {"qr_code_data": qr_code_data})
                
                return {
                    "qr_available": True,
                    "session_id": self.session_id,
                    "qr_data": qr_code_data
                }
            except TimeoutException:
                logger.warning("QR code not found within timeout period")
                
                # Check if already logged in again (in case authentication happened during timeout)
                if self._is_authenticated():
                    logger.info("Authentication detected after timeout")
                    
                    # Update session status
                    supabase.table("sessions").update({
                        "status": SessionStatus.ACTIVE,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", str(self.session_id)).execute()
                    
                    return {
                        "qr_available": False,
                        "session_id": self.session_id,
                        "already_authenticated": True
                    }
                
                return {
                    "qr_available": False,
                    "error": "QR code not found within timeout period"
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
        try:
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
                
                # Open WhatsApp Web and wait for it to load
                self.driver.get("https://web.whatsapp.com/")
                time.sleep(3)  # Give the page a moment to load
            
            # Refresh the page to ensure we have the latest state
            try:
                self.driver.refresh()
                time.sleep(3)  # Wait for refresh to complete
            except Exception as e:
                logger.warning(f"Error refreshing page: {e}")
            
            # Check authentication status
            if self._is_authenticated():
                logger.info(f"Session {session_id} is authenticated")
                
                # Update session status in database
                supabase.table("sessions").update({
                    "status": SessionStatus.ACTIVE,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(session_id)).execute()
                
                # Try to get QR data if it exists
                try:
                    session_data = self._get_session_data(str(session_id))
                    qr_data = session_data.get("qr_code_data")
                    
                    return {
                        "status": "authenticated",
                        "qr_data": qr_data if qr_data else None
                    }
                except Exception as e:
                    logger.warning(f"Error retrieving QR data: {e}")
                    return {"status": "authenticated"}
            
            # Not authenticated, check for QR code
            try:
                qr_code_element = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "canvas"))
                )
                
                # Extract QR code if possible
                try:
                    qr_code_data = self.driver.execute_script("""
                        var canvas = arguments[0];
                        return canvas.toDataURL('image/png');
                    """, qr_code_element)
                    
                    # Update session data
                    self._update_session_data(str(session_id), {"qr_code_data": qr_code_data})
                    
                    # Take a screenshot for debugging
                    try:
                        screenshot_path = os.path.join(self.data_dir, "qr_screenshot.png")
                        self.driver.save_screenshot(screenshot_path)
                        logger.info(f"Saved QR screenshot to {screenshot_path}")
                    except Exception as e:
                        logger.error(f"Error saving QR screenshot: {e}")
                    
                    return {
                        "status": "not_authenticated",
                        "qr_available": True,
                        "qr_data": qr_code_data
                    }
                except Exception as e:
                    logger.error(f"Error extracting QR code data: {e}")
            except Exception as e:
                logger.warning(f"No QR code found: {e}")
            
            return {"status": "not_authenticated"}
        except Exception as e:
            logger.error(f"Error checking session status: {e}")
            return {"status": "error", "message": str(e)}
    
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

echo "✅ Updated WhatsAppService with improved authentication detection"

# 2. Create a test script to manually check authentication status
cat > test_auth_status.py << 'EOL'
#!/usr/bin/env python3
import os
import sys
import json
import time
from datetime import datetime
from uuid import UUID

# Add the app directory to the Python path
sys.path.insert(0, os.path.abspath('.'))

# Import the WhatsApp service
from app.services.whatsapp_service import WhatsAppService
from app.utils.logger import get_logger

logger = get_logger()

def test_authentication():
    """Test WhatsApp authentication detection"""
    logger.info("Starting WhatsApp authentication testing...")
    
    # Create a test user ID - replace with your actual user ID from logs
    test_user_id = UUID('e4cb8a86-6474-454d-a740-3ae98266a509')  # Update with your user ID
    
    # Initialize the WhatsApp service
    whatsapp_service = WhatsAppService(test_user_id)
    
    # Initialize a session
    logger.info("Initializing WhatsApp session...")
    result = whatsapp_service.initialize_session()
    
    # Print the result
    logger.info(f"Session initialization result: {json.dumps(result, default=str)}")
    
    if 'session_id' in result:
        session_id = result['session_id']
        
        # Loop to check authentication status
        attempts = 0
        while attempts < 10:
            logger.info(f"Checking authentication status (attempt {attempts+1})...")
            status_result = whatsapp_service.check_session_status(session_id)
            logger.info(f"Authentication status: {json.dumps(status_result, default=str)}")
            
            if status_result.get('status') == 'authenticated':
                logger.info("Authentication successful!")
                break
            
            logger.info("Waiting for authentication...")
            time.sleep(5)
            attempts += 1
        
        # Close the session
        whatsapp_service.close_session()
    
    return result

if __name__ == "__main__":
    test_authentication()
EOL

chmod +x test_auth_status.py
echo "✅ Created authentication test script"

# 3. Update the frontend SessionManager to handle authentication
cat > frontend-session-manager-updates.txt << 'EOL'
To update your frontend SessionManager component to better handle authentication:

1. Increase polling frequency for authentication status:
```typescript
// In SessionManager.tsx, increase the polling frequency while waiting for QR scan
useEffect(() => {
  let interval: NodeJS.Timeout;
  
  if (session.id && session.status === 'qr_ready') {
    // Check more frequently (every 2 seconds) to detect authentication faster
    interval = setInterval(checkSessionStatus, 2000);
  }
  
  return () => {
    if (interval) clearInterval(interval);
  };
}, [session.id, session.status]);
```

2. Add more detailed status handling:
```typescript
const checkSessionStatus = async () => {
  if (!session.id) return;
  
  setLoading(true);
  try {
    const response = await axios.get(`${config.WHATSAPP.SESSION}/${session.id}`);
    console.log("Session status response:", response.data); // Add logging
    
    if (response.data.status === 'authenticated') {
      setSession({
        ...session,
        status: 'authenticated',
        message: 'WhatsApp session is active! You can now download files.'
      });
      
      // Play a sound or show notification to alert user
      // You could add a small notification sound here
      try {
        const audio = new Audio('/notification.mp3');
        audio.play();
      } catch (e) {
        console.log('Audio notification not supported');
      }
    } else {
      setSession({
        ...session,
        status: 'not_authenticated',
        message: 'Session is not authenticated, please scan the QR code with WhatsApp'
      });
    }
  } catch (error) {
    console.error("Error checking session status:", error);
    setSession({
      ...session,
      status: 'error',
      message: 'An error occurred while checking the session'
    });
  } finally {
    setLoading(false);
  }
};
```

3. Add a visual indicator when authentication is successful:
```jsx
{session.status === 'authenticated' && (
  <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
    <Alert severity="success" sx={{ width: '100%' }}>
      <AlertTitle>Connected</AlertTitle>
      WhatsApp session is active and ready to use!
    </Alert>
  </Box>
)}
```

4. Consider adding a more obvious UI change on authentication:
```jsx
// At the top of your component:
import { Alert, AlertTitle, CircularProgress, Box, Divider, Paper, Typography } from '@mui/material';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';

// Then in your render function, replace the QR code display with a success message when authenticated:
{session.status === 'qr_ready' && (
  <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center' }}>
    {session.qrData ? (
      <Box sx={{ p: 2 }}>
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

{session.status === 'authenticated' && (
  <Box sx={{ mb: 3, display: 'flex', justifyContent: 'center', flexDirection: 'column', alignItems: 'center' }}>
    <CheckCircleIcon color="success" style={{ fontSize: 80, marginBottom: 16 }} />
    <Typography variant="h6" color="success.main" gutterBottom>
      WhatsApp Connected
    </Typography>
    <Typography variant="body1">
      Your WhatsApp session is active and ready to use
    </Typography>
  </Box>
)}
```
EOL

echo "✅ Created frontend update instructions"

echo -e "\n===== INSTRUCTIONS ====="
echo "1. Apply the backend fixes:"
echo "   - Replace app/services/whatsapp_service.py with the updated version"
echo ""
echo "2. Test authentication detection with the provided script:"
echo "   python test_auth_status.py"
echo ""
echo "3. Update your frontend SessionManager component using the suggestions"
echo "   in frontend-session-manager-updates.txt"
echo ""
echo "4. Restart your backend server:"
echo "   python -m app.main"
echo ""
echo "5. Restart your frontend development server if needed"
echo ""
echo "6. Test the complete flow again - QR code scan should now properly trigger"
echo "   authentication detection and UI updates"
echo ""
echo "WhatsApp authentication detection fix is now complete!"