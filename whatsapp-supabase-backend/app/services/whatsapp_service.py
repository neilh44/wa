import os
import time
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
    
    def secure_session_initialization(self, phone_number: str, client_ip: Optional[str] = None) -> Dict[str, Any]:
        """Initialize a secure WhatsApp session with additional validation.
        
        Args:
            phone_number: The phone number for the WhatsApp account
            client_ip: Optional client IP for additional security logging
            
        Returns:
            Session data including QR code information
        """
        logger.info(f"Initializing secure session for phone number {phone_number}")
        
        # Create a new session record with security metadata
        session_data = {
            "user_id": str(self.user_id),
            "session_type": "whatsapp",
            "device_name": "Chrome",
            "status": SessionStatus.INACTIVE,
            "session_data": {
                "phone_number": phone_number,
                "client_ip": client_ip,
                "security_level": "enhanced",
                "created_at": datetime.utcnow().isoformat()
            }
        }
        
        # Save to database
        result = supabase.table("sessions").insert(session_data).execute()
        self.session_id = result.data[0]["id"] if result.data else None
        
        # Initialize the driver with the secure session
        return self._initialize_driver_and_get_qr(self.session_id)
    
    def initialize_session(self) -> Dict[str, Any]:
        """Initialize a standard WhatsApp session and return QR code data."""
        logger.info("Initializing standard session")
        
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
        
        # Initialize the driver with the session
        return self._initialize_driver_and_get_qr(self.session_id)
    
    def _initialize_driver_and_get_qr(self, session_id: UUID) -> Dict[str, Any]:
        """Set up ChromeDriver and get the QR code for WhatsApp Web.
        
        Args:
            session_id: The session ID to associate with this driver instance
            
        Returns:
            Dictionary with QR code data and session information
        """
        try:
            # Setup Chrome options
            chrome_options = Options()
            chrome_options.add_argument("--headless=new")  # Use new headless mode
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1280,720")  # Set window size
            chrome_options.add_argument(f"--user-data-dir={self.data_dir}")
            
            # Use a local ChromeDriver if available
            chrome_driver_path = self._get_chromedriver_path()
            
            if chrome_driver_path and os.path.exists(chrome_driver_path):
                logger.info(f"Using local ChromeDriver from: {chrome_driver_path}")
                service = Service(executable_path=chrome_driver_path)
            else:
                # Set the specific Chrome version for webdriver-manager
                os.environ["WDM_CHROME_VERSION"] = self._get_chrome_version()
                logger.info(f"Setting Chrome version for webdriver-manager: {os.environ.get('WDM_CHROME_VERSION')}")
                service = Service(ChromeDriverManager().install())
            
            # Initialize the driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Set page load timeout
            self.driver.set_page_load_timeout(60)
            
            # Open WhatsApp Web
            logger.info("Opening WhatsApp Web")
            self.driver.get("https://web.whatsapp.com/")
            
            # Wait for QR code or check if already logged in
            try:
                # First check if user is already logged in
                logger.info("Checking if already logged in")
                try:
                    # Check for the main interface element
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "[data-icon='chat']"))
                    )
                    
                    # If we get here, user is already logged in
                    logger.info("User already logged in, no QR code needed")
                    
                    # Update session status
                    supabase.table("sessions").update({
                        "status": SessionStatus.ACTIVE,
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", str(session_id)).execute()
                    
                    return {"already_authenticated": True, "session_id": session_id}
                    
                except Exception:
                    # Not logged in, continue to QR code detection
                    logger.info("Not logged in, proceeding to QR code detection")
                    pass
                
                # Try different CSS selectors for QR code canvas
                qr_selectors = [
                    "canvas", 
                    "div[data-ref] canvas", 
                    "div[data-testid='qrcode'] canvas",
                    "div._1zCMq canvas",  # Older WhatsApp class
                    "div._2UwZ_ canvas"   # Another possible class
                ]
                
                qr_code_element = None
                for selector in qr_selectors:
                    logger.info(f"Trying QR code selector: {selector}")
                    try:
                        qr_code_element = WebDriverWait(self.driver, 10).until(
                            EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                        )
                        if qr_code_element:
                            logger.info(f"Found QR code with selector: {selector}")
                            break
                    except Exception:
                        continue
                
                if not qr_code_element:
                    logger.error("Could not find QR code element with any selector")
                    # Take a screenshot to debug
                    screenshot_path = os.path.join(self.data_dir, "whatsapp_qr_debug.png")
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Saved debug screenshot to {screenshot_path}")
                    
                    return {"qr_available": False, "error": "QR code element not found", "session_id": session_id}
                
                # Extract QR code data from canvas
                logger.info("Extracting QR code data")
                try:
                    # Get the canvas as base64 image
                    get_qr_script = """
                    var canvas = arguments[0];
                    return canvas.toDataURL('image/png').substring(22);
                    """
                    qr_base64 = self.driver.execute_script(get_qr_script, qr_code_element)
                    
                    # Update session in database to indicate QR is ready
                    supabase.table("sessions").update({
                        "status": SessionStatus.INACTIVE,
                        "session_data": {
                            **self._get_session_data(session_id), 
                            "qr_generated": True,
                            "qr_data": qr_base64
                        },
                        "updated_at": datetime.utcnow().isoformat()
                    }).eq("id", str(session_id)).execute()
                    
                    return {
                        "qr_available": True, 
                        "session_id": session_id,
                        "qr_data": qr_base64
                    }
                except Exception as e:
                    logger.error(f"Error extracting QR code data: {e}")
                    # Take a screenshot to debug
                    screenshot_path = os.path.join(self.data_dir, "whatsapp_qr_debug.png")
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Saved debug screenshot to {screenshot_path}")
                    
                    return {"qr_available": False, "error": f"QR code data extraction failed: {str(e)}", "session_id": session_id}
            except Exception as e:
                logger.error(f"Error detecting QR code: {e}")
                return {"qr_available": False, "error": str(e), "session_id": session_id}
                
        except Exception as e:
            logger.error(f"Error initializing driver: {e}")
            return {"error": str(e), "session_id": session_id}
        
        def _get_chrome_version(self) -> str:
            """Get the installed Chrome version."""
        import subprocess
        import platform
        
        system = platform.system()
        
        try:
            if system == "Darwin":  # macOS
                process = subprocess.Popen(
                    ['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', '--version'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                output, _ = process.communicate()
                version = output.decode('UTF-8').replace('Google Chrome ', '').strip()
                return version.split('.')[0]  # Return major version only (e.g., "135")
            elif system == "Windows":
                # Windows - use registry or WMI query
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Google\Chrome\BLBeacon")
                version, _ = winreg.QueryValueEx(key, "version")
                return version.split('.')[0]
            elif system == "Linux":
                process = subprocess.Popen(
                    ['google-chrome', '--version'],
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE
                )
                output, _ = process.communicate()
                version = output.decode('UTF-8').replace('Google Chrome ', '').strip()
                return version.split('.')[0]
        except Exception as e:
            logger.error(f"Error getting Chrome version: {e}")
            
        # Default to our known version from the error message
        return "135"
    
    def _get_chromedriver_path(self) -> Optional[str]:
        """Get a ChromeDriver path based on common locations."""
        # Check common locations
        common_paths = [
            os.path.join(os.getcwd(), "chromedriver"),  # Project directory
            os.path.join(os.getcwd(), "chromedriver.exe"),
            "/usr/local/bin/chromedriver",  # System paths
            "/usr/bin/chromedriver",
            "C:\\chromedriver.exe",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _get_session_data(self, session_id: UUID) -> Dict[str, Any]:
        """Get current session data from the database."""
        session_query = supabase.table("sessions").select("*").eq("id", str(session_id)).execute()
        
        if not session_query.data:
            return {}
        
        return session_query.data[0].get("session_data", {})
    
    def check_session_status(self, session_id: UUID) -> Dict[str, Any]:
        """Check if the session is authenticated."""
        # Query session from database
        session_query = supabase.table("sessions").select("*").eq("id", str(session_id)).execute()
        
        if not session_query.data:
            return {"status": "not_found"}
        
        session_data = session_query.data[0]
        
        # If driver is not initialized, initialize it
        if not self.driver:
            try:
                # Setup Chrome options
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                chrome_options.add_argument(f"--user-data-dir={self.data_dir}")
                
                # Use a local ChromeDriver if available, otherwise use webdriver-manager
                chrome_driver_path = self._get_chromedriver_path()
                
                if chrome_driver_path and os.path.exists(chrome_driver_path):
                    service = Service(executable_path=chrome_driver_path)
                else:
                    # Set Chrome version for compatibility
                    os.environ["WDM_CHROME_VERSION"] = self._get_chrome_version()
                    service = Service(ChromeDriverManager().install())
                
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                
                # Open WhatsApp Web
                self.driver.get("https://web.whatsapp.com/")
            except Exception as e:
                logger.error(f"Error initializing driver for status check: {e}")
                return {"status": "error", "error": str(e)}
        
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
            logger.warning(f"Session not authenticated: {e}")
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
            try:
                self.driver.quit()
            except Exception as e:
                logger.error(f"Error closing driver: {e}")
            finally:
                self.driver = None
        
        if self.session_id:
            # Update session status in database
            try:
                supabase.table("sessions").update({
                    "status": SessionStatus.INACTIVE,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(self.session_id)).execute()
            except Exception as e:
                logger.error(f"Error updating session status: {e}")