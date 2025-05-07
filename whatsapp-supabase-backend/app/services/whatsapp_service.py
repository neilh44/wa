import os
import time
import base64
import platform
from datetime import datetime, timedelta
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
import mimetypes
import re

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
    
    def download_files(self) -> Dict[str, Any]:
        """
        Download files from WhatsApp and return file info.
        This method scans directories where WhatsApp Web saves files and records them in the database.
        """
        logger.info(f"Starting WhatsApp file scan for user {self.user_id}")
        
        # Placeholder for downloaded files
        downloaded_files = []
        stats = {
            "images": 0,
            "documents": 0,
            "audio": 0,
            "video": 0,
            "other": 0,
            "total_size": 0
        }
        
        # Create downloads directory if it doesn't exist
        downloads_dir = os.path.join(self.data_dir, "downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        
        # Common WhatsApp Web file storage paths when using Selenium/Chrome
        possible_paths = [
            os.path.join(self.data_dir, "Default", "Downloads"),
            os.path.join(self.data_dir, "Downloads"),
            downloads_dir,
            self.data_dir,  # Root directory
        ]
        
        # Log all directories in the data_dir for debugging
        try:
            if os.path.exists(self.data_dir):
                logger.info(f"Contents of data_dir: {os.listdir(self.data_dir)}")
                
                # Check for Default directory
                default_dir = os.path.join(self.data_dir, "Default")
                if os.path.exists(default_dir):
                    logger.info(f"Contents of Default directory: {os.listdir(default_dir)}")
        except Exception as e:
            logger.error(f"Error listing directories: {str(e)}")
        
        # File type mappings
        file_type_mappings = {
            # Images
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.heic'],
            # Documents
            'document': ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', 
                        '.csv', '.rtf', '.odt', '.ods', '.odp', '.pages', '.numbers', '.key'],
            # Audio
            'audio': ['.mp3', '.wav', '.ogg', '.m4a', '.aac', '.flac', '.opus', '.amr'],
            # Video
            'video': ['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v', '.3gp'],
            # Archives
            'archive': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        }
        
        # Flatten for extension checking
        all_extensions = [ext for exts in file_type_mappings.values() for ext in exts]
        
        # WhatsApp specific file patterns
        whatsapp_patterns = [
            'WhatsApp Image', 'WhatsApp Video', 'WhatsApp Audio', 'WhatsApp Document',
            'WA', 'IMG-', 'VID-', 'AUD-', 'DOC-', 'PTT-'
        ]
        
        # Get existing files from database to avoid duplicates (batch query)
        existing_files = self._get_existing_files()
        existing_paths = {file.get('storage_path', ''): True for file in existing_files}
        
        # Track phone numbers from file naming patterns
        phone_number_map = {}
        
        # Get list of recently active chats if driver is available
        active_chats = {}
        if self.driver and self._is_authenticated():
            try:
                active_chats = self._extract_active_chats()
                logger.info(f"Found {len(active_chats)} active chats")
            except Exception as e:
                logger.error(f"Error extracting active chats: {str(e)}")
        
        # Scan all potential directories
        for base_path in possible_paths:
            if not os.path.exists(base_path):
                logger.debug(f"Path does not exist: {base_path}")
                continue
                
            logger.info(f"Scanning directory: {base_path}")
            
            # Walk through all directories and files
            for root, dirs, files in os.walk(base_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    
                    # Check if file already exists in database
                    if file_path in existing_paths:
                        logger.debug(f"File already exists in database: {file_path}")
                        continue
                    
                    # Skip system files and non-media files
                    file_lower = file.lower()
                    
                    # Check if it's likely a WhatsApp file either by extension or pattern
                    is_valid_extension = any(file_lower.endswith(ext) for ext in all_extensions)
                    is_whatsapp_pattern = any(pattern.lower() in file_lower for pattern in whatsapp_patterns)
                    
                    if not (is_valid_extension or is_whatsapp_pattern):
                        continue
                    
                    logger.info(f"Found potential WhatsApp file: {file}")
                    
                    try:
                        # Get file size and creation time
                        file_size = os.path.getsize(file_path)
                        file_ctime = os.path.getctime(file_path)
                        file_date = datetime.fromtimestamp(file_ctime)
                        
                        # Try to determine mime type
                        mime_type, _ = mimetypes.guess_type(file_path)
                        if not mime_type:
                            # Use a default based on extension
                            mime_type = "application/octet-stream"
                        
                        # Determine media type
                        media_type = 'other'
                        for type_name, extensions in file_type_mappings.items():
                            if any(file_lower.endswith(ext) for ext in extensions):
                                media_type = type_name
                                break
                        
                        # Try to determine phone number from filename or match with active chats
                        phone_number = self._extract_phone_number(file, file_date, active_chats)
                        
                        # Stats tracking
                        stats[media_type if media_type in stats else 'other'] += 1
                        stats['total_size'] += file_size
                        
                        # Create file info dictionary
                        file_info = {
                            "filename": file,
                            "local_path": file_path,
                            "phone_number": phone_number,
                            "size": file_size,
                            "mime_type": mime_type,
                            "media_type": media_type,
                            "created_at": file_date.isoformat()
                        }
                        
                        downloaded_files.append(file_info)
                        
                    except Exception as e:
                        logger.error(f"Error processing file {file_path}: {str(e)}")
        
        # Add files to database in batches
        if downloaded_files:
            try:
                self._add_files_to_database(downloaded_files)
            except Exception as e:
                logger.error(f"Error adding files to database: {str(e)}")
        
        # Log statistics
        logger.info(f"Download scan complete. Found {len(downloaded_files)} new files:")
        logger.info(f"Images: {stats['images']}, Documents: {stats['documents']}, " 
                    f"Audio: {stats['audio']}, Video: {stats['video']}, Other: {stats['other']}")
        logger.info(f"Total size: {stats['total_size'] / (1024 * 1024):.2f} MB")
        
        return {
            "files": downloaded_files,
            "stats": stats
        }

    def _get_existing_files(self) -> List[Dict[str, Any]]:
        """Get existing files from database in a single query."""
        try:
            result = supabase.table("files") \
                .select("storage_path") \
                .eq("user_id", str(self.user_id)) \
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error retrieving existing files: {str(e)}")
            return []

    def _add_files_to_database(self, files: List[Dict[str, Any]]) -> None:
        """Add multiple files to database efficiently."""
        if not files:
            return
            
        # Prepare batch of records
        records = []
        for file_info in files:
            record = {
                "user_id": str(self.user_id),
                "filename": file_info["filename"],
                "phone_number": file_info["phone_number"],
                "size": file_info["size"],
                "mime_type": file_info["mime_type"],
                "storage_path": file_info["local_path"],
                "media_type": file_info.get("media_type", "other"),
                "uploaded": False
            }
            records.append(record)
        
        # Insert in batches of 50 (to avoid large payloads)
        batch_size = 50
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            try:
                result = supabase.table("files").insert(batch).execute()
                logger.info(f"Added batch of {len(batch)} files to database")
            except Exception as e:
                logger.error(f"Error adding batch to database: {str(e)}")

    def _extract_phone_number(self, filename: str, file_date: datetime, active_chats: Dict[str, Any]) -> str:
        """
        Try to extract phone number from filename or match with active chats.
        """
        # Common WhatsApp patterns with phone numbers
        # Example: IMG-20230615-WA0003 (from +1234567890).jpg
        
        # First check for direct phone number in filename
        phone_patterns = [
            r'from \+(\d+)',
            r'from \((\d+)\)',
            r'from (\d{10,})',
            r'(\d{10,})\.', 
            r'WhatsApp.*?(\d{10,})',
        ]
        
        for pattern in phone_patterns:
            matches = re.search(pattern, filename)
            if matches:
                return matches.group(1)
        
        # Try to extract date from filename (like IMG-20230615-WA0003)
        date_match = re.search(r'(\d{8})|\d{6}|\d{4}-\d{2}-\d{2}', filename)
        
        # If we have active chats and a date match, try to find the most active chat around that time
        if active_chats and date_match:
            # Use file creation date for matching with active chats
            # Find the closest chat by timestamp
            closest_chat = None
            closest_diff = float('inf')
            
            for phone, chat_info in active_chats.items():
                if 'last_activity' in chat_info:
                    chat_time = chat_info['last_activity']
                    time_diff = abs((chat_time - file_date).total_seconds())
                    
                    if time_diff < closest_diff:
                        closest_diff = time_diff
                        closest_chat = phone
            
            # If we found a chat with activity within 1 hour, use that phone number
            if closest_chat and closest_diff < 3600:
                return closest_chat
        
        # Default fallback
        return "unknown"

    def _extract_active_chats(self) -> Dict[str, Any]:
        """
        Extract information about active chats from WhatsApp Web.
        Returns a dict of phone numbers with last activity timestamps.
        """
        active_chats = {}
        
        if not self.driver:
            return active_chats
        
        try:
            # Find chat list
            chat_list = self.driver.find_elements(By.CSS_SELECTOR, "div[role='row']")
            
            for chat in chat_list:
                try:
                    # Get chat title (usually contains phone number or name)
                    title_element = chat.find_element(By.CSS_SELECTOR, "span[data-testid='chat-title']")
                    title = title_element.text.strip()
                    
                    # Try to extract timestamp
                    timestamp_element = chat.find_element(By.CSS_SELECTOR, "span[data-testid='chat-timestamp']")
                    timestamp_text = timestamp_element.text.strip()
                    
                    # Parse timestamp (simplified)
                    # Current time as fallback
                    chat_time = datetime.now()
                    
                    # Try to parse common timestamp formats
                    if ":" in timestamp_text:  # Today timestamps like "14:22"
                        hour, minute = map(int, timestamp_text.split(':'))
                        chat_time = chat_time.replace(hour=hour, minute=minute)
                    elif "yesterday" in timestamp_text.lower():
                        chat_time = chat_time - timedelta(days=1)
                    
                    # Extract phone number if possible
                    phone_match = re.search(r'\+(\d+)', title)
                    phone = phone_match.group(1) if phone_match else title
                    
                    active_chats[phone] = {
                        'title': title,
                        'last_activity': chat_time
                    }
                    
                except Exception as e:
                    logger.debug(f"Error processing chat: {str(e)}")
                    continue
                    
            return active_chats
            
        except Exception as e:
            logger.error(f"Error extracting active chats: {str(e)}")
            return active_chats
    
    def _check_file_exists(self, file_path: str) -> bool:
        """Check if a file already exists in the database based on path."""
        # This method is kept for backward compatibility
        try:
            # Query to check if file exists
            result = supabase.table("files") \
                .select("*") \
                .eq("storage_path", file_path) \
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error checking if file exists: {str(e)}")
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
                supabase.table("sessions").update({
                    "status": SessionStatus.INACTIVE,
                    "updated_at": datetime.utcnow().isoformat()
                }).eq("id", str(self.session_id)).execute()
                logger.info(f"Session {self.session_id} marked as inactive")
            except Exception as e:
                logger.error(f"Error updating session status: {e}")