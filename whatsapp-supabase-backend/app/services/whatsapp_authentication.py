import os
import time
from datetime import datetime
from typing import Dict, Any
from uuid import UUID
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from app.models.session import SessionStatus
from app.utils.logger import get_logger

logger = get_logger()

class WhatsAppAuthentication:
    """Handles WhatsApp web authentication and session management."""
    
    def __init__(self, user_id: UUID, data_dir: str, supabase_client):
        self.user_id = user_id
        self.data_dir = data_dir
        self.supabase = supabase_client
        self.driver = None
        self.session_id = None
    
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
            result = self.supabase.table("sessions").insert(session_data).execute()
            self.session_id = result.data[0]["id"] if result.data else None
            
            if not self.session_id:
                logger.error("Failed to create session record")
                return {"qr_available": False, "error": "Failed to create session record"}
            
            # Check if already authenticated
            if self._is_authenticated():
                logger.info("Already authenticated in initialize_session")
                
                # Update session status
                self.supabase.table("sessions").update({
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
                    self.supabase.table("sessions").update({
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
            session_query = self.supabase.table("sessions").select("*").eq("id", str(session_id)).execute()
            
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
                self.supabase.table("sessions").update({
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

    def _get_session_data(self, session_id: str) -> Dict[str, Any]:
        """Get session data from database."""
        try:
            session_query = self.supabase.table("sessions").select("*").eq("id", session_id).execute()
            
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
            self.supabase.table("sessions").update({
                "session_data": merged_data,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", session_id).execute()
            
            return True
        except Exception as e:
            logger.error(f"Error updating session data: {e}")
            return False
            
    def close_session(self):
        """Close the WhatsApp session."""
        logger.info(f"Closing WhatsApp session for user {self.user_id}")
        
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")
            finally:
                self.driver = None
        
        if self.session_id:
            # Update session status in database
            try:
                self.supabase.table("sessions").update({
                    "status": SessionStatus.INACTIVE,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(self.session_id)).execute()
                logger.info(f"Session {self.session_id} marked as inactive")
            except Exception as e:
                logger.error(f"Error updating session status: {e}")