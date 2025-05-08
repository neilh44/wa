import os
import hashlib
from typing import Dict, Any
from datetime import datetime
import mimetypes
from app.utils.logger import get_logger

logger = get_logger()

class StorageServiceHelper:
    """
    Helper class for cloud storage services.
    Handles common functionality like file path generation, metadata extraction, etc.
    """
    def __init__(self, storage_service):
        """
        Initialize with a storage service adapter
        
        Args:
            storage_service: Storage service adapter that implements required methods
        """
        self.storage_service = storage_service
        
    def upload_file(self, file_path: str, user_id: str, metadata: Dict[str, Any] = None) -> str:
        """
        Upload a file to storage with appropriate path and metadata
        
        Args:
            file_path: Path to local file
            user_id: User ID for path organization
            metadata: Additional file metadata
            
        Returns:
            Public URL of the uploaded file
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
            
        # Default metadata
        if metadata is None:
            metadata = {}
            
        # Extract filename
        filename = os.path.basename(file_path)
        
        # Generate file hash if not provided
        if "file_hash" not in metadata:
            file_hash = self._calculate_file_hash(file_path)
            metadata["file_hash"] = file_hash
        else:
            file_hash = metadata["file_hash"]
            
        # Check if file with same hash already exists
        existing_files = self.storage_service.query_files({"metadata": {"file_hash": file_hash}})
        if existing_files:
            logger.info(f"File with hash {file_hash} already exists in storage")
            return existing_files[0].get("storage_url", "")
            
        # Generate destination path
        file_ext = os.path.splitext(filename)[1].lower()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        destination_path = f"{user_id}/{timestamp}_{filename}"
        
        # Guess mime type if not provided
        if "mime_type" not in metadata:
            mime_type, _ = mimetypes.guess_type(file_path)
            if mime_type:
                metadata["mime_type"] = mime_type
            else:
                metadata["mime_type"] = "application/octet-stream"
                
        # Upload file
        try:
            url = self.storage_service.upload_file(file_path, destination_path, metadata)
            logger.info(f"Uploaded file {filename} to {destination_path}")
            return url
        except Exception as e:
            logger.error(f"Failed to upload file {filename}: {str(e)}")
            raise
            
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate MD5 hash of a file."""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()