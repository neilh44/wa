import os
import time
from typing import Dict, Any, List
from app.utils.logger import get_logger

logger = get_logger()

class FileUploadService:
    """
    Service to handle file uploads and storage management
    """
    def __init__(self, supabase_client):
        """
        Initialize with Supabase client
        
        Args:
            supabase_client: Initialized Supabase client
        """
        self.supabase = supabase_client
        
    def sync_files_to_storage(self, files: List[Dict[str, Any]], user_id: str) -> Dict[str, Any]:
        """
        Upload multiple files to storage and update database records
        
        Args:
            files: List of file records from database
            user_id: User ID for organization
            
        Returns:
            Statistics about the upload operation
        """
        stats = {
            "total": len(files),
            "successful": 0,
            "errors": 0,
            "skipped_duplicates": 0,
            "timeouts": 0
        }
        
        if not files:
            return stats
            
        logger.info(f"Syncing {len(files)} files to storage for user {user_id}")
        
        for idx, file in enumerate(files):
            # Log progress periodically
            if idx > 0 and idx % 10 == 0:
                logger.info(f"Processed {idx}/{len(files)} files")
                
            file_id = file.get("id")
            local_path = file.get("storage_path")
            file_hash = file.get("file_hash", "")
            
            # Skip if already uploaded
            if file.get("uploaded", False):
                stats["skipped_duplicates"] += 1
                continue
                
            # Check if file exists locally
            if not local_path or not os.path.exists(local_path):
                logger.warning(f"File not found at {local_path}")
                
                # Mark as error in database
                try:
                    self.supabase.table("files").update({
                        "upload_error": "File not found locally"
                    }).eq("id", file_id).execute()
                except Exception as e:
                    logger.error(f"Error updating file record: {str(e)}")
                
                stats["errors"] += 1
                continue
                
            # Check for duplicates by file hash
            if file_hash:
                try:
                    duplicate_query = self.supabase.table("files").select("id", "storage_url").eq("file_hash", file_hash).eq("uploaded", True).neq("id", file_id).execute()
                    if duplicate_query.data:
                        # Found a duplicate that's already uploaded
                        duplicate = duplicate_query.data[0]
                        
                        # Use the same storage URL
                        self.supabase.table("files").update({
                            "storage_url": duplicate.get("storage_url"),
                            "uploaded": True,
                            "upload_error": None,
                            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                        }).eq("id", file_id).execute()
                        
                        logger.info(f"Using existing storage URL for duplicate file {file_id}")
                        stats["skipped_duplicates"] += 1
                        continue
                except Exception as e:
                    logger.warning(f"Error checking for duplicates: {str(e)}")
            
            # Prepare for upload
            try:
                # Create destination path
                filename = os.path.basename(local_path)
                file_ext = os.path.splitext(filename)[1].lower()
                timestamp = time.strftime("%Y%m%d%H%M%S")
                destination_path = f"{user_id}/{timestamp}_{filename}"
                
                # Get file size
                file_size = os.path.getsize(local_path)
                
                # Set timeout based on file size (larger files need more time)
                # 10MB = ~30 seconds, scale accordingly
                timeout = max(30, int(file_size / (10 * 1024 * 1024) * 30))
                
                # Upload with timeout handling
                try:
                    # Upload file
                    with open(local_path, "rb") as f:
                        mime_type = file.get("mime_type", "application/octet-stream")
                        self.supabase.storage.from_("whatsapp_media").upload(
                            destination_path, 
                            f,
                            {"contentType": mime_type, "upsert": True}
                        )
                    
                    # Get public URL
                    storage_url = self.supabase.storage.from_("whatsapp_media").get_public_url(destination_path)
                    
                    # Update database record
                    self.supabase.table("files").update({
                        "storage_url": storage_url,
                        "storage_path": destination_path,
                        "uploaded": True,
                        "upload_error": None,
                        "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ")
                    }).eq("id", file_id).execute()
                    
                    logger.info(f"Successfully uploaded file {file_id} to {destination_path}")
                    stats["successful"] += 1
                    
                except TimeoutError:
                    logger.warning(f"Timeout uploading file {file_id}")
                    self.supabase.table("files").update({
                        "upload_error": "Upload timeout"
                    }).eq("id", file_id).execute()
                    stats["timeouts"] += 1
                    
            except Exception as e:
                logger.error(f"Error uploading file {file_id}: {str(e)}")
                
                # Update error in database
                try:
                    self.supabase.table("files").update({
                        "upload_error": str(e)[:255]  # Truncate long error messages
                    }).eq("id", file_id).execute()
                except Exception as inner_e:
                    logger.error(f"Error updating file record: {str(inner_e)}")
                    
                stats["errors"] += 1
        
        logger.info(f"File sync complete: {stats}")
        return stats
        
    def get_upload_status(self, user_id: str) -> Dict[str, Any]:
        """
        Get upload status statistics for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Upload status statistics
        """
        try:
            # Get total count
            total_query = self.supabase.table("files").select("id", count="exact").eq("user_id", user_id).execute()
            total_count = total_query.count if hasattr(total_query, 'count') else 0
            
            # Get uploaded count
            uploaded_query = self.supabase.table("files").select("id", count="exact").eq("user_id", user_id).eq("uploaded", True).execute()
            uploaded_count = uploaded_query.count if hasattr(uploaded_query, 'count') else 0
            
            # Get error count
            error_query = self.supabase.table("files").select("id", count="exact").eq("user_id", user_id).not_.is_("upload_error", "null").execute()
            error_count = error_query.count if hasattr(error_query, 'count') else 0
            
            return {
                "total": total_count,
                "uploaded": uploaded_count,
                "errors": error_count,
                "pending": total_count - uploaded_count - error_count,
                "progress_percentage": round((uploaded_count / total_count) * 100, 2) if total_count > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting upload status: {str(e)}")
            return {
                "total": 0,
                "uploaded": 0,
                "errors": 0,
                "pending": 0,
                "progress_percentage": 0,
                "error": str(e)
            }