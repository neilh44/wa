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
    
    def initialize_session(self) -> Dict[str, Any]:
        """Initialize a WhatsApp session and return QR code data."""
        # Setup Chrome options
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"--user-data-dir={self.data_dir}")
        
        # Initialize the Chrome driver
        service = Service(ChromeDriverManager().install())
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
        try:
            qr_code_element = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "canvas"))
            )
            # In a real app, you'd extract QR code data from the canvas
            # This is a simplified version
            qr_data = {"qr_available": True, "session_id": self.session_id}
            return qr_data
        except Exception as e:
            logger.error(f"QR code not found: {e}")
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
            
            # Initialize the Chrome driver
            service = Service(ChromeDriverManager().install())
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
        except:
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
