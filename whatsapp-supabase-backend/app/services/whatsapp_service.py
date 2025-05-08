import os
import re
from uuid import UUID
from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase import create_client, Client  # Add this full import line

from app.utils.logger import get_logger
from app.config import settings
from app.services.whatsapp_authentication import WhatsAppAuthentication
from app.services.file_management import FileManager
from app.services.database_module import DatabaseManager
from app.services.chat_analysis import ChatAnalyzer
from app.services.phone_extraction import PhoneExtractor
from app.services.file_upload import FileUploadService
from app.services.storage_service_helper import StorageServiceHelper
from app.services.supabase_storage_service import SupabaseStorageService

logger = get_logger()

# Initialize supabase client
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)  # Add this line

class WhatsAppService:
    # Rest of your implementation remains the same
    """Main WhatsApp service integrating all components."""
    
    def __init__(self, user_id: UUID, supabase_client):
        """
        Initialize the WhatsApp service with all components.
        
        Args:
            user_id: UUID of the user owning this session
            supabase_client: Initialized Supabase client for database operations
        """
        self.user_id = user_id
        self.supabase = supabase_client
        
        # Create data directory
        self.data_dir = os.path.join(settings.whatsapp_data_dir, str(user_id))
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize storage services
        supabase_storage = SupabaseStorageService(supabase_client)
        self.storage_helper = StorageServiceHelper(supabase_storage)
        
        # Initialize file upload service
        self.file_upload_service = FileUploadService(supabase_client)
        
        # Initialize components
        self.auth_service = WhatsAppAuthentication(user_id, self.data_dir, supabase_client)
        self.file_manager = FileManager(user_id, self.data_dir)
        self.db_manager = DatabaseManager(supabase_client, user_id)
        self.phone_extractor = PhoneExtractor()
        
        # Connect components
        self.driver = None
        self.session_id = None
        self.chat_analyzer = None
        
        logger.info(f"WhatsApp service initialized for user {user_id}")
    
    # Authentication methods
    def initialize_session(self) -> Dict[str, Any]:
        """Initialize a WhatsApp session and return QR code data."""
        logger.info(f"Initializing WhatsApp session for user {self.user_id}")
        result = self.auth_service.initialize_session()
        
        # Store references
        self.driver = self.auth_service.driver
        self.session_id = self.auth_service.session_id
        
        # Initialize chat analyzer if driver is available
        if self.driver:
            self.chat_analyzer = ChatAnalyzer(self.driver)
        
        return result
    
    def check_session_status(self, session_id: UUID) -> Dict[str, Any]:
        """Check if the session is authenticated."""
        logger.info(f"Checking session status for session {session_id}")
        result = self.auth_service.check_session_status(session_id)
        
        # Update driver reference
        self.driver = self.auth_service.driver
        
        # Initialize chat analyzer if driver is available
        if self.driver and not self.chat_analyzer:
            self.chat_analyzer = ChatAnalyzer(self.driver)
        
        return result
    
    def close_session(self):
        """Close the WhatsApp session."""
        logger.info(f"Closing session for user {self.user_id}")
        self.auth_service.close_session()
        self.driver = None
        self.chat_analyzer = None
    
    # File management methods
    def download_files(self, auto_upload: bool = False) -> Dict[str, Any]:
        """
        Scan for WhatsApp files and add them to the database.
        
        Args:
            auto_upload: Whether to automatically upload files after download
        """
        logger.info(f"Starting file download scan for user {self.user_id}")
        
        # Get active chats for better phone number extraction
        active_chats = {}
        if self.chat_analyzer:
            try:
                active_chats = self.chat_analyzer.extract_active_chats()
                logger.info(f"Found {len(active_chats)} active chats for context")
            except Exception as e:
                logger.error(f"Error extracting active chats: {str(e)}")
        
        # Scan for files
        scan_result = self.file_manager.scan_whatsapp_files(active_chats)
        
        # Add files to database
        if scan_result["files"]:
            try:
                self.db_manager.add_files_to_database(scan_result["files"])
                logger.info(f"Added {len(scan_result['files'])} files to database")
            except Exception as e:
                logger.error(f"Error adding files to database: {str(e)}")
        
        # Auto-upload if requested
        if auto_upload and scan_result["files"]:
            try:
                upload_result = self.upload_files()
                scan_result["upload_stats"] = upload_result
                logger.info(f"Auto-uploaded files with result: {upload_result}")
            except Exception as e:
                logger.error(f"Error during auto-upload: {str(e)}")
                scan_result["upload_error"] = str(e)
        
        return scan_result
    
    def upload_files(self, file_ids: List[str] = None) -> Dict[str, Any]:
        """
        Upload WhatsApp files to storage.
        
        Args:
            file_ids: Specific file IDs to upload, or None to upload all unuploaded files
        """
        logger.info(f"Starting file upload for user {self.user_id}")
        if file_ids:
            logger.info(f"Uploading specific files: {file_ids}")
        else:
            logger.info(f"Uploading all unuploaded files")
            
        return self.file_upload_service.upload_files(self.user_id, file_ids)
    
    def get_files(self, filter_criteria: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Get WhatsApp files with optional filtering.
        
        Args:
            filter_criteria: Optional dictionary with filter criteria
            limit: Maximum number of files to return
            offset: Offset for pagination
        """
        logger.info(f"Getting files for user {self.user_id} with filters: {filter_criteria}")
        return self.db_manager.get_files(filter_criteria, limit, offset)
    
    def get_file_stats(self) -> Dict[str, Any]:
        """Get statistics about the user's WhatsApp files."""
        logger.info(f"Getting file stats for user {self.user_id}")
        return self.db_manager.get_file_stats()
    
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """Delete a file record from the database."""
        logger.info(f"Deleting file {file_id} for user {self.user_id}")
        return self.db_manager.delete_file(file_id)
    
    def sync_files(self) -> Dict[str, Any]:
        """
        Scan for new WhatsApp files and upload them to storage in one operation.
        
        Returns:
            Dictionary with scan and upload statistics
        """
        logger.info(f"Starting file sync for user {self.user_id}")
        
        # First scan for new files
        scan_result = self.download_files(auto_upload=False)
        
        # Then upload all unuploaded files
        upload_result = self.upload_files()
        
        result = {
            "scan": {
                "files_found": len(scan_result.get("files", [])),
                "stats": scan_result.get("stats", {})
            },
            "upload": upload_result
        }
        
        logger.info(f"File sync complete for user {self.user_id}: found {result['scan']['files_found']} files, " +
                   f"uploaded {upload_result.get('uploaded', 0)} files")
        
        return result
    
    def process_bulk_upload(self, file_paths: List[str], phone_number: str = None) -> Dict[str, Any]:
        """
        Process a bulk upload of files.
        
        Args:
            file_paths: List of file paths to process
            phone_number: Optional phone number to associate with files
            
        Returns:
            Dictionary with process results
        """
        logger.info(f"Processing bulk upload of {len(file_paths)} files for user {self.user_id}")
        
        # Process files
        process_result = self.file_manager.process_bulk_upload(file_paths, phone_number)
        
        # Add to database
        if process_result["files"]:
            try:
                self.db_manager.add_files_to_database(process_result["files"])
                logger.info(f"Added {len(process_result['files'])} files to database from bulk upload")
            except Exception as e:
                logger.error(f"Error adding bulk files to database: {str(e)}")
                process_result["database_error"] = str(e)
        
        # Upload to storage
        try:
            # Extract file IDs from newly added files
            # This requires the database to have returned the IDs
            # If not available, will default to uploading all unuploaded files
            upload_result = self.upload_files()
            process_result["upload_result"] = upload_result
        except Exception as e:
            logger.error(f"Error uploading bulk files: {str(e)}")
            process_result["upload_error"] = str(e)
        
        return process_result

    def update_file_phone_numbers(self) -> Dict[str, Any]:
        """
        Update phone numbers for existing files in the database based on their paths.
        
        Returns:
            Dictionary with update statistics
        """
        logger.info(f"Starting phone number update for user {self.user_id}")
        
        # Get all files with unknown phone numbers
        files = self.db_manager.get_files({"phone_number": "unknown"}, limit=1000, offset=0)
        
        updated_count = 0
        organized_count = 0
        failed_count = 0
        
        for file in files.get("files", []):
            # Try to extract phone number from the full path
            file_path = file.get("storage_path", "")
            if file_path:
                # Try both patterns for phone extraction
                whatsapp_patterns = [
                    r'(\d+)@s\.whatsapp\.net',  # Regular contacts
                    r'(\d+)@status'             # Status updates
                ]
                
                phone_number = None
                for pattern in whatsapp_patterns:
                    folder_match = re.search(pattern, file_path)
                    if folder_match:
                        # Extract phone number
                        phone_number = folder_match.group(1)
                        logger.info(f"Found phone number {phone_number} from pattern {pattern} in path: {file_path}")
                        break
                
                if phone_number:
                    # Update the database entry
                    updated = self.db_manager.update_file(file.get("id"), {
                        "phone_number": phone_number
                    })
                    
                    if updated:
                        updated_count += 1
                        
                        # Reorganize the file
                        media_type = file.get("media_type", "other")
                        filename = file.get("filename", "")
                        
                        # Only reorganize if we have the necessary info
                        if file_path and filename and media_type:
                            try:
                                organized_path = self.file_manager.organize_file_by_phone(
                                    file_path, 
                                    filename, 
                                    phone_number, 
                                    media_type
                                )
                                
                                # Update the organized path if it changed
                                if organized_path and organized_path != file.get("organized_path"):
                                    self.db_manager.update_file(file.get("id"), {
                                        "organized_path": organized_path
                                    })
                                    logger.info(f"Updated organized path for file {file.get('id')} to {organized_path}")
                                    organized_count += 1
                                else:
                                    logger.warning(f"Could not organize or no change needed for file path: {file_path}")
                            except Exception as e:
                                logger.error(f"Error organizing file {file.get('id')}: {str(e)}")
                    else:
                        failed_count += 1
                        logger.warning(f"Failed to update database entry for file {file.get('id')}")
                else:
                    failed_count += 1
                    logger.warning(f"No phone number pattern match found in path: {file_path}")
        
        return {
            "total_files_processed": len(files.get("files", [])),
            "updated_files": updated_count,
            "organized_files": organized_count,
            "failed_updates": failed_count
        }


    @classmethod
    def create_service(cls, user_id: UUID, supabase_client) -> 'WhatsAppService':
        """
        Factory method to create a WhatsApp service instance.
        
        Args:
            user_id: UUID of the user
            supabase_client: Initialized Supabase client
            
        Returns:
            WhatsAppService instance
        """
        try:
            service = cls(user_id, supabase_client)
            return service
        except Exception as e:
            logger.error(f"Error creating WhatsApp service: {str(e)}")
            raise