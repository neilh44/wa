from typing import Dict, Any, List, Optional, BinaryIO

from app.utils.logger import get_logger

logger = get_logger()

class SupabaseStorageService:
    """Implementation of storage service interface using Supabase Storage."""
    
    def __init__(self, supabase_client):
        """
        Initialize the Supabase storage service.
        
        Args:
            supabase_client: The Supabase client instance
        """
        self.supabase = supabase_client
    
    def upload(self, 
              bucket: str, 
              destination_path: str, 
              file_content: BinaryIO, 
              content_type: Optional[str] = None, 
              metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Upload a file to Supabase storage.
        
        Args:
            bucket: Storage bucket name
            destination_path: Path within the bucket
            file_content: File content as bytes or file-like object
            content_type: Optional MIME type
            metadata: Optional metadata dictionary
            
        Returns:
            Dictionary with upload result
        """
        # Prepare file options
        file_options = {}
        if content_type:
            file_options["content-type"] = content_type
        
        # Check if file exists before uploading
        try:
            # Try to get file metadata - if it succeeds, file exists
            self.supabase.storage.from_(bucket).get_public_url(destination_path)
            logger.info(f"File already exists at {destination_path}, skipping upload")
            return {"path": destination_path, "status": "exists"}
        except Exception:
            # File doesn't exist, proceed with upload
            pass
        
        # Upload to storage
        try:
            result = self.supabase.storage.from_(bucket).upload(
                destination_path, 
                file_content,
                file_options=file_options
            )
            return result
        except Exception as e:
            # Handle duplicate error specifically
            if hasattr(e, 'json') and isinstance(e.json(), dict):
                error_data = e.json()
                if error_data.get('error') == 'Duplicate':
                    logger.warning(f"File already exists at {destination_path}")
                    return {"path": destination_path, "status": "exists"}
            
            # Re-raise other errors
            logger.error(f"Error uploading file to {destination_path}: {str(e)}")
            raise
    
    def query_files(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Query files based on metadata.
        
        Args:
            query_params: Dictionary with query parameters
            
        Returns:
            List of matching file metadata
        """
        try:
            # Check if we're querying by file hash
            if "metadata" in query_params and "file_hash" in query_params["metadata"]:
                file_hash = query_params["metadata"]["file_hash"]
                
                # Query the database table that tracks your files
                result = self.supabase.table("files").select("*").eq("file_hash", file_hash).execute()
                
                return result.data
            return []
        except Exception as e:
            logger.error(f"Error querying files: {str(e)}")
            return []
    
    # Rest of the methods remain the same
    def delete(self, bucket: str, path: str) -> Dict[str, Any]:
        """Delete a file from Supabase storage."""
        return self.supabase.storage.from_(bucket).remove([path])
    
    def get_url(self, bucket: str, path: str) -> str:
        """Get public URL for a file in Supabase storage."""
        return self.supabase.storage.from_(bucket).get_public_url(path)
    
    def list_files(self, bucket: str, prefix: str = "") -> List[Dict[str, Any]]:
        """List files in a Supabase storage bucket with optional prefix."""
        return self.supabase.storage.from_(bucket).list(prefix)
    
    def create_signed_url(self, bucket: str, path: str, expires_in: int = 60) -> Dict[str, Any]:
        """Create a signed URL for private file access."""
        return self.supabase.storage.from_(bucket).create_signed_url(path, expires_in)