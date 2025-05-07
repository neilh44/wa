import os
from typing import Dict, List, Any, Optional
from uuid import UUID
from app.utils.logger import get_logger
from app.config import settings
from supabase import create_client, Client
from datetime import datetime

logger = get_logger()
supabase: Client = create_client(settings.supabase_url, settings.supabase_key)

class StorageService:
    def __init__(self, user_id: UUID):
        self.user_id = user_id

    def upload_file(self, file_id: UUID) -> Dict[str, Any]:
        """Upload a file to Supabase Storage."""
        # Create a service role client
        service_client = create_client(settings.supabase_url, settings.supabase_service_key)
        
        # Get file info from database
        file_query = supabase.table("files").select("*").eq("id", str(file_id)).execute()
        
        if not file_query.data:
            logger.error(f"File not found: {file_id}")
            return {"success": False, "error": "File not found"}
        
        file_data = file_query.data[0]
        local_path = file_data["storage_path"]
        
        if not os.path.exists(local_path):
            logger.error(f"Local file not found: {local_path}")
            return {"success": False, "error": "Local file not found"}
        
        try:
            # Organize by phone number in storage
            phone_number = file_data["phone_number"].replace("+", "").replace(" ", "")
            storage_path = f"{phone_number}/{file_data['filename']}"
            
            # Upload to Supabase Storage using service role client
            with open(local_path, "rb") as f:
                file_content = f.read()
                
            result = service_client.storage.from_("whatsapp-files").upload(
                storage_path,
                file_content,
                {"content-type": file_data.get("mime_type", "application/octet-stream")}
            )
            
            # Update file status in database
            supabase.table("files").update({
                "uploaded": True,
                "storage_path": storage_path,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(file_id)).execute()
            
            return {"success": True, "storage_path": storage_path}
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
            
            # Update upload attempts
            supabase.table("files").update({
                "upload_attempts": file_data.get("upload_attempts", 0) + 1,
                "updated_at": datetime.utcnow().isoformat()
            }).eq("id", str(file_id)).execute()
            
            return {"success": False, "error": str(e)}
     
     
        
    def get_files(self, phone_number: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get files from Supabase Storage, optionally filtered by phone number."""
        query = supabase.table("files").select("*").eq("user_id", str(self.user_id))
        
        if phone_number:
            query = query.eq("phone_number", phone_number)
        
        result = query.execute()
        return result.data if result.data else []
    
    def get_missing_files(self) -> List[Dict[str, Any]]:
        """Get files that have not been uploaded successfully."""
        result = supabase.table("files") \
            .select("*") \
            .eq("user_id", str(self.user_id)) \
            .eq("uploaded", False) \
            .execute()
        
        return result.data if result.data else []
