from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from app.utils.logger import get_logger

logger = get_logger()

class DatabaseManager:
    """Manages database operations for WhatsApp files and sessions."""
    
    def __init__(self, supabase_client, user_id: UUID):
        self.supabase = supabase_client
        self.user_id = user_id
    
    def get_existing_files(self) -> List[Dict[str, Any]]:
        """Get existing files from database in a single query."""
        try:
            result = self.supabase.table("files") \
                .select("id, storage_path, file_hash, uploaded") \
                .eq("user_id", str(self.user_id)) \
                .execute()
            
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error retrieving existing files: {str(e)}")
            return []
        
    def add_files_to_database(self, files: List[Dict[str, Any]]) -> None:
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
                # Remove the file_hash field if it's causing issues
                "uploaded": False
            }
            records.append(record)
        
        # Insert in batches of 50 (to avoid large payloads)
        batch_size = 50
        for i in range(0, len(records), batch_size):
            batch = records[i:i+batch_size]
            try:
                result = self.supabase.table("files").insert(batch).execute()
                logger.info(f"Added batch of {len(batch)} files to database")
            except Exception as e:
                logger.error(f"Error adding batch to database: {str(e)}")
                # Log the detailed structure of the record to diagnose issues
                if batch:
                    logger.error(f"Record structure: {list(batch[0].keys())}")
        
        
    
    def get_files(self, filter_criteria: Dict[str, Any] = None, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
        """
        Get WhatsApp files with optional filtering.
        
        Args:
            filter_criteria: Optional dictionary with filter criteria (e.g., uploaded, media_type)
            limit: Maximum number of files to return (pagination)
            offset: Offset for pagination
            
        Returns:
            Dictionary with files and count
        """
        try:
            # Count total files matching criteria
            count_query = self.supabase.table("files").select("id", count="exact").eq("user_id", str(self.user_id))
            
            # Build data query with pagination
            data_query = self.supabase.table("files").select("*").eq("user_id", str(self.user_id))
            
            # Apply filters if provided
            if filter_criteria:
                for key, value in filter_criteria.items():
                    count_query = count_query.eq(key, value)
                    data_query = data_query.eq(key, value)
            
            # Get count
            count_result = count_query.execute()
            total_count = count_result.count if hasattr(count_result, 'count') else 0
            
            # Apply pagination and order
            data_query = data_query.order("created_at", desc=True).range(offset, offset + limit - 1)
            
            # Execute query
            result = data_query.execute()
            files = result.data if result.data else []
            
            return {
                "files": files,
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": (offset + limit) < total_count
            }
        except Exception as e:
            logger.error(f"Error retrieving files: {str(e)}")
            return {
                "files": [],
                "total": 0,
                "limit": limit,
                "offset": offset,
                "has_more": False,
                "error": str(e)
            }
    
    def get_file_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the user's WhatsApp files.
        
        Returns:
            Dictionary with various file statistics
        """
        try:
            # Get total file count and size
            count_query = self.supabase.table("files").select("id", count="exact").eq("user_id", str(self.user_id)).execute()
            total_count = count_query.count if hasattr(count_query, 'count') else 0
            
            # Get uploaded count
            uploaded_query = self.supabase.table("files").select("id", count="exact").eq("user_id", str(self.user_id)).eq("uploaded", True).execute()
            uploaded_count = uploaded_query.count if hasattr(uploaded_query, 'count') else 0
            
            # Get total size
            size_query = self.supabase.table("files").select("size").eq("user_id", str(self.user_id)).execute()
            total_size = sum(file.get("size", 0) for file in size_query.data) if size_query.data else 0
            
            # Get counts by media type
            media_stats = {}
            for media_type in ["image", "document", "audio", "video", "other"]:
                type_query = self.supabase.table("files").select("id", count="exact").eq("user_id", str(self.user_id)).eq("media_type", media_type).execute()
                media_stats[media_type] = type_query.count if hasattr(type_query, 'count') else 0
            
            # Get counts by phone number
            phone_query = self.supabase.table("files").select("phone_number").eq("user_id", str(self.user_id)).execute()
            phone_stats = {}
            for file in phone_query.data:
                phone = file.get("phone_number", "unknown")
                if phone not in phone_stats:
                    phone_stats[phone] = 0
                phone_stats[phone] += 1
            
            return {
                "total_files": total_count,
                "uploaded_files": uploaded_count,
                "total_size_bytes": total_size,
                "total_size_mb": round(total_size / (1024 * 1024), 2),
                "media_types": media_stats,
                "phone_numbers": phone_stats,
                "percent_uploaded": round((uploaded_count / total_count) * 100, 2) if total_count > 0 else 0
            }
        except Exception as e:
            logger.error(f"Error getting file stats: {str(e)}")
            return {
                "error": str(e),
                "total_files": 0,
                "uploaded_files": 0,
                "total_size_bytes": 0,
                "total_size_mb": 0
            }
    def update_file(self, file_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update a file record in the database.
        
        Args:
            file_id: ID of the file to update
            update_data: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.supabase.table("files") \
                .update(update_data) \
                .eq("id", file_id) \
                .eq("user_id", str(self.user_id)) \
                .execute()
            
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error updating file {file_id}: {str(e)}")
            return False
        
    def delete_file(self, file_id: str) -> Dict[str, Any]:
        """
        Delete a file record from the database.
        
        Args:
            file_id: ID of the file to delete
            
        Returns:
            Result of the deletion operation
        """
        try:
            # First get the file info to check if it's uploaded
            file_query = self.supabase.table("files").select("*").eq("id", file_id).eq("user_id", str(self.user_id)).execute()
            
            if not file_query.data:
                return {"success": False, "message": "File not found"}
                
            file_info = file_query.data[0]
            
            # If file is uploaded, try to delete from storage too
            if file_info.get("uploaded") and file_info.get("storage_url"):
                try:
                    # Extract bucket path from URL
                    storage_path = file_info.get("storage_url").split("/")[-1]
                    
                    # Delete from storage
                    self.supabase.storage.from_("whatsapp_media").remove([storage_path])
                    logger.info(f"Deleted file from storage: {storage_path}")
                except Exception as e:
                    logger.warning(f"Error deleting file from storage: {str(e)}")
            
            # Delete from database
            result = self.supabase.table("files").delete().eq("id", file_id).eq("user_id", str(self.user_id)).execute()
            
            return {
                "success": True,
                "message": "File deleted successfully"
            }
        except Exception as e:
            logger.error(f"Error deleting file: {str(e)}")
            return {
                "success": False,
                "message": f"Error deleting file: {str(e)}"
            }