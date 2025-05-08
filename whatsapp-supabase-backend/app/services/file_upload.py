from typing import List, Dict, Any
from uuid import UUID

from app.utils.logger import get_logger

logger = get_logger()

class FileUploadService:
    """Service for uploading WhatsApp files to storage."""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def upload_files(self, user_id: UUID, file_ids: List[str] = None) -> Dict[str, Any]:
        """
        Upload WhatsApp files to storage.
        
        Args:
            user_id: ID of the user who owns the files
            file_ids: Specific file IDs to upload, or None to upload all unuploaded files for this user
            
        Returns:
            Upload statistics
        """
        try:
            # Query files to upload
            query = self.supabase.table("files").select("*")
            
            if file_ids:
                # Upload specific files
                query = query.in_("id", file_ids)
            else:
                # Upload all unuploaded files for this user
                query = query.eq("user_id", str(user_id)).eq("uploaded", False)
            
            result = query.execute()
            files = result.data if result.data else []
            
            if not files:
                logger.info("No files to upload")
                return {
                    "status": "success", 
                    "message": "No files to upload",
                    "total": 0,
                    "uploaded": 0,
                    "skipped": 0,
                    "errors": 0
                }
            
            logger.info(f"Uploading {len(files)} files to storage")
            
            # Upload stats
            stats = {
                "successful": 0,
                "skipped_duplicates": 0,
                "errors": 0,
                "timeouts": 0
            }
            
            # Process each file
            for file in files:
                try:
                    # Skip already uploaded files
                    if file.get("uploaded", False):
                        stats["skipped_duplicates"] += 1
                        continue
                    
                    file_path = file.get("storage_path")
                    file_id = file.get("id")
                    
                    if not file_path:
                        logger.warning(f"Missing file path for file ID: {file_id}")
                        stats["errors"] += 1
                        continue
                    
                    # Read file content
                    try:
                        with open(file_path, "rb") as f:
                            file_content = f.read()
                    except Exception as e:
                        logger.error(f"Error reading file {file_path}: {str(e)}")
                        stats["errors"] += 1
                        continue
                    
                    # Generate storage path
                    filename = file.get("filename", "unknown")
                    phone_number = file.get("phone_number", "unknown")
                    media_type = file.get("media_type", "other")
                    
                    # Use structured path: user_id/phone_number/media_type/filename
                    storage_path = f"{user_id}/{phone_number}/{media_type}/{filename}"
                    
                    # Upload to storage
                    try:
                        result = self.supabase.storage.from_("whatsapp_media").upload(
                            storage_path, 
                            file_content,
                            file_options={"content-type": file.get("mime_type", "application/octet-stream")}
                        )
                        
                        # Get public URL
                        storage_url = self.supabase.storage.from_("whatsapp_media").get_public_url(storage_path)
                        
                        # Update database record
                        self.supabase.table("files").update({
                            "uploaded": True,
                            "storage_url": storage_url,
                            "storage_path": storage_path
                        }).eq("id", file_id).execute()
                        
                        stats["successful"] += 1
                        logger.debug(f"Successfully uploaded file: {filename}")
                    except Exception as e:
                        logger.error(f"Error uploading file {filename} to storage: {str(e)}")
                        stats["errors"] += 1
                        
                except Exception as e:
                    logger.error(f"Unexpected error processing file: {str(e)}")
                    stats["errors"] += 1
            
            return {
                "status": "success",
                "message": f"Processed {len(files)} files",
                "total": len(files),
                "uploaded": stats["successful"],
                "skipped": stats["skipped_duplicates"],
                "errors": stats["errors"] + stats["timeouts"]
            }
            
        except Exception as e:
            logger.error(f"Error uploading files: {str(e)}")
            return {
                "status": "error",
                "message": f"Error uploading files: {str(e)}",
                "total": 0,
                "uploaded": 0,
                "skipped": 0,
                "errors": 1
            }
    
    def sync_files_to_storage(self, files: List[Dict[str, Any]], user_id: str) -> Dict[str, int]:
        """
        Sync a list of files to storage.
        
        Args:
            files: List of file info dictionaries
            user_id: ID of the user who owns the files
            
        Returns:
            Dictionary with upload statistics
        """
        stats = {
            "successful": 0,
            "skipped_duplicates": 0,
            "errors": 0,
            "timeouts": 0
        }
        
        # Extract file IDs
        file_ids = [file.get("id") for file in files if file.get("id")]
        
        if file_ids:
            # Use the main upload function
            upload_result = self.upload_files(user_id, file_ids)
            
            # Map the stats
            stats["successful"] = upload_result.get("uploaded", 0)
            stats["skipped_duplicates"] = upload_result.get("skipped", 0)
            stats["errors"] = upload_result.get("errors", 0)
        
        return stats