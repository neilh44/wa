from typing import Dict, List, Any, Optional
from uuid import UUID
from app.utils.logger import get_logger
from app.models.file import File, FileCreate
from app.services.storage_service import StorageService
from app.config import settings
from supabase import create_client, Client
from datetime import datetime

logger = get_logger()
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

class FileService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id
        self.storage_service = StorageService(user_id)
    
    def get_user_files(self, phone_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all files for a user, optionally filtered by phone number."""
        return self.storage_service.get_files(phone_number)
    
    def sync_missing_files(self) -> Dict[str, Any]:
        """Synchronize missing files by uploading them to storage."""
        missing_files = self.storage_service.get_missing_files()
        
        if not missing_files:
            return {"message": "No missing files found", "files_synced": 0}
        
        files_synced = 0
        
        for file in missing_files:
            result = self.storage_service.upload_file(UUID(file["id"]))
            
            if result["success"]:
                files_synced += 1
        
        return {
            "message": f"Synced {files_synced} out of {len(missing_files)} files",
            "files_synced": files_synced,
            "total_missing": len(missing_files)
        }
    
    def create_file_record(self, file_data: FileCreate) -> File:
        """Create a new file record."""
        file_dict = file_data.dict()
        file_dict["user_id"] = str(self.user_id)
        file_dict["uploaded"] = False
        
        result = supabase.table("files").insert(file_dict).execute()
        
        if not result.data:
            logger.error("Failed to create file record")
            raise Exception("Failed to create file record")
        
        return File(**result.data[0])
